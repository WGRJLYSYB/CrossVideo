# CrossVideo — Cross‑platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Create the initial CrossVideo schema.

Revision ID: 20260918_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260918_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure the alembic_version table's version_num column can accommodate longer version strings
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);")
    
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("username"),
        )
        op.create_index("ix_users_username", "users", ["username"], unique=False)

    if "playback_progress" not in tables:
        op.create_table(
            "playback_progress",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("site_host", sa.String(length=255), nullable=True),
            sa.Column("url_hash", sa.String(length=64), nullable=False),
            sa.Column("clean_url", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("progress_seconds", sa.Float(), nullable=False),
            sa.Column("duration", sa.Float(), nullable=False),
            sa.Column("completed", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("client_updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_playback_progress_user_id", "playback_progress", ["user_id"], unique=False)
        op.create_index("ix_playback_progress_site_host", "playback_progress", ["site_host"], unique=False)
        op.create_index("idx_user_url", "playback_progress", ["user_id", "url_hash"], unique=True)

    if "blocked_sites" not in tables:
        op.create_table(
            "blocked_sites",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("site_host", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_blocked_sites_user_id", "blocked_sites", ["user_id"], unique=False)
        op.create_index("idx_user_site", "blocked_sites", ["user_id", "site_host"], unique=True)


def downgrade() -> None:
    op.drop_table("blocked_sites")
    op.drop_table("playback_progress")
    op.drop_table("users")
