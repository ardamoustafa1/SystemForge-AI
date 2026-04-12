"""realtime messaging indexes and constraints

Revision ID: 0004_realtime_messaging_indexes
Revises: 0003_outbox_relay_hardening
Create Date: 2026-04-10 02:00:00
"""

from alembic import op


revision = "0004_realtime_messaging_indexes"
down_revision = "0003_outbox_relay_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "ux_messages_conversation_server_seq",
        "messages",
        ["conversation_id", "server_seq"],
    )
    op.create_index(
        "ix_messages_conversation_id_server_seq",
        "messages",
        ["conversation_id", "server_seq"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_members_user_id_left_at",
        "conversation_members",
        ["user_id", "left_at"],
        unique=False,
    )
    op.create_index(
        "ix_message_recipients_conversation_recipient_read_at",
        "message_recipients",
        ["conversation_id", "recipient_user_id", "read_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_message_recipients_conversation_recipient_read_at",
        table_name="message_recipients",
    )
    op.drop_index("ix_conversation_members_user_id_left_at", table_name="conversation_members")
    op.drop_index("ix_messages_conversation_id_server_seq", table_name="messages")
    op.drop_constraint("ux_messages_conversation_server_seq", "messages", type_="unique")
