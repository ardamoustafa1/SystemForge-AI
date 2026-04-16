from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_active_workspace_member
from app.db.session import get_db
from app.models import WorkspaceMember
from app.schemas.design import DesignVersionCompareResponse, DesignVersionDetail, DesignVersionSummary
from app.services.design_version_service import (
    compare_output_versions,
    explain_output_diff,
    get_output_version_detail,
    list_output_versions,
)

router = APIRouter(prefix="/designs", tags=["design-versions"])


@router.get("/{design_id}/versions", response_model=list[DesignVersionSummary])
def list_versions(
    design_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return list_output_versions(db, workspace_member, design_id)


# Static segment must be registered before `/{version_id}` or "compare" is parsed as an integer id.
@router.get("/{design_id}/versions/compare", response_model=DesignVersionCompareResponse)
def compare_versions(
    design_id: int,
    version_a: int = Query(..., alias="a"),
    version_b: int = Query(..., alias="b"),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return compare_output_versions(db, workspace_member, design_id, version_a, version_b)


@router.get("/{design_id}/versions/{version_id}", response_model=DesignVersionDetail)
def get_version(
    design_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return get_output_version_detail(db, workspace_member, design_id, version_id)


@router.get("/{design_id}/versions/explain")
def explain_versions(
    design_id: int,
    version_a: int = Query(..., alias="a"),
    version_b: int = Query(..., alias="b"),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    return explain_output_diff(db, workspace_member, design_id, version_a, version_b)
