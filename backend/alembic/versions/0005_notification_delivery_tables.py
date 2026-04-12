"""notification delivery tables

Revision ID: 0005_notification_delivery_tables
Revises: 0004_realtime_messaging_indexes
Create Date: 2026-04-10 02:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_notification_delivery_tbls"
down_revision = "0004_realtime_messaging_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_devices",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("device_token", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=True),
        sa.Column("app_version", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "device_token", name="ux_notification_devices_provider_token"),
    )
    op.create_index(
        "ix_notification_devices_user_is_active",
        "notification_devices",
        ["user_id", "is_active"],
        unique=False,
    )

    op.create_table(
        "notification_attempts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("device_token", sa.String(length=255), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_attempts_recipient_created_at",
        "notification_attempts",
        ["recipient_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_notification_attempts_message_recipient",
        "notification_attempts",
        ["message_id", "recipient_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_attempts_message_recipient", table_name="notification_attempts")
    op.drop_index("ix_notification_attempts_recipient_created_at", table_name="notification_attempts")
    op.drop_table("notification_attempts")
    op.drop_index("ix_notification_devices_user_is_active", table_name="notification_devices")
    op.drop_table("notification_devices")
