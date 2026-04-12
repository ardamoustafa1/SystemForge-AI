import difflib

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Design, DesignInput, DesignOutputVersion, User
from app.schemas.design import (
    DesignInputPayload,
    DesignOutputPayload,
    DesignVersionCompareResponse,
    DesignVersionDetail,
    DesignVersionSummary,
)
from app.services.export_service import build_markdown_export


def _owned_design(db: Session, design_id: int, owner_id: int) -> Design:
    design = db.scalar(select(Design).where(Design.id == design_id, Design.owner_id == owner_id))
    if not design:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Design not found")
    return design


def list_output_versions(db: Session, user: User, design_id: int) -> list[DesignVersionSummary]:
    _owned_design(db, design_id, user.id)
    rows = db.scalars(
        select(DesignOutputVersion)
        .where(DesignOutputVersion.design_id == design_id)
        .order_by(desc(DesignOutputVersion.created_at))
    ).all()
    return [
        DesignVersionSummary(
            id=r.id,
            created_at=r.created_at,
            model_name=r.model_name,
            generation_ms=r.generation_ms,
            scale_stance=r.scale_stance,
        )
        for r in rows
    ]


def get_output_version_detail(db: Session, user: User, design_id: int, version_id: int) -> DesignVersionDetail:
    _owned_design(db, design_id, user.id)
    row = db.scalar(
        select(DesignOutputVersion).where(
            DesignOutputVersion.id == version_id,
            DesignOutputVersion.design_id == design_id,
        )
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return DesignVersionDetail(
        id=row.id,
        design_id=design_id,
        created_at=row.created_at,
        model_name=row.model_name,
        generation_ms=row.generation_ms,
        scale_stance=row.scale_stance,
        output=DesignOutputPayload.model_validate(row.payload),
    )


def compare_output_versions(
    db: Session,
    user: User,
    design_id: int,
    version_a_id: int,
    version_b_id: int,
) -> DesignVersionCompareResponse:
    design = _owned_design(db, design_id, user.id)
    va = db.scalar(
        select(DesignOutputVersion).where(
            DesignOutputVersion.id == version_a_id,
            DesignOutputVersion.design_id == design_id,
        )
    )
    vb = db.scalar(
        select(DesignOutputVersion).where(
            DesignOutputVersion.id == version_b_id,
            DesignOutputVersion.design_id == design_id,
        )
    )
    if not va or not vb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both versions not found")

    inp = db.scalar(select(DesignInput).where(DesignInput.design_id == design_id))
    if not inp:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Design input missing")
    parsed_in = DesignInputPayload.model_validate(inp.payload)

    out_a = DesignOutputPayload.model_validate(va.payload)
    out_b = DesignOutputPayload.model_validate(vb.payload)
    md_a = build_markdown_export(design.title, parsed_in, out_a)
    md_b = build_markdown_export(design.title, parsed_in, out_b)
    diff_lines = difflib.unified_diff(
        md_a.splitlines(),
        md_b.splitlines(),
        fromfile=f"version-{version_a_id}",
        tofile=f"version-{version_b_id}",
        lineterm="",
    )
    diff_markdown = "```diff\n" + "\n".join(diff_lines) + "\n```"
    return DesignVersionCompareResponse(
        version_a_id=version_a_id,
        version_b_id=version_b_id,
        diff_markdown=diff_markdown,
    )
