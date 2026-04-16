"""Workspace CRUD service – all business logic lives here."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Workspace, WorkspaceMember, RoleEnum


# ───────────────────────────── helpers ─────────────────────────────────────

def _get_member_or_404(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember:
    member = db.scalar(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
    )
    if not member:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    return member


def _require_workspace_role(member: WorkspaceMember, *roles: RoleEnum) -> None:
    if member.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {[r.value for r in roles]}",
        )


# ───────────────────────────── queries ─────────────────────────────────────

def list_workspaces_for_user(db: Session, user: User) -> list[dict]:
    rows = db.execute(
        select(Workspace, WorkspaceMember)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
    ).all()
    return [
        {
            "id": ws.id,
            "name": ws.name,
            "role": mem.role.value,
            "created_at": ws.created_at,
        }
        for ws, mem in rows
    ]


def get_workspace_details(db: Session, user: User, workspace_id: int) -> dict:
    member = _get_member_or_404(db, workspace_id, user.id)
    ws = member.workspace
    members = db.scalars(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == ws.id)
    ).all()
    member_out = [
        {
            "id": m.id,
            "user_id": m.user_id,
            "email": m.user.email,
            "full_name": m.user.full_name,
            "role": m.role.value,
            "joined_at": m.created_at,
        }
        for m in members
    ]
    return {"workspace": ws, "role": member.role.value, "members": member_out}


# ───────────────────────────── mutations ───────────────────────────────────

def create_workspace(db: Session, user: User, name: str) -> dict:
    ws = Workspace(name=name.strip())
    db.add(ws)
    db.flush()  # get ws.id

    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=RoleEnum.admin))

    # Set as default if user has none
    if user.default_workspace_id is None:
        user.default_workspace_id = ws.id

    db.commit()
    db.refresh(ws)
    return {"workspace": ws, "role": "admin", "members": []}


def update_workspace(db: Session, user: User, workspace_id: int, name: str) -> Workspace:
    member = _get_member_or_404(db, workspace_id, user.id)
    _require_workspace_role(member, RoleEnum.admin)
    ws = member.workspace
    ws.name = name.strip()
    db.commit()
    db.refresh(ws)
    return ws


def delete_workspace(db: Session, user: User, workspace_id: int) -> None:
    member = _get_member_or_404(db, workspace_id, user.id)
    _require_workspace_role(member, RoleEnum.admin)
    ws = member.workspace

    # Reassign default_workspace_id for all members who had this as default
    for m in ws.members:
        if m.user.default_workspace_id == workspace_id:
            m.user.default_workspace_id = None

    db.delete(ws)
    db.commit()


def invite_member(db: Session, actor: User, workspace_id: int, email: str, role: RoleEnum) -> dict:
    actor_member = _get_member_or_404(db, workspace_id, actor.id)
    _require_workspace_role(actor_member, RoleEnum.admin, RoleEnum.editor)
    parsed_role = role

    if parsed_role == RoleEnum.admin:
        _require_workspace_role(actor_member, RoleEnum.admin)

    target_user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if not target_user:
        raise HTTPException(status_code=404, detail="No user found with that email")

    existing = db.scalar(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user.id)
    )
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member of this workspace")

    new_member = WorkspaceMember(workspace_id=workspace_id, user_id=target_user.id, role=parsed_role)
    db.add(new_member)

    # Set as default if user has no default
    if target_user.default_workspace_id is None:
        target_user.default_workspace_id = workspace_id

    db.commit()
    db.refresh(new_member)
    return {
        "id": new_member.id,
        "user_id": target_user.id,
        "email": target_user.email,
        "full_name": target_user.full_name,
        "role": new_member.role.value,
        "joined_at": new_member.created_at,
    }


def update_member_role(db: Session, actor: User, workspace_id: int, member_id: int, role: RoleEnum) -> dict:
    actor_member = _get_member_or_404(db, workspace_id, actor.id)
    _require_workspace_role(actor_member, RoleEnum.admin)
    parsed_role = role

    target = db.scalar(
        select(WorkspaceMember)
        .where(WorkspaceMember.id == member_id, WorkspaceMember.workspace_id == workspace_id)
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if target.user_id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    target.role = parsed_role
    db.commit()
    return {
        "id": target.id,
        "user_id": target.user_id,
        "email": target.user.email,
        "full_name": target.user.full_name,
        "role": target.role.value,
        "joined_at": target.created_at,
    }


def remove_member(db: Session, actor: User, workspace_id: int, member_id: int) -> None:
    actor_member = _get_member_or_404(db, workspace_id, actor.id)
    _require_workspace_role(actor_member, RoleEnum.admin)

    target = db.scalar(
        select(WorkspaceMember)
        .where(WorkspaceMember.id == member_id, WorkspaceMember.workspace_id == workspace_id)
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    if target.user_id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself from workspace")

    db.delete(target)
    db.commit()


def set_default_workspace(db: Session, user: User, workspace_id: int) -> None:
    """Verify user is a member and set as their default workspace."""
    _get_member_or_404(db, workspace_id, user.id)
    user.default_workspace_id = workspace_id
    db.commit()


def get_workspace_budget(db: Session, user: User, workspace_id: int) -> dict:
    member = _get_member_or_404(db, workspace_id, user.id)
    return {
        "workspace_id": workspace_id,
        "monthly_token_budget": member.workspace.monthly_token_budget,
        "budget_alert_threshold_pct": member.workspace.budget_alert_threshold_pct,
    }


def update_workspace_budget(
    db: Session,
    user: User,
    workspace_id: int,
    monthly_token_budget: int,
    budget_alert_threshold_pct: int,
) -> dict:
    member = _get_member_or_404(db, workspace_id, user.id)
    _require_workspace_role(member, RoleEnum.admin)
    member.workspace.monthly_token_budget = monthly_token_budget
    member.workspace.budget_alert_threshold_pct = budget_alert_threshold_pct
    db.commit()
    return {
        "workspace_id": workspace_id,
        "monthly_token_budget": member.workspace.monthly_token_budget,
        "budget_alert_threshold_pct": member.workspace.budget_alert_threshold_pct,
    }
