import re

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.rate_limiter import enforce_rate_limit
from app.db.session import get_db
from app.schemas.design import DesignInputPayload, DesignOutputPayload, ExportResponse, PublicDesignResponse
from app.schemas.export_format import ExportFormatQuery
from app.services.design_service import get_design_artifact_by_share_token, get_public_design_by_token
from app.services.export_service import build_pdf_bytes, render_export_content

router = APIRouter(prefix="/public", tags=["public"])


def _safe_filename(title: str) -> str:
    raw = re.sub(r"[^\w\s\-]", "_", title, flags=re.UNICODE).strip()
    ascii_only = "".join(c if ord(c) < 128 else "_" for c in raw)
    return (ascii_only[:72] or "design").replace(" ", "_")


@router.get("/share/{token}", response_model=PublicDesignResponse)
async def get_shared_design(token: str, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="public-share-ip", identifier=client_ip, limit=120, window_seconds=60)
    return get_public_design_by_token(db=db, token=token)


@router.get(
    "/share/{token}/export",
    responses={
        200: {
            "description": (
                "Same contract as authenticated export: `format=markdown` is JSON; `format=pdf` is binary PDF."
            ),
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ExportResponse"}},
                "application/pdf": {"schema": {"type": "string", "format": "binary"}},
            },
        }
    },
    summary="Export shared design (Markdown JSON or PDF binary)",
)
async def export_shared_design(
    token: str,
    request: Request,
    export_format: ExportFormatQuery = Query(
        default=ExportFormatQuery.markdown,
        alias="format",
        description="`markdown` returns JSON; `pdf` returns binary PDF.",
    ),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="public-share-export-ip", identifier=client_ip, limit=60, window_seconds=60)
    design, design_input, design_output = get_design_artifact_by_share_token(db=db, token=token)
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
