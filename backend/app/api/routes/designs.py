from fastapi import APIRouter, Body, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.auth.deps import enforce_csrf, get_active_workspace_member, get_current_user
from app.core.rate_limiter import enforce_rate_limit, enforce_usage_quota
from app.core.idempotency import enforce_idempotency
from app.db.session import get_db
from app.models import User, WorkspaceMember
from app.schemas.design import (
    CostCalibrationResponse,
    CreateDesignCommentRequest,
    CreateDesignRequest,
    DesignCommentOut,
    DesignDetailResponse,
    DesignReviewStatusResponse,
    DesignShareStatusResponse,
    PaginatedDesignSummaryResponse,
    RegenerateDesignRequest,
    RegenerateDesignResponse,
    UpdateDesignNotesRequest,
    UpdateDesignNotesResponse,
    UpdateDesignArchitectureRequest,
    UpdateDesignReviewRequest,
)
from app.services.design_service import (
    create_design_for_user,
    add_design_comment_for_user,
    delete_design_for_user,
    disable_design_share_for_user,
    enable_design_share_for_user,
    get_design_review_for_user,
    get_cost_calibration_for_user,
    get_design_decision_timeline,
    get_design_detail_for_user,
    get_design_share_status_for_user,
    list_designs_for_user,
    list_design_comments_for_user,
    regenerate_design_for_user,
    update_design_review_for_user,
    update_design_notes_for_user,
    update_design_architecture_for_user,
)

router = APIRouter(prefix="/designs", tags=["designs"])


@router.post("", response_model=DesignDetailResponse)
async def create_design(
    request: CreateDesignRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    client_ip = http_request.client.host if http_request.client else "unknown"
    await enforce_rate_limit(scope="design-create-user", identifier=str(user.id), limit=3, window_seconds=60)
    await enforce_rate_limit(scope="design-create-ip", identifier=client_ip, limit=5, window_seconds=60)
    await enforce_usage_quota(
        scope="llm-tokens",
        identifier=f"{workspace_member.workspace_id}:{user.id}",
        consume_units=1200,
        max_units=workspace_member.workspace.monthly_token_budget,
        window_seconds=30 * 24 * 60 * 60,
    )
    await enforce_idempotency(
        scope="design-create",
        owner_key=f"{workspace_member.workspace_id}:{user.id}",
        idempotency_key=idempotency_key,
        ttl_seconds=300,
    )
    return await create_design_for_user(db=db, user=user, workspace_member=workspace_member, request=request)


@router.get("", response_model=PaginatedDesignSummaryResponse)
def list_designs(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return list_designs_for_user(db=db, workspace_member=workspace_member, query=q, page=page, page_size=page_size)


@router.get("/{design_id}", response_model=DesignDetailResponse)
def get_design(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return get_design_detail_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.delete("/{design_id}")
def delete_design(
    design_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    delete_design_for_user(db=db, workspace_member=workspace_member, design_id=design_id)
    return {"ok": True}


@router.post("/{design_id}/regenerate", response_model=RegenerateDesignResponse, status_code=202)
async def regenerate_design(
    design_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    body: RegenerateDesignRequest | None = Body(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    client_ip = http_request.client.host if http_request.client else "unknown"
    await enforce_rate_limit(
        scope="design-regenerate-user",
        identifier=str(workspace_member.user_id),
        limit=4,
        window_seconds=60,
    )
    await enforce_rate_limit(scope="design-regenerate-ip", identifier=client_ip, limit=8, window_seconds=60)
    await enforce_usage_quota(
        scope="llm-tokens",
        identifier=f"{workspace_member.workspace_id}:{workspace_member.user_id}",
        consume_units=1000,
        max_units=workspace_member.workspace.monthly_token_budget,
        window_seconds=30 * 24 * 60 * 60,
    )
    await enforce_idempotency(
        scope="design-regenerate",
        owner_key=f"{workspace_member.workspace_id}:{design_id}:{workspace_member.user_id}",
        idempotency_key=idempotency_key,
        ttl_seconds=300,
    )
    return await regenerate_design_for_user(db=db, workspace_member=workspace_member, design_id=design_id, body=body)


@router.get("/{design_id}/share", response_model=DesignShareStatusResponse)
def get_share_status(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return get_design_share_status_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.post("/{design_id}/share", response_model=DesignShareStatusResponse)
def enable_share(
    design_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return enable_design_share_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.delete("/{design_id}/share", response_model=DesignShareStatusResponse)
def disable_share(
    design_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return disable_design_share_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.patch("/{design_id}/notes", response_model=UpdateDesignNotesResponse)
def update_notes(
    design_id: int,
    payload: UpdateDesignNotesRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return update_design_notes_for_user(
        db=db,
        workspace_member=workspace_member,
        design_id=design_id,
        notes=payload.notes,
    )


@router.patch("/{design_id}/architecture", response_model=DesignDetailResponse)
def update_architecture(
    design_id: int,
    payload: UpdateDesignArchitectureRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return update_design_architecture_for_user(
        db=db,
        workspace_member=workspace_member,
        design_id=design_id,
        mermaid=payload.mermaid,
    )


@router.get("/{design_id}/review", response_model=DesignReviewStatusResponse)
def get_review_status(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return get_design_review_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.patch("/{design_id}/review", response_model=DesignReviewStatusResponse)
async def update_review_status(
    design_id: int,
    payload: UpdateDesignReviewRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    await enforce_idempotency(
        scope="design-review-update",
        owner_key=f"{workspace_member.workspace_id}:{workspace_member.user_id}:{design_id}",
        idempotency_key=idempotency_key,
        ttl_seconds=180,
    )
    return update_design_review_for_user(db=db, workspace_member=workspace_member, design_id=design_id, payload=payload)


@router.get("/{design_id}/comments", response_model=list[DesignCommentOut])
def list_comments(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return list_design_comments_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.post("/{design_id}/comments", response_model=DesignCommentOut, status_code=201)
async def create_comment(
    design_id: int,
    payload: CreateDesignCommentRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    await enforce_idempotency(
        scope="design-comment-create",
        owner_key=f"{workspace_member.workspace_id}:{workspace_member.user_id}:{design_id}",
        idempotency_key=idempotency_key,
        ttl_seconds=120,
    )
    return add_design_comment_for_user(
        db=db,
        workspace_member=workspace_member,
        actor=user,
        design_id=design_id,
        payload=payload,
    )


@router.get("/{design_id}/cost-calibration", response_model=CostCalibrationResponse)
async def get_cost_calibration(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return await get_cost_calibration_for_user(db=db, workspace_member=workspace_member, design_id=design_id)


@router.get("/{design_id}/timeline")
def decision_timeline(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return {"items": get_design_decision_timeline(db=db, workspace_member=workspace_member, design_id=design_id)}
