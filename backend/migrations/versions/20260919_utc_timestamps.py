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