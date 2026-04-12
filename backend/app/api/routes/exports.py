import re

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.rate_limiter import enforce_rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.design import DesignInputPayload, DesignOutputPayload, ExportResponse
from app.schemas.export_format import ExportFormatQuery
from app.services.design_service import get_design_artifact_for_user
from app.services.export_service import build_pdf_bytes, render_export_content

router = APIRouter(prefix="/designs", tags=["exports"])


def _safe_filename(title: str) -> str:
    """ASCII-only; HTTP Content-Disposition must be latin-1 in Starlette."""
    raw = re.sub(r"[^\w\s\-]", "_", title, flags=re.UNICODE).strip()
    ascii_only = "".join(c if ord(c) < 128 else "_" for c in raw)
    return (ascii_only[:72] or "design").replace(" ", "_")


@router.get(
    "/{design_id}/export",
    responses={
        200: {
            "description": (
                "Depends on `format`: `markdown` (default) returns JSON (`ExportResponse`). "
                "`pdf` returns raw PDF bytes with `Content-Type: application/pdf` (not JSON)."
            ),
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ExportResponse"}},
                "application/pdf": {"schema": {"type": "string", "format": "binary"}},
            },
        }
    },
    summary="Export design as Markdown (JSON) or PDF (binary)",
)
async def get_design_export(
    design_id: int,
    request: Request,
    export_format: ExportFormatQuery = Query(
        default=ExportFormatQuery.markdown,
        alias="format",
        description="`markdown` returns JSON (`ExportResponse`). `pdf` returns raw PDF bytes.",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="design-export-user", identifier=str(user.id), limit=40, window_seconds=60)
    await enforce_rate_limit(scope="design-export-ip", identifier=client_ip, limit=80, window_seconds=60)
    design, design_input, design_output = get_design_artifact_for_user(db=db, user=user, design_id=design_id)
    parsed_input = DesignInputPayload.model_validate(design_input.payload)
    parsed_output = DesignOutputPayload.model_validate(design_output.payload)

    if export_format == ExportFormatQuery.markdown:
        content = render_export_content(
            design_title=design.title,
            design_input=parsed_input,
            output=parsed_output,
            export_format="markdown",
        )
        return ExportResponse(
            design_id=design.id,
            title=design.title,
            format="markdown",
            content=content,
        )

    pdf_bytes = build_pdf_bytes(design.title, parsed_input, parsed_output)
    fn = f"{_safe_filename(design.title)}-systemforge.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )
