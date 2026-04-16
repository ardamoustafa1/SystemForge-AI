from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_active_workspace_member
from app.db.session import get_db
from app.models import WorkspaceMember
from app.schemas.operations import OpsSummaryResponse
from app.services.design_service import get_workspace_ops_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/ops-summary", response_model=OpsSummaryResponse)
def get_ops_summary(
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return get_workspace_ops_summary(db=db, workspace_member=workspace_member)

