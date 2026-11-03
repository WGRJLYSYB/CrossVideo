# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Add normalized media episode progress.

Revision ID: 20261102_media_progress
Revises: 20261101_superusers
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261102_media_progress"
down_revision = "20261101_superusers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "media_progress" not in tables:
        op.create_table(
            "media_progress",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=1000), nullable=False),
            sa.Column("title_key", sa.String(length=64), nullable=False),
            sa.Column("season", sa.Integer(), nullable=False),
            sa.Column("episode", sa.Integer(), nullable=False),
            sa.Column("last_url_hash", sa.String(length=64), nullable=False),
            sa.Column("progress_seconds", sa.Float(), nullable=False),
            sa.Column("duration", sa.Float(), nullable=False),
            sa.Column("completed", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("client_updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_media_progress_user_id", "media_progress", ["user_id"], unique=False)
        op.create_index(
            "idx_media_user_title_season_episode",
            "media_progress",
            ["user_id", "title_key", "season", "episode"],
            unique=True,
        )

    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("playback_progress")}
    if "media_progress_id" not in columns:
        with op.batch_alter_table("playback_progress") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "media_progress_id",
                    sa.Integer(),
                    sa.ForeignKey(
                        "media_progress.id",
                        ondelete="SET NULL",
                        name="fk_playback_progress_media_progress_id",
                    ),
                    nullable=True,
                )
            )
            batch_op.create_index(
                "ix_playback_progress_media_progress_id",
                ["media_progress_id"],
                unique=False,
            )


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("playback_progress")}
    if "media_progress_id" in columns:
        with op.batch_alter_table("playback_progress") as batch_op:
            batch_op.drop_index("ix_playback_progress_media_progress_id")
            batch_op.drop_column("media_progress_id")
    tables = set(inspect(op.get_bind()).get_table_names())
    if "media_progress" in tables:
        op.drop_table("media_progress")
