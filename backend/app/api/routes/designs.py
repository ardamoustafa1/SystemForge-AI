from fastapi import APIRouter, Body, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth.deps import enforce_csrf, get_current_user
from app.core.rate_limiter import enforce_rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.design import (
    CreateDesignRequest,
    DesignDetailResponse,
    DesignShareStatusResponse,
    PaginatedDesignSummaryResponse,
    RegenerateDesignRequest,
    RegenerateDesignResponse,
    UpdateDesignNotesRequest,
    UpdateDesignNotesResponse,
)
from app.services.design_service import (
    create_design_for_user,
    delete_design_for_user,
    disable_design_share_for_user,
    enable_design_share_for_user,
    get_design_detail_for_user,
    get_design_share_status_for_user,
    list_designs_for_user,
    regenerate_design_for_user,
    update_design_notes_for_user,
)

router = APIRouter(prefix="/designs", tags=["designs"])


@router.post("", response_model=DesignDetailResponse)
async def create_design(
    request: CreateDesignRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
):
    client_ip = http_request.client.host if http_request.client else "unknown"
    await enforce_rate_limit(scope="design-create-user", identifier=str(user.id), limit=20, window_seconds=60)
    await enforce_rate_limit(scope="design-create-ip", identifier=client_ip, limit=40, window_seconds=60)
    return await create_design_for_user(db=db, user=user, request=request)


@router.get("", response_model=PaginatedDesignSummaryResponse)
def list_designs(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list_designs_for_user(db=db, user=user, query=q, page=page, page_size=page_size)


@router.get("/{design_id}", response_model=DesignDetailResponse)
def get_design(design_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_design_detail_for_user(db=db, user=user, design_id=design_id)


@router.delete("/{design_id}")
def delete_design(
    design_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
):
    delete_design_for_user(db=db, user=user, design_id=design_id)
    return {"ok": True}


@router.post("/{design_id}/regenerate", response_model=RegenerateDesignResponse, status_code=202)
async def regenerate_design(
    design_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    body: RegenerateDesignRequest | None = Body(default=None),
):
    client_ip = http_request.client.host if http_request.client else "unknown"
    await enforce_rate_limit(scope="design-regenerate-user", identifier=str(user.id), limit=10, window_seconds=60)
    await enforce_rate_limit(scope="design-regenerate-ip", identifier=client_ip, limit=20, window_seconds=60)
    return await regenerate_design_for_user(db=db, user=user, design_id=design_id, body=body)


@router.get("/{design_id}/share", response_model=DesignShareStatusResponse)
def get_share_status(
    design_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_design_share_status_for_user(db=db, user=user, design_id=design_id)


@router.post("/{design_id}/share", response_model=DesignShareStatusResponse)
def enable_share(
    design_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
):
    return enable_design_share_for_user(db=db, user=user, design_id=design_id)


@router.delete("/{design_id}/share", response_model=DesignShareStatusResponse)
def disable_share(
    design_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
):
    return disable_design_share_for_user(db=db, user=user, design_id=design_id)


@router.patch("/{design_id}/notes", response_model=UpdateDesignNotesResponse)
def update_notes(
    design_id: int,
    payload: UpdateDesignNotesRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
):
    return update_design_notes_for_user(db=db, user=user, design_id=design_id, notes=payload.notes)
