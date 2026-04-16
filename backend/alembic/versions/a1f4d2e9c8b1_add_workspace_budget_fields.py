"""Add workspace budget fields

Revision ID: a1f4d2e9c8b1
Revises: 9d2b6c1a4d77
Create Date: 2026-04-15 12:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "a1f4d2e9c8b1"
down_revision = "9d2b6c1a4d77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("monthly_token_budget", sa.Integer(), nullable=False, server_default="200000"))
    op.add_column("workspaces", sa.Column("budget_alert_threshold_pct", sa.Integer(), nullable=False, server_default="80"))
    op.alter_column("workspaces", "monthly_token_budget", server_default=None)
    op.alter_column("workspaces", "budget_alert_threshold_pct", server_default=None)


def downgrade() -> None:
    op.drop_column("workspaces", "budget_alert_threshold_pct")
    op.drop_column("workspaces", "monthly_token_budget")

