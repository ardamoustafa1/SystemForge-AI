from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.auth.deps import get_active_workspace_member, require_workspace_role
from app.db.session import get_db
from app.models import Design, DesignOutput, RoleEnum, WorkspaceMember
from app.schemas.design import DesignInputPayload, DesignOutputPayload
from app.services.job_center_service import list_jobs
from app.services.live_cost_service import (
    get_cloud_pricing,
    get_workspace_usage,
    report_workspace_usage,
    sync_cloud_pricing,
)
from app.services.template_policy_service import get_template_policy, update_template_policy
from app.core.idempotency import enforce_idempotency
from app.core.async_bridge import run_async
from app.services.export_job_service import enqueue_export_job
from app.services.design_service import get_design_artifact_for_user

router = APIRouter(tags=["advanced-features"])


@router.get("/dashboard/job-center")
async def job_center(
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    generation_rows = (
        db.query(DesignOutput)
        .join(Design, Design.id == DesignOutput.design_id)
        .filter(Design.workspace_id == workspace_member.workspace_id)
        .order_by(DesignOutput.updated_at.desc())
        .limit(20)
        .all()
    )
    return {
        "jobs": await list_jobs(workspace_member.workspace_id, workspace_member.user_id),
        "recent_generations": [
            {"design_id": row.design_id, "generation_ms": row.generation_ms, "updated_at": row.updated_at.isoformat()}
            for row in generation_rows
        ],
    }


@router.post("/dashboard/job-center/retry")
def retry_job(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("job-center-retry", f"{workspace_member.workspace_id}:{workspace_member.user_id}", idempotency_key, 90))
    job_type = str(payload.get("job_type", ""))
    design_id = int(payload.get("design_id", 0) or 0)
    if design_id <= 0:
        raise HTTPException(status_code=400, detail="design_id is required")
    if job_type == "export":
        export_format = str(payload.get("format", "pdf"))
        design, design_input, design_output = get_design_artifact_for_user(db, workspace_member, design_id)
        if not design_output:
            raise HTTPException(status_code=400, detail="Design output missing")
        job_id = run_async(
            enqueue_export_job(
                design_title=design.title,
                design_input=DesignInputPayload.model_validate(design_input.payload),
                design_output=DesignOutputPayload.model_validate(design_output.payload),
                export_format=export_format,  # type: ignore[arg-type]
                workspace_id=workspace_member.workspace_id,
                user_id=workspace_member.user_id,
                design_id=design_id,
            )
        )
        return {"ok": True, "job_id": job_id}
    if job_type == "generation":
        design = db.get(Design, design_id)
        if not design or design.workspace_id != workspace_member.workspace_id:
            raise HTTPException(status_code=404, detail="Design not found")
        design.status = "generating"
        db.commit()
        from app.services.design_service import _enqueue_generation  # local import
        run_async(_enqueue_generation(design_id, "balanced", "en"))
        return {"ok": True, "job_type": "generation"}
    raise HTTPException(status_code=400, detail="Unsupported job_type")


@router.post("/cost/pricing-sync")
async def pricing_sync(
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    require_workspace_role(workspace_member, RoleEnum.admin, RoleEnum.editor)
    await enforce_idempotency("cost-pricing-sync", f"{workspace_member.workspace_id}:{workspace_member.user_id}", idempotency_key, 120)
    return await sync_cloud_pricing()


@router.get("/cost/pricing")
async def pricing_view(
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    _ = workspace_member
    return await get_cloud_pricing()


@router.post("/workspaces/{workspace_id}/cost/usage")
async def report_usage(
    workspace_id: int,
    payload: dict = Body(...),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if workspace_member.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    require_workspace_role(workspace_member, RoleEnum.admin, RoleEnum.editor)
    await enforce_idempotency("cost-usage-report", f"{workspace_id}:{workspace_member.user_id}", idempotency_key, 180)
    monthly_actual_usd = int(payload.get("monthly_actual_usd", 0))
    source = str(payload.get("source", "manual"))
    return await report_workspace_usage(workspace_id, monthly_actual_usd=monthly_actual_usd, source=source)


@router.get("/workspaces/{workspace_id}/cost/usage")
async def usage_view(
    workspace_id: int,
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    if workspace_member.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    return await get_workspace_usage(workspace_id)


@router.get("/workspaces/{workspace_id}/templates-policy")
async def get_templates_policy_route(
    workspace_id: int,
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    if workspace_member.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    return await get_template_policy(workspace_id)


@router.put("/workspaces/{workspace_id}/templates-policy")
async def put_templates_policy_route(
    workspace_id: int,
    payload: dict = Body(...),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if workspace_member.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    require_workspace_role(workspace_member, RoleEnum.admin, RoleEnum.editor)
    await enforce_idempotency("template-policy-update", f"{workspace_id}:{workspace_member.user_id}", idempotency_key, 180)
    return await update_template_policy(workspace_id, payload)


@router.post("/designs/{design_id}/drift-detection")
def drift_detection(
    design_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("drift-detection", f"{workspace_member.workspace_id}:{workspace_member.user_id}:{design_id}", idempotency_key, 120))
    from app.services.design_service import get_design_artifact_for_user
    design, design_input, design_output = get_design_artifact_for_user(db, workspace_member, design_id)
    observed_p95 = int(payload.get("observed_p95_ms", 0))
    observed_monthly_cost = int(payload.get("observed_monthly_usd", 0))
    expected_cost = 0
    if design_output and design_output.payload:
        est = (design_output.payload or {}).get("estimated_cloud_cost") or {}
        expected_cost = int(est.get("monthly_usd_max", 0) or 0)
    drift_items: list[str] = []
    if observed_p95 > 400:
        drift_items.append("Latency drift detected against baseline architecture assumptions.")
    if expected_cost and observed_monthly_cost > int(expected_cost * 1.2):
        drift_items.append("Cloud cost drift detected (actual > 120% of estimated max).")
    return {
        "design_id": design.id,
        "drift_detected": len(drift_items) > 0,
        "drift_items": drift_items,
        "observed": payload,
        "expected_cost_max": expected_cost,
        "input_snapshot": {"traffic_assumptions": (design_input.payload or {}).get("traffic_assumptions", "")},
    }


@router.post("/designs/{design_id}/roadmap-autopilot")
def roadmap_autopilot(
    design_id: int,
    provider: str = Query(default="jira"),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    run_async(enforce_idempotency("roadmap-autopilot", f"{workspace_member.workspace_id}:{workspace_member.user_id}:{design_id}:{provider}", idempotency_key, 120))
    from app.services.design_service import get_design_artifact_for_user
    _, _, design_output = get_design_artifact_for_user(db, workspace_member, design_id)
    if not design_output:
        raise HTTPException(status_code=400, detail="Design output missing")
    checklist = (design_output.payload or {}).get("engineering_checklist") or []
    items = []
    for idx, item in enumerate(checklist[:100], start=1):
        effort = 2 if len(str(item)) < 60 else 5
        items.append(
            {
                "id": idx,
                "title": item,
                "estimate_points": effort,
                "provider": provider,
                "status": "todo",
            }
        )
    return {"design_id": design_id, "provider": provider, "backlog_items": items}

