"""add api_key_hash

Revision ID: 1234567890ab
Revises: e1a4f2d7c901
Create Date: 2026-06-21 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "1234567890ab"
down_revision = "e1a4f2d7c901"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("user_settings", sa.Column("api_key_hash", sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column("user_settings", "api_key_hash")
