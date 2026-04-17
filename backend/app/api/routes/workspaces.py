"""Workspace API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status, Header
from sqlalchemy.orm import Session

from app.auth.deps import enforce_csrf, get_current_user
from app.core.rate_limiter import enforce_rate_limit
from app.core.idempotency import enforce_idempotency
from app.db.session import get_db
from app.models import RoleEnum, User
from app.schemas.workspace import (
    ActiveWorkspaceResponse,
    CreateWorkspaceRequest,
    InviteMemberRequest,
    UpdateWorkspaceBudgetRequest,
    UpdateMemberRoleRequest,
    UpdateWorkspaceRequest,
    WorkspaceBudgetResponse,
    WorkspaceMemberOut,
    WorkspaceSummary,
)
from app.services.workspace_service import (
    create_workspace,
    delete_workspace,
    get_workspace_details,
    invite_member,
    list_workspaces_for_user,
    remove_member,
    get_workspace_budget,
    set_default_workspace,
    update_member_role,
    update_workspace_budget,
    update_workspace,
)
from app.services.security_audit_service import log_security_audit
from app.core.async_bridge import run_async

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ─────────────────────── workspace CRUD ─────────────────────────────────────

@router.get("", response_model=list[WorkspaceSummary])
def list_workspaces(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list_workspaces_for_user(db=db, user=user)


@router.post("", response_model=ActiveWorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_route(
    payload: CreateWorkspaceRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    client_ip = http_request.client.host if http_request.client else "unknown"
    await enforce_rate_limit(scope="workspace-create", identifier=str(user.id), limit=10, window_seconds=3600)
    await enforce_idempotency(scope="workspace-create", owner_key=str(user.id), idempotency_key=idempotency_key, ttl_seconds=600)
    res = create_workspace(db=db, user=user, name=payload.name)
    await log_security_audit("workspace.create", actor_user_id=user.id, workspace_id=res["workspace"].id, metadata={"name": payload.name})
    return res


@router.get("/{workspace_id}", response_model=ActiveWorkspaceResponse)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_workspace_details(db=db, user=user, workspace_id=workspace_id)


@router.patch("/{workspace_id}")
async def update_workspace_route(
    workspace_id: int,
    payload: UpdateWorkspaceRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    await enforce_idempotency("workspace-update", f"{user.id}:{workspace_id}", idempotency_key, 300)
    res = update_workspace(db=db, user=user, workspace_id=workspace_id, name=payload.name)
    await log_security_audit("workspace.update", actor_user_id=user.id, workspace_id=workspace_id, metadata={"name": payload.name})
    return res


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace_route(
    workspace_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("workspace-delete", f"{user.id}:{workspace_id}", idempotency_key, 300))
    delete_workspace(db=db, user=user, workspace_id=workspace_id)
    run_async(log_security_audit("workspace.delete", actor_user_id=user.id, workspace_id=workspace_id, metadata={}))


@router.post("/{workspace_id}/default", status_code=status.HTTP_204_NO_CONTENT)
def set_default(
    workspace_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("workspace-set-default", f"{user.id}:{workspace_id}", idempotency_key, 180))
    set_default_workspace(db=db, user=user, workspace_id=workspace_id)


@router.get("/{workspace_id}/budget", response_model=WorkspaceBudgetResponse)
def get_budget(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_workspace_budget(db=db, user=user, workspace_id=workspace_id)


@router.patch("/{workspace_id}/budget", response_model=WorkspaceBudgetResponse)
async def update_budget(
    workspace_id: int,
    payload: UpdateWorkspaceBudgetRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    await enforce_idempotency("workspace-budget-update", f"{user.id}:{workspace_id}", idempotency_key, 300)
    res = update_workspace_budget(
        db=db,
        user=user,
        workspace_id=workspace_id,
        monthly_token_budget=payload.monthly_token_budget,
        budget_alert_threshold_pct=payload.budget_alert_threshold_pct,
    )
    await log_security_audit(
        "workspace.budget.update",
        actor_user_id=user.id,
        workspace_id=workspace_id,
        metadata={"monthly_token_budget": payload.monthly_token_budget, "budget_alert_threshold_pct": payload.budget_alert_threshold_pct},
    )
    return res


# ─────────────────────── members ─────────────────────────────────────────────

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberOut, status_code=status.HTTP_201_CREATED)
async def invite_member_route(
    workspace_id: int,
    payload: InviteMemberRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    await enforce_idempotency("workspace-invite-member", f"{user.id}:{workspace_id}", idempotency_key, 600)
    res = invite_member(db=db, actor=user, workspace_id=workspace_id, email=payload.email, role=RoleEnum(payload.role))
    await log_security_audit("workspace.member.invite", actor_user_id=user.id, workspace_id=workspace_id, metadata={"email": payload.email, "role": payload.role})
    return res


@router.patch("/{workspace_id}/members/{member_id}", response_model=WorkspaceMemberOut)
def update_role_route(
    workspace_id: int,
    member_id: int,
    payload: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("workspace-role-update", f"{user.id}:{workspace_id}:{member_id}", idempotency_key, 180))
    res = update_member_role(db=db, actor=user, workspace_id=workspace_id, member_id=member_id, role=RoleEnum(payload.role))
    run_async(log_security_audit("workspace.member.role_update", actor_user_id=user.id, workspace_id=workspace_id, metadata={"member_id": member_id, "role": payload.role}))
    return res


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_route(
    workspace_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_csrf),
    user: User = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("workspace-member-remove", f"{user.id}:{workspace_id}:{member_id}", idempotency_key, 180))
    remove_member(db=db, actor=user, workspace_id=workspace_id, member_id=member_id)
    run_async(log_security_audit("workspace.member.remove", actor_user_id=user.id, workspace_id=workspace_id, metadata={"member_id": member_id}))
