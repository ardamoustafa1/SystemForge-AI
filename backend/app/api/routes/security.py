from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_active_workspace_member, require_workspace_role
from app.db.session import get_db
from app.models import RoleEnum, WorkspaceMember
from app.services.abuse_analytics_service import get_abuse_summary
from app.services.security_audit_service import list_security_audit

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/abuse-summary")
async def abuse_summary(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    _ = db
    require_workspace_role(workspace_member, RoleEnum.admin)
    return await get_abuse_summary(days=days)


@router.get("/audit-trail")
async def audit_trail(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    _ = db
    require_workspace_role(workspace_member, RoleEnum.admin)
    rows = await list_security_audit(limit=limit)
    scoped = [r for r in rows if r.get("workspace_id") in {None, workspace_member.workspace_id}]
    return {"items": scoped}


@router.get("/anomaly-summary")
async def anomaly_summary(
    db: Session = Depends(get_db),
    workspace_member: WorkspaceMember = Depends(get_active_workspace_member),
):
    _ = db
    require_workspace_role(workspace_member, RoleEnum.admin)
    abuse = await get_abuse_summary(days=7)
    high = int(abuse.get("high_severity", 0))
    rate_limited = int(abuse.get("rate_limit", 0))
    ws_events = int(abuse.get("ws_rate_limited", 0)) + int(abuse.get("ws_payload_too_large", 0))
    anomalies: list[str] = []
    if high >= 10:
        anomalies.append("High severity abuse events exceeded weekly baseline")
    if ws_events >= 20:
        anomalies.append("WebSocket abuse events above normal threshold")
    if rate_limited >= 100:
        anomalies.append("API rate-limit pressure indicates possible automated misuse")
    return {
        "workspace_id": workspace_member.workspace_id,
        "anomaly_score": min(100, high * 5 + ws_events + (rate_limited // 5)),
        "anomalies": anomalies,
        "signals": {"high_severity": high, "rate_limited": rate_limited, "ws_events": ws_events},
    }

