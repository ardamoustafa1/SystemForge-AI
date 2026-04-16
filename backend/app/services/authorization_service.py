from __future__ import annotations

from fastapi import HTTPException, status

from app.models import RoleEnum, WorkspaceMember


def ensure_design_read_access(_: WorkspaceMember) -> None:
    return


def ensure_design_write_access(member: WorkspaceMember) -> None:
    if member.role == RoleEnum.viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer role cannot modify designs")


def ensure_design_share_access(member: WorkspaceMember) -> None:
    if member.role == RoleEnum.viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer role cannot manage share settings")

