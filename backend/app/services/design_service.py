import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Conversation, ConversationMember, Design, DesignInput, DesignOutput, DesignOutputVersion, User
from app.schemas.design import (
    CreateDesignRequest,
    DesignDetailResponse,
    DesignInputPayload,
    DesignOutputPayload,
    DesignShareStatusResponse,
    PaginatedDesignSummaryResponse,
    PublicDesignResponse,
    RegenerateDesignRequest,
    RegenerateDesignResponse,
    DesignSummary,
    UpdateDesignNotesResponse,
)
from app.services.export_service import build_markdown_export
from app.services.generation_service import generate_structured_design


async def _enqueue_generation(design_id: int, scale_stance: str) -> None:
    from app.core.redis import get_redis_client
    import json
    redis = get_redis_client()
    settings = get_settings()
    stream = f"{settings.outbox_stream_prefix}:generation"
    await redis.xadd(
        stream,
        {
            "type": "design.generate",
            "payload_json": json.dumps({"design_id": design_id, "scale_stance": scale_stance})
        },
        maxlen=settings.stream_maxlen_approx,
        approximate=True,
    )


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


def _get_owned_design(db: Session, design_id: int, owner_id: int) -> Design:
    design = db.scalar(select(Design).where(Design.id == design_id, Design.owner_id == owner_id))
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


async def create_design_for_user(db: Session, user: User, request: CreateDesignRequest) -> DesignDetailResponse:
    design = Design(
        owner_id=user.id,
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

    await _enqueue_generation(design.id, request.scale_stance)

    return _build_detail_response(design, new_input, None)


def list_designs_for_user(
    db: Session,
    user: User,
    query: str | None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedDesignSummaryResponse:
    offset = (page - 1) * page_size
    stmt = select(Design).where(Design.owner_id == user.id)
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


def get_design_detail_for_user(db: Session, user: User, design_id: int) -> DesignDetailResponse:
    design, design_input, design_output = get_design_artifact_for_user(db=db, user=user, design_id=design_id)
    return _build_detail_response(design, design_input, design_output)


def delete_design_for_user(db: Session, user: User, design_id: int) -> None:
    design = _get_owned_design(db, design_id, user.id)
    cid = design.discussion_conversation_id
    if cid is not None:
        conv = db.get(Conversation, cid)
        if conv is not None:
            db.delete(conv)
    db.delete(design)
    db.commit()


def get_design_artifact_for_user(db: Session, user: User, design_id: int) -> tuple[Design, DesignInput, DesignOutput | None]:
    design = _get_owned_design(db, design_id, user.id)
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
    user: User,
    design_id: int,
    body: RegenerateDesignRequest | None = None,
) -> RegenerateDesignResponse:
    scale_stance = body.scale_stance if body else "balanced"
    design, _, _ = get_design_artifact_for_user(db=db, user=user, design_id=design_id)
    
    design.status = "generating"
    design.updated_at = datetime.now(timezone.utc)
    db.commit()

    await _enqueue_generation(design.id, scale_stance)

    return RegenerateDesignResponse(
        design_id=design.id,
        status="generating",
        message="Design regeneration queued asynchronously.",
    )


def update_design_notes_for_user(db: Session, user: User, design_id: int, notes: str) -> UpdateDesignNotesResponse:
    design = _get_owned_design(db=db, design_id=design_id, owner_id=user.id)
    design.notes = notes.strip()
    db.commit()
    db.refresh(design)
    return UpdateDesignNotesResponse(
        design_id=design.id,
        notes=design.notes,
        updated_at=design.updated_at,
    )


def enable_design_share_for_user(db: Session, user: User, design_id: int) -> DesignShareStatusResponse:
    design = _get_owned_design(db, design_id, user.id)
    if not design.share_token:
        design.share_token = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(design)
    return DesignShareStatusResponse(enabled=True, share_url=_share_url_for_design(design))


def disable_design_share_for_user(db: Session, user: User, design_id: int) -> DesignShareStatusResponse:
    design = _get_owned_design(db, design_id, user.id)
    design.share_token = None
    db.commit()
    db.refresh(design)
    return DesignShareStatusResponse(enabled=False, share_url=None)


def get_design_share_status_for_user(db: Session, user: User, design_id: int) -> DesignShareStatusResponse:
    design = _get_owned_design(db, design_id, user.id)
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
