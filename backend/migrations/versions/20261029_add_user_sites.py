# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Track sites users watch videos on.

Revision ID: 20261029_user_sites
Revises: 20260922_add_favorite_and_watchlater
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261029_user_sites"
down_revision = "20260922_add_favorite_and_watchlater"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "user_sites" in inspect(op.get_bind()).get_table_names():
        return

    op.create_table(
        "user_sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("site_host", sa.String(length=255), nullable=False),
        sa.Column("site_name", sa.String(length=255), nullable=False),
        sa.Column("last_watched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("watched_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_sites_user_id", "user_sites", ["user_id"], unique=False)
    op.create_index("ix_user_sites_last_watched_at", "user_sites", ["last_watched_at"], unique=False)
    op.create_index("idx_user_site_host", "user_sites", ["user_id", "site_host"], unique=True)

    op.execute(sa.text("""
        INSERT INTO user_sites (user_id, site_host, site_name, last_watched_at, watched_seconds)
        SELECT user_id, lower(site_host), lower(site_host), max(updated_at), 0
        FROM playback_progress
        WHERE site_host IS NOT NULL AND site_host <> ''
        GROUP BY user_id, lower(site_host)
    """))


def downgrade() -> None:
    op.drop_table("user_sites")
