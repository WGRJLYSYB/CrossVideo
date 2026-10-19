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

"""Normalize existing timestamp columns to UTC-aware PostgreSQL timestamps.

Revision ID: 20260919_utc_timestamps
Revises: 20260918_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_utc_timestamps"
down_revision = "20260918_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table, columns in {
        "users": ["created_at", "updated_at", "locked_until"],
        "playback_progress": ["created_at", "updated_at", "client_updated_at"],
        "blocked_sites": ["created_at"],
    }.items():
        for column in columns:
            op.execute(sa.text(f"""
                ALTER TABLE {table}
                ALTER COLUMN {column} TYPE TIMESTAMP WITH TIME ZONE
                USING {column} AT TIME ZONE 'Asia/Shanghai'
            """))


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table, columns in {
        "users": ["created_at", "updated_at", "locked_until"],
        "playback_progress": ["created_at", "updated_at", "client_updated_at"],
        "blocked_sites": ["created_at"],
    }.items():
        for column in columns:
            op.execute(sa.text(f"""
                ALTER TABLE {table}
                ALTER COLUMN {column} TYPE TIMESTAMP
                USING {column} AT TIME ZONE 'UTC'
            """))