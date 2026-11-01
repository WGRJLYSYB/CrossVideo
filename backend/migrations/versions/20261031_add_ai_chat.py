# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Persist per-user AI conversations and monthly token usage.

Revision ID: 20261031_ai_chat
Revises: 20261031_account_security
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261031_ai_chat"
down_revision = "20261031_account_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "ai_conversations" not in tables:
        op.create_table(
            "ai_conversations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("messages", sa.JSON(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"], unique=False)
        op.create_index("idx_ai_conversation_user", "ai_conversations", ["user_id"], unique=True)
    if "ai_monthly_usage" not in tables:
        op.create_table(
            "ai_monthly_usage",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("month", sa.String(length=7), nullable=False),
            sa.Column("used_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reserved_tokens", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_ai_monthly_usage_user_id", "ai_monthly_usage", ["user_id"], unique=False)
        op.create_index("idx_ai_usage_user_month", "ai_monthly_usage", ["user_id", "month"], unique=True)


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "ai_monthly_usage" in tables:
        op.drop_table("ai_monthly_usage")
    if "ai_conversations" in tables:
        op.drop_table("ai_conversations")
