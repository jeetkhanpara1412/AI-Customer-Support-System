"""Persist conversation topic and pending clarification options."""

import sqlalchemy as sa

from alembic import op

revision = "0002_conversation_memory"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations", sa.Column("current_topic", sa.String(64), nullable=True)
    )
    op.add_column(
        "conversations", sa.Column("pending_clarification", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("conversations", "pending_clarification")
    op.drop_column("conversations", "current_topic")
