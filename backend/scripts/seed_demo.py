"""Seed a local demo workspace with realistic SystemForge AI examples.

This script is intentionally idempotent. It is safe to run on every local
Docker Compose startup because it updates/creates only the demo user,
workspace, and named showcase designs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Design, DesignInput, DesignOutput, RoleEnum, User, UserSettings, Workspace, WorkspaceMember
from app.schemas.design import DesignInputPayload, ScaleStance
from app.services.export_service import build_markdown_export
from app.services.generation_service import generate_structured_design


DEMO_EMAIL = os.getenv("DEMO_USER_EMAIL", "demo@systemforge.dev")
DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "SystemForgeDemo123!")
DEMO_FULL_NAME = os.getenv("DEMO_USER_FULL_NAME", "SystemForge Demo")
DEMO_WORKSPACE = os.getenv("DEMO_WORKSPACE_NAME", "SystemForge Showcase")


@dataclass(frozen=True)
class DemoBrief:
    title: str
    payload: DesignInputPayload
    scale_stance: ScaleStance = "balanced"
    review_status: str = "approved"


SHOWCASE_BRIEFS = [
    DemoBrief(
        title="Multi-tenant SaaS Control Plane",
        payload=DesignInputPayload(
            project_title="Multi-tenant SaaS Control Plane",
            project_type="B2B SaaS",
            problem_statement=(
                "Design a workspace-first SaaS control plane for product teams that need tenant isolation, "
                "role based access, audit trails, usage budgets, and reliable asynchronous jobs."
            ),
            expected_users="50k registered users, 2k daily active workspace admins",
            traffic_assumptions="Read-heavy dashboard traffic with short bursts during generation and export jobs",
            budget_sensitivity="medium",
            preferred_stack="Next.js, FastAPI, PostgreSQL, Redis Streams, Kubernetes",
            constraints="Keep tenant boundaries explicit and avoid cross-workspace data leakage.",
            deployment_scope="single-region",
            data_sensitivity="high",
            real_time_required=True,
            mode="product",
            document_context="",
        ),
    ),
    DemoBrief(
        title="Marketplace Order & Fulfillment Platform",
        payload=DesignInputPayload(
            project_title="Marketplace Order & Fulfillment Platform",
            project_type="Marketplace",
            problem_statement=(
                "Design a seller marketplace where buyers can place orders, sellers manage inventory, "
                "payments are reconciled asynchronously, and fulfillment events are visible in real time."
            ),
            expected_users="250k buyers, 12k sellers, 20k daily orders",
            traffic_assumptions="Spiky checkout traffic, seller dashboard polling, webhook bursts from payment providers",
            budget_sensitivity="high",
            preferred_stack="React, FastAPI, PostgreSQL, Redis, Stripe webhooks, Docker",
            constraints="Payment events must be idempotent and inventory updates must be race-safe.",
            deployment_scope="multi-region",
            data_sensitivity="critical",
            real_time_required=True,
            mode="product",
            document_context="",
        ),
        scale_stance="conservative",
        review_status="in_review",
    ),
    DemoBrief(
        title="AI Workflow Automation Hub",
        payload=DesignInputPayload(
            project_title="AI Workflow Automation Hub",
            project_type="AI workflow platform",
            problem_statement=(
                "Design an automation hub where teams compose AI workflows, queue model calls, track token budgets, "
                "retry failed jobs, and export architecture artifacts for review."
            ),
            expected_users="10k teams, 1M monthly workflow runs",
            traffic_assumptions="Background job heavy traffic with model-provider latency variance and periodic tenant bursts",
            budget_sensitivity="medium",
            preferred_stack="Next.js, FastAPI, PostgreSQL, Redis Streams, OpenTelemetry, Helm",
            constraints="Provider failures must degrade gracefully and all generated artifacts need schema validation.",
            deployment_scope="global",
            data_sensitivity="medium",
            real_time_required=False,
            mode="product",
            document_context="",
        ),
        scale_stance="aggressive",
        review_status="approved",
    ),
]


def ensure_demo_user(db) -> tuple[User, Workspace]:
    user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(
            email=DEMO_EMAIL,
            full_name=DEMO_FULL_NAME,
            password_hash=hash_password(DEMO_PASSWORD),
            is_active=True,
        )
        db.add(user)
        db.flush()

    workspace = None
    if user.default_workspace_id:
        workspace = db.get(Workspace, user.default_workspace_id)
    if workspace is None:
        existing_member = db.scalar(
            select(WorkspaceMember)
            .where(WorkspaceMember.user_id == user.id)
            .order_by(WorkspaceMember.id.asc())
        )
        if existing_member is not None:
            workspace = db.get(Workspace, existing_member.workspace_id)
        if workspace is None:
            workspace = Workspace(name=DEMO_WORKSPACE, monthly_token_budget=500_000, budget_alert_threshold_pct=80)
            db.add(workspace)
            db.flush()
        user.default_workspace_id = workspace.id
        db.flush()

    member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if member is None:
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=RoleEnum.admin))

    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user.id))
    if settings is None:
        db.add(UserSettings(user_id=user.id, theme="dark", default_mode="product"))

    return user, workspace


async def upsert_design(db, user: User, workspace: Workspace, brief: DemoBrief) -> None:
    existing = db.scalar(
        select(Design).where(
            Design.workspace_id == workspace.id,
            Design.title == brief.title,
        )
    )
    output, generation_ms, model_name = await generate_structured_design(
        brief.payload,
        scale_stance=brief.scale_stance,
    )
    markdown = build_markdown_export(brief.title, brief.payload, output)

    if existing is None:
        design = Design(
            owner_id=user.id,
            workspace_id=workspace.id,
            title=brief.title,
            project_type=brief.payload.project_type,
            status="completed",
            review_status=brief.review_status,
            notes="Seeded local demo artifact. Safe to delete or regenerate.",
        )
        db.add(design)
        db.flush()
        db.add(DesignInput(design_id=design.id, payload=brief.payload.model_dump()))
        db.add(
            DesignOutput(
                design_id=design.id,
                payload=output.model_dump(),
                markdown_export=markdown,
                model_name=model_name,
                generation_ms=generation_ms,
            )
        )
        return

    existing.project_type = brief.payload.project_type
    existing.status = "completed"
    existing.review_status = brief.review_status
    existing.notes = existing.notes or "Seeded local demo artifact. Safe to delete or regenerate."
    if existing.input is None:
        db.add(DesignInput(design_id=existing.id, payload=brief.payload.model_dump()))
    else:
        existing.input.payload = brief.payload.model_dump()
    if existing.output is None:
        db.add(
            DesignOutput(
                design_id=existing.id,
                payload=output.model_dump(),
                markdown_export=markdown,
                model_name=model_name,
                generation_ms=generation_ms,
            )
        )
    else:
        existing.output.payload = output.model_dump()
        existing.output.markdown_export = markdown
        existing.output.model_name = model_name
        existing.output.generation_ms = generation_ms


async def main() -> None:
    db = SessionLocal()
    try:
        user, workspace = ensure_demo_user(db)
        for brief in SHOWCASE_BRIEFS:
            await upsert_design(db, user=user, workspace=workspace, brief=brief)
        db.commit()
        print("Demo workspace ready")
        print(f"Email: {DEMO_EMAIL}")
        print(f"Password: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
