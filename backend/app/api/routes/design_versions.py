from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.design import DesignVersionCompareResponse, DesignVersionDetail, DesignVersionSummary
from app.services.design_version_service import (
    compare_output_versions,
    get_output_version_detail,
    list_output_versions,
)

router = APIRouter(prefix="/designs", tags=["design-versions"])


@router.get("/{design_id}/versions", response_model=list[DesignVersionSummary])
def list_versions(
    design_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list_output_versions(db, user, design_id)


# Static segment must be registered before `/{version_id}` or "compare" is parsed as an integer id.
@router.get("/{design_id}/versions/compare", response_model=DesignVersionCompareResponse)
def compare_versions(
    design_id: int,
    version_a: int = Query(..., alias="a"),
    version_b: int = Query(..., alias="b"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compare_output_versions(db, user, design_id, version_a, version_b)


@router.get("/{design_id}/versions/{version_id}", response_model=DesignVersionDetail)
def get_version(
    design_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_output_version_detail(db, user, design_id, version_id)
