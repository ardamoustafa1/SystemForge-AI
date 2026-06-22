"""add API key metadata fields

Revision ID: b7d9e2f4a611
Revises: 1234567890ab
"""

from alembic import op
import sqlalchemy as sa


revision = "b7d9e2f4a611"
down_revision = "1234567890ab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("api_key_last4", sa.String(length=4), nullable=True))
    op.add_column("user_settings", sa.Column("api_key_created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_settings", sa.Column("api_key_revoked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "api_key_revoked_at")
    op.drop_column("user_settings", "api_key_created_at")
    op.drop_column("user_settings", "api_key_last4")
