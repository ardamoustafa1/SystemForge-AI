"""Add refresh token sessions

Revision ID: e1a4f2d7c901
Revises: c3e7bca19d12
Create Date: 2026-04-15 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e1a4f2d7c901"
down_revision = "c3e7bca19d12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_token_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_token_sessions_user_id"), "refresh_token_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_token_sessions_token_hash"), "refresh_token_sessions", ["token_hash"], unique=True)
    op.alter_column("refresh_token_sessions", "is_revoked", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_token_sessions_token_hash"), table_name="refresh_token_sessions")
    op.drop_index(op.f("ix_refresh_token_sessions_user_id"), table_name="refresh_token_sessions")
    op.drop_table("refresh_token_sessions")

