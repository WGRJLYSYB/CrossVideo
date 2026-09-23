"""Add favorites and watch_later tables.

Revision ID: 20260922_add_favorite_and_watchlater
Revises: 20260919_utc_timestamps
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260922_add_favorite_and_watchlater"
down_revision = "20260919_utc_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "favorites" not in tables:
        op.create_table(
            "favorites",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("site_host", sa.String(length=255), nullable=True),
            sa.Column("url_hash", sa.String(length=64), nullable=False),
            sa.Column("clean_url", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("duration", sa.Float(), nullable=False, server_default="0"),
            sa.Column("progress_seconds", sa.Float(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_favorites_user_id", "favorites", ["user_id"], unique=False)
        op.create_index("ix_favorites_site_host", "favorites", ["site_host"], unique=False)
        op.create_index("idx_fav_user_url", "favorites", ["user_id", "url_hash"], unique=True)

    if "watch_later" not in tables:
        op.create_table(
            "watch_later",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("site_host", sa.String(length=255), nullable=True),
            sa.Column("url_hash", sa.String(length=64), nullable=False),
            sa.Column("clean_url", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("duration", sa.Float(), nullable=False, server_default="0"),
            sa.Column("progress_seconds", sa.Float(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_watch_later_user_id", "watch_later", ["user_id"], unique=False)
        op.create_index("ix_watch_later_site_host", "watch_later", ["site_host"], unique=False)
        op.create_index("idx_wl_user_url", "watch_later", ["user_id", "url_hash"], unique=True)


def downgrade() -> None:
    op.drop_table("watch_later")
    op.drop_table("favorites")
