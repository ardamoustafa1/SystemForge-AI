"""outbox relay hardening columns

Revision ID: 0003_outbox_relay_hardening
Revises: 0002_realtime_messaging_phase1
Create Date: 2026-04-10 01:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_outbox_relay_hardening"
down_revision = "0002_realtime_messaging_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbox_events", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox_events", sa.Column("last_error", sa.Text(), nullable=True))
    op.create_index(
        "ix_outbox_processing_started_at",
        "outbox_events",
        ["processing_started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_processing_started_at", table_name="outbox_events")
    op.drop_column("outbox_events", "last_error")
    op.drop_column("outbox_events", "processing_started_at")
