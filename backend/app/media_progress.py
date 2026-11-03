from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from .media import ParsedMedia
from .models import MediaProgress, PlaybackProgress


def save_media_progress(
    db: Session,
    *,
    user_id: int,
    media: ParsedMedia,
    url_hash: str,
    progress_seconds: float,
    duration: float,
    completed: bool,
    client_updated_at: datetime | None,
) -> MediaProgress:
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    statement = insert(MediaProgress).values(
        user_id=user_id,
        title=media.title,
        title_key=media.title_key,
        season=media.season,
        episode=media.episode,
        last_url_hash=url_hash,
        progress_seconds=progress_seconds,
        duration=duration,
        completed=completed,
        client_updated_at=client_updated_at,
        updated_at=datetime.now(UTC),
    )
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[
            MediaProgress.user_id,
            MediaProgress.title_key,
            MediaProgress.season,
            MediaProgress.episode,
        ],
        set_={
            "title": excluded.title,
            "last_url_hash": excluded.last_url_hash,
            "progress_seconds": excluded.progress_seconds,
            "duration": excluded.duration,
            "completed": excluded.completed,
            "client_updated_at": excluded.client_updated_at,
            "updated_at": excluded.updated_at,
        },
        where=(
            MediaProgress.client_updated_at.is_(None)
            | (excluded.client_updated_at >= MediaProgress.client_updated_at)
            | (excluded.progress_seconds > MediaProgress.progress_seconds)
        ),
    )
    db.execute(statement)
    saved = db.scalar(
        select(MediaProgress).where(
            MediaProgress.user_id == user_id,
            MediaProgress.title_key == media.title_key,
            MediaProgress.season == media.season,
            MediaProgress.episode == media.episode,
        )
    )
    if saved is None:
        raise RuntimeError("The media progress upsert did not persist a record")
    return saved


def refresh_media_progress(db: Session, media_progress_ids: set[int]) -> None:
    for media_progress_id in media_progress_ids:
        media = db.get(MediaProgress, media_progress_id)
        if media is None:
            continue
        latest = db.scalar(
            select(PlaybackProgress)
            .where(PlaybackProgress.media_progress_id == media_progress_id)
            .order_by(PlaybackProgress.updated_at.desc(), PlaybackProgress.id.desc())
            .limit(1)
        )
        if latest is None:
            db.delete(media)
            continue
        media.last_url_hash = latest.url_hash
        media.progress_seconds = latest.progress_seconds
        media.duration = latest.duration
        media.completed = latest.completed
        media.client_updated_at = latest.client_updated_at
        media.updated_at = latest.updated_at
