"""design output version history for regenerate diff

Revision ID: 0007_output_versions
Revises: 0006_des_discuss_fk
Create Date: 2026-04-11 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_output_versions"
down_revision = "0006_des_discuss_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "design_output_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("design_id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("markdown_export", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=80), nullable=False),
        sa.Column("generation_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scale_stance", sa.String(length=20), nullable=False, server_default="balanced"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["design_id"], ["designs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_design_output_versions_design_id", "design_output_versions", ["design_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_design_output_versions_design_id", table_name="design_output_versions")
    op.drop_table("design_output_versions")
