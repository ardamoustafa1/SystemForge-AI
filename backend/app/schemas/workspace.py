from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

WorkspaceRole = Literal["admin", "editor", "viewer"]


class WorkspaceSummary(BaseModel):
    id: int
    name: str
    role: WorkspaceRole
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceDetail(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    monthly_token_budget: int = 200000
    budget_alert_threshold_pct: int = 80

    model_config = {"from_attributes": True}


class WorkspaceMemberOut(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: str
    role: WorkspaceRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class UpdateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class InviteMemberRequest(BaseModel):
    email: str
    role: WorkspaceRole = "viewer"


class UpdateMemberRoleRequest(BaseModel):
    role: WorkspaceRole


class ActiveWorkspaceResponse(BaseModel):
    workspace: WorkspaceDetail
    role: WorkspaceRole
    members: list[WorkspaceMemberOut]

    model_config = {"from_attributes": True}


class WorkspaceBudgetResponse(BaseModel):
    workspace_id: int
    monthly_token_budget: int
    budget_alert_threshold_pct: int


class UpdateWorkspaceBudgetRequest(BaseModel):
    monthly_token_budget: int = Field(..., ge=10_000, le=10_000_000)
    budget_alert_threshold_pct: int = Field(..., ge=50, le=99)
