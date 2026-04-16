import base64
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.deps import get_active_workspace_member
from app.core.async_bridge import run_async
from app.core.rate_limiter import enforce_rate_limit
from app.db.session import get_db
from app.models import WorkspaceMember
from app.schemas.design import (
    CostAnalysisRequest,
    CostAnalysisResponse,
    DesignInputPayload,
    DesignOutputPayload,
    ExportJobCreateResponse,
    ExportJobStatusResponse,
    ExportResponse,
)
from app.schemas.export_format import ExportFormatQuery
from app.services.design_service import get_design_artifact_for_user
from app.services.export_service import build_pdf_bytes, render_export_content
from app.services.export_job_service import enqueue_export_job, get_export_job
from app.core.idempotency import enforce_idempotency
from app.services.scaffold_service import build_scaffold_zip
from app.services.terraform_service import build_terraform_zip

router = APIRouter(prefix="/designs", tags=["exports"])


def _enforce_export_job_access(job: dict, workspace_member: WorkspaceMember) -> None:
    job_workspace_id = job.get("workspace_id")
    job_user_id = job.get("user_id")
    if job_workspace_id is None or job_user_id is None:
        raise HTTPException(status_code=403, detail="Export job ownership metadata is missing")
    if int(job_workspace_id) != workspace_member.workspace_id or int(job_user_id) != workspace_member.user_id:
        raise HTTPException(status_code=403, detail="Export job access denied")


def _safe_filename(title: str) -> str:
    """ASCII-only; HTTP Content-Disposition must be latin-1 in Starlette."""
    raw = re.sub(r"[^\w\s\-]", "_", title, flags=re.UNICODE).strip()
    ascii_only = "".join(c if ord(c) < 128 else "_" for c in raw)
    return (ascii_only[:72] or "design").replace(" ", "_")  # type: ignore


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
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="design-export-user", identifier=str(workspace_member.user_id), limit=40, window_seconds=60)
    await enforce_rate_limit(scope="design-export-ip", identifier=client_ip, limit=80, window_seconds=60)
    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
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


@router.post(
    "/{design_id}/export-jobs",
    response_model=ExportJobCreateResponse,
    status_code=202,
    summary="Queue an async export job for large downloads",
)
def create_design_export_job(
    design_id: int,
    request: Request,
    export_format: str = Query(default="pdf"),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if export_format not in {"pdf", "markdown"}:
        raise HTTPException(status_code=400, detail="Unsupported export format for async jobs")
    client_ip = request.client.host if request.client else "unknown"
    run_async(enforce_rate_limit(scope="design-export-job-user", identifier=str(workspace_member.user_id), limit=15, window_seconds=60))
    run_async(enforce_rate_limit(scope="design-export-job-ip", identifier=client_ip, limit=30, window_seconds=60))
    run_async(enforce_idempotency(
        scope="design-export-job",
        owner_key=f"{workspace_member.workspace_id}:{design_id}:{workspace_member.user_id}:{export_format}",
        idempotency_key=idempotency_key,
        ttl_seconds=180,
    ))
    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
    parsed_input = DesignInputPayload.model_validate(design_input.payload)
    parsed_output = DesignOutputPayload.model_validate(design_output.payload)
    job_id = run_async(enqueue_export_job(
        design_title=design.title,
        design_input=parsed_input,
        design_output=parsed_output,
        export_format=export_format,  # type: ignore[arg-type]
        workspace_id=workspace_member.workspace_id,
        user_id=workspace_member.user_id,
        design_id=design_id,
    ))
    return ExportJobCreateResponse(job_id=job_id, status="queued")


@router.get("/export-jobs/{job_id}", response_model=ExportJobStatusResponse)
async def get_design_export_job_status(
    job_id: str,
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    job = await get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    _enforce_export_job_access(job, workspace_member)
    return ExportJobStatusResponse(
        job_id=job_id,
        status=job.get("status", "failed"),
        format=job.get("format"),
        filename=job.get("filename"),
        error=job.get("error"),
    )


@router.get("/export-jobs/{job_id}/download")
async def download_design_export_job(
    job_id: str,
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    job = await get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    _enforce_export_job_access(job, workspace_member)
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Export job is not completed yet")
    content_b64 = job.get("content_b64")
    if not content_b64:
        raise HTTPException(status_code=500, detail="Export job content missing")
    content = base64.b64decode(content_b64.encode("ascii"))
    filename = str(job.get("filename") or "design-export.bin")
    return Response(
        content=content,
        media_type=str(job.get("mime_type") or "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{design_id}/export/scaffold",
    summary="Download project scaffold ZIP generated from the AI design output",
    response_class=Response,
)
async def get_scaffold_export(
    design_id: int,
    request: Request,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="scaffold-export-user", identifier=str(workspace_member.user_id), limit=10, window_seconds=60)
    await enforce_rate_limit(scope="scaffold-export-ip", identifier=client_ip, limit=20, window_seconds=60)

    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
    if not design_output:
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_400_BAD_REQUEST, detail="Design has no generated output yet")

    parsed_input = DesignInputPayload.model_validate(design_input.payload)
    parsed_output = DesignOutputPayload.model_validate(design_output.payload)

    zip_bytes = build_scaffold_zip(title=design.title, design_input=parsed_input, design_output=parsed_output)
    fn = f"{_safe_filename(design.title)}-scaffold.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@router.get(
    "/{design_id}/export/terraform",
    summary="Download Terraform IaC ZIP generated from the AI design output",
    response_class=Response,
)
async def get_terraform_export(
    design_id: int,
    request: Request,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="tf-export-user", identifier=str(workspace_member.user_id), limit=10, window_seconds=60)
    await enforce_rate_limit(scope="tf-export-ip", identifier=client_ip, limit=20, window_seconds=60)

    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
    if not design_output:
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_400_BAD_REQUEST, detail="Design has no generated output yet")

    parsed_input = DesignInputPayload.model_validate(design_input.payload)
    parsed_output = DesignOutputPayload.model_validate(design_output.payload)

    zip_bytes = build_terraform_zip(title=design.title, design_input=parsed_input, design_output=parsed_output)
    fn = f"{_safe_filename(design.title)}-terraform.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@router.get(
    "/{design_id}/export/tasks-csv",
    summary="Download Jira/Linear compatible task CSV from the engineering checklist",
    response_class=Response,
)
async def get_tasks_csv_export(
    design_id: int,
    request: Request,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    provider: str = Query(default="jira", description="Either 'jira' or 'linear'"),
):
    import csv
    import io

    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(scope="csv-export-user", identifier=str(workspace_member.user_id), limit=20, window_seconds=60)
    await enforce_rate_limit(scope="csv-export-ip", identifier=client_ip, limit=40, window_seconds=60)

    design, design_input, design_output = get_design_artifact_for_user(
        db=db, workspace_member=workspace_member, design_id=design_id
    )
    if not design_output:
        from fastapi import HTTPException, status as st
        raise HTTPException(status_code=st.HTTP_400_BAD_REQUEST, detail="Design has no generated output yet")

    parsed_output = DesignOutputPayload.model_validate(design_output.payload)
    checklist = parsed_output.engineering_checklist

    buf = io.StringIO()
    writer = csv.writer(buf)

    if provider.lower() == "linear":
        writer.writerow(["Title", "Description", "Priority", "Status"])
        for item in checklist:
            writer.writerow([item, f"Implementation task imported from SystemForge AI\\n\\nProject: {design.title}", "Medium", "Todo"])
    else:
        # Default Jira format
        writer.writerow(["Summary", "Issue Type", "Description", "Priority"])
        for item in checklist:
            writer.writerow([item, "Task", f"Implementation task imported from SystemForge AI\\n\\nProject: {design.title}", "Medium"])

    fn = f"{_safe_filename(design.title)}-tasks.csv"

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@router.post(
    "/{design_id}/cost-analysis",
    response_model=CostAnalysisResponse,
    summary="Run scenario-based cloud cost analysis",
)
def analyze_design_cost(
    design_id: int,
    body: CostAnalysisRequest,
    request: Request,
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    client_ip = request.client.host if request.client else "unknown"
    run_async(enforce_rate_limit(scope="cost-analysis-user", identifier=str(workspace_member.user_id), limit=30, window_seconds=60))
    run_async(enforce_rate_limit(scope="cost-analysis-ip", identifier=client_ip, limit=60, window_seconds=60))
    run_async(enforce_idempotency(
        scope="cost-analysis",
        owner_key=f"{workspace_member.workspace_id}:{workspace_member.user_id}:{design_id}",
        idempotency_key=idempotency_key,
        ttl_seconds=90,
    ))
    design, _, design_output = get_design_artifact_for_user(db=db, workspace_member=workspace_member, design_id=design_id)
    parsed_output = DesignOutputPayload.model_validate(design_output.payload)
    estimated = parsed_output.estimated_cloud_cost
    if not estimated:
        return CostAnalysisResponse(
            design_id=design.id,
            monthly_usd_min=0,
            monthly_usd_max=0,
            yearly_usd_min=0,
            yearly_usd_max=0,
            confidence="low",
            breakdown=["Base design does not include a cloud cost baseline yet."],
            optimization_recommendations=["Regenerate design with more explicit traffic assumptions for stronger estimates."],
        )

    reliability_factor = {"lean": 0.85, "balanced": 1.0, "critical": 1.35}[body.reliability_profile]
    multiplier = body.traffic_multiplier * body.data_multiplier * reliability_factor
    monthly_min = int(round(estimated.monthly_usd_min * multiplier))
    monthly_max = int(round(estimated.monthly_usd_max * multiplier))
    confidence: str = "medium"
    if body.traffic_multiplier >= 3 or body.data_multiplier >= 3:
        confidence = "low"
    elif 0.75 <= multiplier <= 1.5:
        confidence = "high"
    return CostAnalysisResponse(
        design_id=design.id,
        monthly_usd_min=monthly_min,
        monthly_usd_max=monthly_max,
        yearly_usd_min=monthly_min * 12,
        yearly_usd_max=monthly_max * 12,
        confidence=confidence,  # type: ignore[arg-type]
        breakdown=[
            *estimated.cost_breakdown,
            f"Scenario multipliers -> traffic x{body.traffic_multiplier:.2f}, data x{body.data_multiplier:.2f}, reliability {body.reliability_profile}.",
        ],
        optimization_recommendations=[
            "Right-size always-on compute pools with autoscaling guardrails.",
            "Cap cross-region egress via caching and regional read replicas.",
            "Set workspace-level budget alerts and enforce monthly token quotas.",
        ],
    )
