import difflib

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Design, DesignInput, DesignOutputVersion, WorkspaceMember
from app.services.authorization_service import ensure_design_read_access
from app.schemas.design import (
    DesignInputPayload,
    DesignOutputPayload,
    DesignVersionCompareResponse,
    DesignVersionDetail,
    DesignVersionSummary,
)
from app.services.export_service import build_markdown_export


def _workspace_design(db: Session, design_id: int, workspace_member: WorkspaceMember) -> Design:
    ensure_design_read_access(workspace_member)
    design = db.scalar(
        select(Design).where(Design.id == design_id, Design.workspace_id == workspace_member.workspace_id)
    )
    if not design:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Design not found")
    return design


def list_output_versions(db: Session, workspace_member: WorkspaceMember, design_id: int) -> list[DesignVersionSummary]:
    _workspace_design(db, design_id, workspace_member)
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


def get_output_version_detail(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
    version_id: int,
) -> DesignVersionDetail:
    _workspace_design(db, design_id, workspace_member)
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
    workspace_member: WorkspaceMember,
    design_id: int,
    version_a_id: int,
    version_b_id: int,
) -> DesignVersionCompareResponse:
    design = _workspace_design(db, design_id, workspace_member)
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


def explain_output_diff(
    db: Session,
    workspace_member: WorkspaceMember,
    design_id: int,
    version_a_id: int,
    version_b_id: int,
) -> dict:
    compared = compare_output_versions(db, workspace_member, design_id, version_a_id, version_b_id)
    added = 0
    removed = 0
    for line in compared.diff_markdown.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        if line.startswith("-") and not line.startswith("---"):
            removed += 1
    rationale = []
    if added > removed:
        rationale.append("The newer version introduces additional implementation detail and safeguards.")
    elif removed > added:
        rationale.append("The newer version simplifies parts of the architecture to reduce complexity.")
    else:
        rationale.append("The update mostly rebalances existing decisions instead of changing scope.")
    rationale.append("Review open questions and trade-off sections for decision ownership confirmation.")
    return {
        "version_a_id": version_a_id,
        "version_b_id": version_b_id,
        "added_lines": added,
        "removed_lines": removed,
        "technical_explanation": " ".join(rationale),
    }
