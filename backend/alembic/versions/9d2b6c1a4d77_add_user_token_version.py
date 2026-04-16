"""Add user token version

Revision ID: 9d2b6c1a4d77
Revises: f76e4a9f0333
Create Date: 2026-04-15 12:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d2b6c1a4d77"
down_revision = "f76e4a9f0333"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("users", "token_version", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "token_version")

