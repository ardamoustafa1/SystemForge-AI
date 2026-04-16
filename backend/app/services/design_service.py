import secrets
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Conversation, ConversationMember, Design, DesignInput, DesignOutput, DesignOutputVersion, User, DesignComment
from app.models import WorkspaceMember
from app.schemas.design import (
    CreateDesignCommentRequest,
    CostCalibrationResponse,
    CreateDesignRequest,
    DesignCommentOut,
    DesignDetailResponse,
    DesignReviewStatusResponse,
    DesignInputPayload,
    DesignOutputPayload,
    DesignShareStatusResponse,
    PaginatedDesignSummaryResponse,
    PublicDesignResponse,
    RegenerateDesignRequest,
    RegenerateDesignResponse,
    DesignSummary,
    UpdateDesignNotesResponse,
    UpdateDesignReviewRequest,
)
from app.services.export_service import build_markdown_export
from app.services.generation_service import generate_structured_design
from app.services.authorization_service import (
    ensure_design_read_access,
    ensure_design_share_access,
    ensure_design_write_access,
)
from app.services.job_center_service import track_job
from app.services.live_cost_service import get_cloud_pricing, get_workspace_usage
async def _enqueue_generation(design_id: int, scale_stance: str, output_language: str = "en") -> None:
    from app.core.redis import get_redis_client
    import json
    redis = get_redis_client()
    settings = get_settings()
    stream = f"{settings.outbox_stream_prefix}:generation"
    trace_id = str(uuid4())
    await redis.xadd(
        stream,
        {
            "type": "design.generate",
            "payload_json": json.dumps(
                {
                    "design_id": design_id,
                    "scale_stance": scale_stance,
                    "output_language": output_language,
                    "trace_id": trace_id,
                }
            ),
        },
        maxlen=settings.stream_maxlen_approx,
        approximate=True,
    )
    try:
        with SessionLocal() as db:
            design = db.get(Design, design_id)
            if design and design.owner_id:
                await redis.xadd(
                    f"{settings.outbox_stream_prefix}:realtime:{design.owner_id}",
                    {
                        "type": "design.progress",
                        "payload_json": json.dumps(
                            {
                                "design_id": design_id,
                                "status": "generating",
                                "phase": "queued",
                                "progress_pct": 5,
                                "trace_id": trace_id,
                            }
                        ),
                    },
                    maxlen=settings.stream_maxlen_approx,
                    approximate=True,
                )
    except Exception:
        pass


def _ensure_design_discussion_conversation(db: Session, design: Design) -> None:
    """Create a 1:1 realtime conversation for this design and add the owner as member."""
    if design.discussion_conversation_id is not None:
        return
    conv = Conversation(
        kind="design",
        title=design.title[:160] if design.title else None,
        created_by_user_id=design.owner_id,
    )
    db.add(conv)
    db.flush()
    db.add(
        ConversationMember(
            conversation_id=int(conv.id),
            user_id=design.owner_id,
            role="member",
        )
    )
    design.discussion_conversation_id = int(conv.id)


def _get_workspace_design(db: Session, design_id: int, workspace_member: WorkspaceMember) -> Design:
    ensure_design_read_access(workspace_member)
    design = db.scalar(
        select(Design).where(
            Design.id == design_id,
            Design.workspace_id == workspace_member.workspace_id,
        )
    )
    if not design:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Design not found")
    return design


def _share_url_for_design(design: Design) -> str | None:
    if not design.share_token:
        return None
    base = get_settings().public_app_url.rstrip("/")
    return f"{base}/share/{design.share_token}"


def _build_detail_response(design: Design, design_input: DesignInput, design_output: DesignOutput | None) -> DesignDetailResponse:
    output_payload = None
    if design_output and design_output.payload:
        output_payload = DesignOutputPayload.model_validate(design_output.payload)

    return DesignDetailResponse(
        id=design.id,
        title=design.title,
        project_type=design.project_type,
        status=design.status,
        created_at=design.created_at,
        updated_at=design.updated_at,
        notes=design.notes,
        discussion_conversation_id=design.discussion_conversation_id,
        input=DesignInputPayload.model_validate(design_input.payload),
        output=output_payload,
        share_enabled=design.share_token is not None,
        share_url=_share_url_for_design(design),
    )


async def create_design_for_user(
    db: Session,
    user: User,
    workspace_member: WorkspaceMember,
    request: CreateDesignRequest,
) -> DesignDetailResponse:
    design = Design(
        owner_id=user.id,
        workspace_id=workspace_member.workspace_id,
        title=request.input.project_title.strip(),
        project_type=request.input.project_type.strip(),
        status="generating",
    )
    db.add(design)
    db.flush()

    new_input = DesignInput(design_id=design.id, payload=request.input.model_dump())
    db.add(new_input)
    db.flush()
    
    _ensure_design_discussion_conversation(db, design)
    db.commit()
    db.refresh(design)

    settings = get_settings()
    if settings.app_env.lower() in {"test", "testing"}:
        output_payload, generation_ms, model_name = await generate_structured_design(
            request.input, scale_stance=request.scale_stance, output_language=request.output_language
        )
        markdown_export = build_markdown_export(request.input.project_title, request.input, output_payload)
        output = DesignOutput(
            design_id=design.id,
            payload=output_payload.model_dump(),
            markdown_export=markdown_export,
            model_name=model_name,
            generation_ms=generation_ms,
        )
        db.add(output)
        db.add(
            DesignOutputVersion(
                design_id=design.id,
                payload=output_payload.model_dump(),
                markdown_export=markdown_export,
                model_name=model_name,
                generation_ms=generation_ms,
                scale_stance=request.scale_stance,
            )
        )
        design.status = "completed"
        db.commit()
        db.refresh(design)
        db.refresh(new_input)
        db.refresh(output)
        return _build_detail_response(design, new_input, output)
    await _enqueue_generation(design.id, request.scale_stance, request.output_language)
    await track_job(
        workspace_id=workspace_member.workspace_id,
        user_id=user.id,
        payload={"job_type": "generation", "design_id": design.id, "status": "queued", "title": design.title},
    )

    return _build_detail_response(design, new_input, None)


def list_designs_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    query: str | None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedDesignSummaryResponse:
    offset = (page - 1) * page_size
    stmt = select(Design).where(Design.workspace_id == workspace_member.workspace_id)
    if query:
        stmt = stmt.where(Design.title.ilike(f"%{query.strip()}%"))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(total_stmt) or 0

    designs = db.scalars(stmt.order_by(desc(Design.created_at)).offset(offset).limit(page_size)).all()
    items = [
        DesignSummary(
            id=item.id,
            title=item.title,
            project_type=item.project_type,
            status=item.status,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in designs
    ]
    return PaginatedDesignSummaryResponse(items=items, total=total, page=page, page_size=page_size)


def get_design_detail_for_user(db: Session, workspace_member: WorkspaceMember, design_id: int) -> DesignDetailResponse:
    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
    return _build_detail_response(design, design_input, design_output)


def delete_design_for_user(db: Session, workspace_member: WorkspaceMember, design_id: int) -> None:
    design = _get_workspace_design(db, design_id, workspace_member)
    cid = design.discussion_conversation_id
    if cid is not None:
        conv = db.get(Conversation, cid)
        if conv is not None:
            db.delete(conv)
    db.delete(design)
    db.commit()


def get_design_artifact_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
) -> tuple[Design, DesignInput, DesignOutput | None]:
    design = _get_workspace_design(db, design_id, workspace_member)
    if design.discussion_conversation_id is None:
        _ensure_design_discussion_conversation(db, design)
        db.commit()
        db.refresh(design)
    design_input = db.scalar(select(DesignInput).where(DesignInput.design_id == design.id))
    design_output = db.scalar(select(DesignOutput).where(DesignOutput.design_id == design.id))
    if not design_input:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Design artifact is incomplete",
        )
    return design, design_input, design_output


def _should_append_regeneration_snapshot(db: Session, design_id: int, existing_output: DesignOutput) -> bool:
    """Avoid duplicating the same snapshot as the latest archived version (e.g. first regen right after create)."""
    latest = db.scalar(
        select(DesignOutputVersion)
        .where(DesignOutputVersion.design_id == design_id)
        .order_by(desc(DesignOutputVersion.created_at), desc(DesignOutputVersion.id))
        .limit(1)
    )
    if latest is None:
        return True
    return latest.markdown_export != existing_output.markdown_export


async def regenerate_design_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
    body: RegenerateDesignRequest | None = None,
) -> RegenerateDesignResponse:
    scale_stance = body.scale_stance if body else "balanced"
    output_language = body.output_language if body else "en"
    ensure_design_write_access(workspace_member)
    design, _, _ = get_design_artifact_for_user(db=db, workspace_member=workspace_member, design_id=design_id)
    
    design.status = "generating"
    design.updated_at = datetime.now(timezone.utc)
    db.commit()

    settings = get_settings()
    if settings.app_env.lower() in {"test", "testing"}:
        input_row = db.scalar(select(DesignInput).where(DesignInput.design_id == design.id))
        if not input_row:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Design input missing")
        parsed_input = DesignInputPayload.model_validate(input_row.payload)
        output_payload, generation_ms, model_name = await generate_structured_design(
            parsed_input, scale_stance=scale_stance, output_language=output_language
        )
        markdown_export = build_markdown_export(parsed_input.project_title, parsed_input, output_payload)
        existing_output = db.scalar(select(DesignOutput).where(DesignOutput.design_id == design.id))
        if existing_output:
            db.add(
                DesignOutputVersion(
                    design_id=design.id,
                    payload=dict(existing_output.payload),
                    markdown_export=existing_output.markdown_export,
                    model_name=existing_output.model_name,
                    generation_ms=existing_output.generation_ms,
                    scale_stance=scale_stance,
                )
            )
            existing_output.payload = output_payload.model_dump()
            existing_output.markdown_export = markdown_export
            existing_output.model_name = model_name
            existing_output.generation_ms = generation_ms
        else:
            db.add(
                DesignOutput(
                    design_id=design.id,
                    payload=output_payload.model_dump(),
                    markdown_export=markdown_export,
                    model_name=model_name,
                    generation_ms=generation_ms,
                )
            )
        design.status = "completed"
        design.updated_at = datetime.now(timezone.utc)
        db.commit()
        return RegenerateDesignResponse(
            design_id=design.id,
            status="completed",
            message="Design regenerated synchronously for tests.",
        )
    await _enqueue_generation(design.id, scale_stance, output_language)
    await track_job(
        workspace_id=workspace_member.workspace_id,
        user_id=workspace_member.user_id,
        payload={"job_type": "generation", "design_id": design.id, "status": "queued", "title": design.title},
    )

    return RegenerateDesignResponse(
        design_id=design.id,
        status="generating",
        message="Design regeneration queued asynchronously.",
    )


def update_design_notes_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
    notes: str,
) -> UpdateDesignNotesResponse:
    ensure_design_write_access(workspace_member)
    design = _get_workspace_design(db=db, design_id=design_id, workspace_member=workspace_member)
    design.notes = notes.strip()
    db.commit()
    db.refresh(design)
    return UpdateDesignNotesResponse(
        design_id=design.id,
        notes=design.notes,
        updated_at=design.updated_at,
    )


def update_design_architecture_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
    mermaid: str,
) -> DesignDetailResponse:
    ensure_design_write_access(workspace_member)
    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
    if design_output is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Design output not ready")

    payload = dict(design_output.payload or {})
    payload["suggested_mermaid_diagram"] = mermaid.strip()
    parsed_output = DesignOutputPayload.model_validate(payload)
    design_output.payload = parsed_output.model_dump()
    design_output.markdown_export = build_markdown_export(design.title, DesignInputPayload.model_validate(design_input.payload), parsed_output)
    design.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(design)
    db.refresh(design_output)
    return _build_detail_response(design, design_input, design_output)


def enable_design_share_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
) -> DesignShareStatusResponse:
    ensure_design_share_access(workspace_member)
    design = _get_workspace_design(db, design_id, workspace_member)
    if not design.share_token:
        design.share_token = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(design)
    return DesignShareStatusResponse(enabled=True, share_url=_share_url_for_design(design))


def disable_design_share_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
) -> DesignShareStatusResponse:
    ensure_design_share_access(workspace_member)
    design = _get_workspace_design(db, design_id, workspace_member)
    design.share_token = None
    db.commit()
    db.refresh(design)
    return DesignShareStatusResponse(enabled=False, share_url=None)


def get_design_share_status_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
) -> DesignShareStatusResponse:
    design = _get_workspace_design(db, design_id, workspace_member)
    return DesignShareStatusResponse(enabled=design.share_token is not None, share_url=_share_url_for_design(design))


def get_public_design_by_token(db: Session, token: str) -> PublicDesignResponse:
    design = db.scalar(select(Design).where(Design.share_token == token))
    if not design:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    design_input = db.scalar(select(DesignInput).where(DesignInput.design_id == design.id))
    design_output = db.scalar(select(DesignOutput).where(DesignOutput.design_id == design.id))
    if not design_input or not design_output:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Design artifact is incomplete")
    return PublicDesignResponse(
        id=design.id,
        title=design.title,
        project_type=design.project_type,
        status=design.status,
        created_at=design.created_at,
        updated_at=design.updated_at,
        input=DesignInputPayload.model_validate(design_input.payload),
        output=DesignOutputPayload.model_validate(design_output.payload),
    )


def get_design_review_for_user(db: Session, workspace_member: WorkspaceMember, design_id: int) -> DesignReviewStatusResponse:
    design = _get_workspace_design(db, design_id, workspace_member)
    return DesignReviewStatusResponse(
        design_id=design.id,
        review_status=design.review_status,  # type: ignore[arg-type]
        review_owner_user_id=design.review_owner_user_id,
        reviewed_at=design.reviewed_at,
        review_decision_note=design.review_decision_note or "",
    )


def update_design_review_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
    payload: UpdateDesignReviewRequest,
) -> DesignReviewStatusResponse:
    ensure_design_write_access(workspace_member)
    design = _get_workspace_design(db, design_id, workspace_member)
    if payload.review_owner_user_id is not None:
        member = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_member.workspace_id,
                WorkspaceMember.user_id == payload.review_owner_user_id,
            )
            .first()
        )
        if not member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review owner must be a member of this workspace")
    if payload.review_status == "approved" and payload.review_owner_user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approved status requires a review owner")
    design.review_status = payload.review_status
    design.review_owner_user_id = payload.review_owner_user_id
    design.review_decision_note = payload.review_decision_note.strip()
    design.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(design)
    return get_design_review_for_user(db, workspace_member, design_id)


def list_design_comments_for_user(db: Session, workspace_member: WorkspaceMember, design_id: int) -> list[DesignCommentOut]:
    _get_workspace_design(db, design_id, workspace_member)
    rows = db.query(DesignComment).filter(DesignComment.design_id == design_id).order_by(DesignComment.created_at.asc()).all()
    return [
        DesignCommentOut(
            id=row.id,
            design_id=row.design_id,
            user_id=row.user_id,
            author_name=(row.user.full_name if row.user else None),
            content=row.content,
            created_at=row.created_at,
        )
        for row in rows
    ]


def add_design_comment_for_user(
    db: Session,
    workspace_member: WorkspaceMember,
    actor: User,
    design_id: int,
    payload: CreateDesignCommentRequest,
) -> DesignCommentOut:
    ensure_design_write_access(workspace_member)
    _get_workspace_design(db, design_id, workspace_member)
    comment = DesignComment(
        design_id=design_id,
        user_id=actor.id,
        content=payload.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return DesignCommentOut(
        id=comment.id,
        design_id=comment.design_id,
        user_id=comment.user_id,
        author_name=actor.full_name,
        content=comment.content,
        created_at=comment.created_at,
    )


def get_design_decision_timeline(db: Session, workspace_member: WorkspaceMember, design_id: int) -> list[dict]:
    design = _get_workspace_design(db, design_id, workspace_member)
    timeline: list[dict] = [
        {"type": "design_created", "at": design.created_at, "actor_user_id": design.owner_id, "summary": "Design created"},
    ]
    if design.reviewed_at:
        timeline.append(
            {
                "type": "review_status",
                "at": design.reviewed_at,
                "actor_user_id": design.review_owner_user_id,
                "summary": f"Review marked as {design.review_status}",
                "note": design.review_decision_note or "",
            }
        )
    comments = (
        db.query(DesignComment)
        .filter(DesignComment.design_id == design_id)
        .order_by(DesignComment.created_at.asc())
        .all()
    )
    for c in comments:
        timeline.append(
            {
                "type": "comment",
                "at": c.created_at,
                "actor_user_id": c.user_id,
                "summary": c.content[:160],
            }
        )
    versions = (
        db.query(DesignOutputVersion)
        .filter(DesignOutputVersion.design_id == design_id)
        .order_by(DesignOutputVersion.created_at.asc())
        .all()
    )
    for v in versions:
        timeline.append(
            {
                "type": "regeneration_snapshot",
                "at": v.created_at,
                "actor_user_id": None,
                "summary": f"Snapshot with stance={v.scale_stance}, model={v.model_name}",
            }
        )
    timeline.sort(key=lambda row: str(row.get("at")))
    return timeline


def get_workspace_ops_summary(db: Session, workspace_member: WorkspaceMember) -> dict[str, int]:
    workspace_id = workspace_member.workspace_id
    total_designs = db.query(func.count(Design.id)).filter(Design.workspace_id == workspace_id).scalar() or 0
    generating_count = db.query(func.count(Design.id)).filter(Design.workspace_id == workspace_id, Design.status == "generating").scalar() or 0
    approved_count = db.query(func.count(Design.id)).filter(Design.workspace_id == workspace_id, Design.review_status == "approved").scalar() or 0
    review_pending_count = db.query(func.count(Design.id)).filter(
        Design.workspace_id == workspace_id,
        Design.review_status.in_(["draft", "in_review", "changes_requested"]),
    ).scalar() or 0
    avg_generation_ms = int(
        db.query(func.avg(DesignOutput.generation_ms)).join(Design, Design.id == DesignOutput.design_id).filter(Design.workspace_id == workspace_id).scalar()
        or 0
    )
    outputs = (
        db.query(DesignOutput)
        .join(Design, Design.id == DesignOutput.design_id)
        .filter(Design.workspace_id == workspace_id)
        .all()
    )
    min_total = 0
    max_total = 0
    risk_drift_count = 0
    for out in outputs:
        payload = out.payload or {}
        estimated = payload.get("estimated_cloud_cost") or {}
        min_total += int(estimated.get("monthly_usd_min", 0) or 0)
        max_total += int(estimated.get("monthly_usd_max", 0) or 0)
        warnings = payload.get("consistency_warnings") or []
        if isinstance(warnings, list) and len(warnings) > 0:
            risk_drift_count += 1
    return {
        "total_designs": int(total_designs),
        "generating_count": int(generating_count),
        "approved_count": int(approved_count),
        "review_pending_count": int(review_pending_count),
        "avg_generation_ms": avg_generation_ms,
        "monthly_cost_min_total": int(min_total),
        "monthly_cost_max_total": int(max_total),
        "risk_drift_count": int(risk_drift_count),
    }


async def get_cost_calibration_for_user(db: Session, workspace_member: WorkspaceMember, design_id: int) -> CostCalibrationResponse:
    design = _get_workspace_design(db, design_id, workspace_member)
    if not design.output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Design output not found")
    estimated = (design.output.payload or {}).get("estimated_cloud_cost") or {}
    est_min = int(estimated.get("monthly_usd_min", 0) or 0)
    est_max = int(estimated.get("monthly_usd_max", 0) or 0)
    pricing = await get_cloud_pricing()
    usage = await get_workspace_usage(workspace_member.workspace_id)
    factor = float(pricing.get("compute_index", 1.0) + pricing.get("network_index", 1.0) + pricing.get("storage_index", 1.0)) / 3.0
    confidence: str = "low"
    traffic = (design.input.payload or {}).get("traffic_assumptions", "") if design.input else ""
    if isinstance(traffic, str) and traffic.strip():
        factor += 0.08
        confidence = "medium"
    if design.input and (design.input.payload or {}).get("document_context"):
        factor += 0.07
        confidence = "high"
    if usage and int(usage.get("monthly_actual_usd", 0) or 0) > 0 and est_max > 0:
        actual = int(usage.get("monthly_actual_usd", 0) or 0)
        usage_factor = max(0.5, min(2.0, actual / est_max))
        factor = (factor + usage_factor) / 2.0
        confidence = "high"
    calibrated_min = int(est_min * max(0.5, factor))
    calibrated_max = int(est_max * max(0.5, factor))
    return CostCalibrationResponse(
        design_id=design.id,
        estimated_monthly_usd_min=est_min,
        estimated_monthly_usd_max=est_max,
        calibrated_monthly_usd_min=calibrated_min,
        calibrated_monthly_usd_max=calibrated_max,
        calibration_factor=round(factor, 2),
        confidence=confidence,  # type: ignore[arg-type]
    )


def get_design_artifact_by_share_token(
    db: Session,
    token: str,
) -> tuple[Design, DesignInput, DesignOutput]:
    design = db.scalar(select(Design).where(Design.share_token == token))
    if not design:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    design_input = db.scalar(select(DesignInput).where(DesignInput.design_id == design.id))
    design_output = db.scalar(select(DesignOutput).where(DesignOutput.design_id == design.id))
    if not design_input or not design_output:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Design artifact is incomplete")
    return design, design_input, design_output
