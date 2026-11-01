# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Track whether a site's homepage title has been checked.

Revision ID: 20261030_site_title_check
Revises: 20261029_user_sites
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261030_site_title_check"
down_revision = "20261029_user_sites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("user_sites")}
    if "title_fetch_attempted" not in columns:
        op.add_column(
            "user_sites",
            sa.Column("title_fetch_attempted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("user_sites")}
    if "title_fetch_attempted" in columns:
        op.drop_column("user_sites", "title_fetch_attempted")
