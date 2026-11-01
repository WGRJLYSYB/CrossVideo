# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Add captcha, email verification, and TOTP account security.

Revision ID: 20261031_account_security
Revises: 20261030_site_title_check
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261031_account_security"
down_revision = "20261030_site_title_check"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "email" not in user_columns:
        op.add_column("users", sa.Column("email", sa.String(length=320), nullable=True))
    if "email_verified" not in user_columns:
        op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "totp_enabled" not in user_columns:
        op.add_column("users", sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "totp_secret" not in user_columns:
        op.add_column("users", sa.Column("totp_secret", sa.String(length=255), nullable=True))

    user_indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_email" not in user_indexes:
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    tables = set(inspector.get_table_names())
    if "captcha_challenges" not in tables:
        op.create_table(
            "captcha_challenges",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("target_points", sa.JSON(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "email_action_tokens" not in tables:
        op.create_table(
            "email_action_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("purpose", sa.String(length=32), nullable=False),
            sa.Column("target_email", sa.String(length=320), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_email_action_tokens_user_id", "email_action_tokens", ["user_id"], unique=False)
        op.create_index("ix_email_action_tokens_token_hash", "email_action_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "email_action_tokens" in tables:
        op.drop_table("email_action_tokens")
    if "captcha_challenges" in tables:
        op.drop_table("captcha_challenges")
    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    user_indexes = {index["name"] for index in inspect(bind).get_indexes("users")}
    if "ix_users_email" in user_indexes:
        op.drop_index("ix_users_email", table_name="users")
    for column in ("totp_secret", "totp_enabled", "email_verified", "email"):
        if column in user_columns:
            op.drop_column("users", column)
