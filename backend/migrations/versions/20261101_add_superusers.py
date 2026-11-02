# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Add superuser and account status fields.

Revision ID: 20261101_superusers
Revises: 20261031_ai_chat
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261101_superusers"
down_revision = "20261031_ai_chat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("users")}
    if "is_superuser" not in columns:
        op.add_column(
            "users",
            sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "is_active" not in columns:
        op.add_column(
            "users",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    tables = set(inspect(op.get_bind()).get_table_names())
    if "email_send_attempts" not in tables:
        op.create_table(
            "email_send_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("purpose", sa.String(length=32), nullable=False),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_email_send_attempts_user_id", "email_send_attempts", ["user_id"], unique=False)
        op.create_index(
            "idx_email_send_user_purpose_sent",
            "email_send_attempts",
            ["user_id", "purpose", "sent_at"],
            unique=False,
        )


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "email_send_attempts" in tables:
        op.drop_table("email_send_attempts")
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("users")}
    if "is_active" in columns:
        op.drop_column("users", "is_active")
    if "is_superuser" in columns:
        op.drop_column("users", "is_superuser")
