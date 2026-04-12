"""link designs to discussion conversations

Revision ID: 0006_des_discuss_fk (must be <=32 chars for alembic_version)
Revises: 0005_notification_delivery_tbls
Create Date: 2026-04-11 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_des_discuss_fk"
down_revision = "0005_notification_delivery_tbls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "designs",
        sa.Column("discussion_conversation_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_designs_discussion_conversation_id",
        "designs",
        "conversations",
        ["discussion_conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_designs_discussion_conversation_id",
        "designs",
        ["discussion_conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_designs_discussion_conversation_id", table_name="designs")
    op.drop_constraint("fk_designs_discussion_conversation_id", "designs", type_="foreignkey")
    op.drop_column("designs", "discussion_conversation_id")
