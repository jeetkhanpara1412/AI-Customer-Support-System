"""Create support system tables."""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64)),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column(
            "failed_login_attempts", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "title", sa.String(160), nullable=False, server_default="New conversation"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id"),
            nullable=False,
        ),
        sa.Column("sender", sa.String(16), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64)),
        sa.Column("confidence", sa.Float()),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "subject", sa.String(160), nullable=False, server_default="Support request"
        ),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tickets_user_id", "tickets", ["user_id"])
    op.create_index("ix_tickets_category", "tickets", ["category"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_table(
        "ticket_replies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False
        ),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ticket_replies_ticket_id", "ticket_replies", ["ticket_id"])
    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_entries_category", "knowledge_entries", ["category"])


def downgrade() -> None:
    op.drop_table("knowledge_entries")
    op.drop_table("ticket_replies")
    op.drop_table("tickets")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
