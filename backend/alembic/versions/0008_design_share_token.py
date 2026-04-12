"""design share_token for read-only public links

Revision ID: 0008_share_token
Revises: 0007_output_versions
Create Date: 2026-04-11 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_share_token"
down_revision = "0007_output_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("designs", sa.Column("share_token", sa.String(length=64), nullable=True))
    op.create_index("ix_designs_share_token", "designs", ["share_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_designs_share_token", table_name="designs")
    op.drop_column("designs", "share_token")
