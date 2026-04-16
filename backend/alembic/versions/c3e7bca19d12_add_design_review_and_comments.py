"""Add design review metadata and comments

Revision ID: c3e7bca19d12
Revises: a1f4d2e9c8b1
Create Date: 2026-04-15 14:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c3e7bca19d12"
down_revision = "a1f4d2e9c8b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("designs", sa.Column("review_status", sa.String(length=24), nullable=False, server_default="draft"))
    op.add_column("designs", sa.Column("review_owner_user_id", sa.Integer(), nullable=True))
    op.add_column("designs", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("designs", sa.Column("review_decision_note", sa.Text(), nullable=False, server_default=""))
    op.create_index(op.f("ix_designs_review_owner_user_id"), "designs", ["review_owner_user_id"], unique=False)
    op.create_foreign_key(None, "designs", "users", ["review_owner_user_id"], ["id"], ondelete="SET NULL")
    op.alter_column("designs", "review_status", server_default=None)
    op.alter_column("designs", "review_decision_note", server_default=None)

    op.create_table(
        "design_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("design_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["design_id"], ["designs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_design_comments_design_id"), "design_comments", ["design_id"], unique=False)
    op.create_index(op.f("ix_design_comments_user_id"), "design_comments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_design_comments_user_id"), table_name="design_comments")
    op.drop_index(op.f("ix_design_comments_design_id"), table_name="design_comments")
    op.drop_table("design_comments")

    op.drop_constraint(None, "designs", type_="foreignkey")
    op.drop_index(op.f("ix_designs_review_owner_user_id"), table_name="designs")
    op.drop_column("designs", "review_decision_note")
    op.drop_column("designs", "reviewed_at")
    op.drop_column("designs", "review_owner_user_id")
    op.drop_column("designs", "review_status")

