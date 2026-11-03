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

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..media import parse_media_title
from ..media_progress import refresh_media_progress, save_media_progress
from ..models import BlockedSite, MediaProgress, PlaybackProgress, User, UserSite
from ..schemas import MediaProgressItem, MediaProgressListResponse, ProgressItem, ProgressListResponse, ProgressQueryResponse, ProgressSyncRequest, SiteRequest
from ..site_tasks import fetch_and_save_site_title

router = APIRouter(prefix="/progress", tags=["progress"])

SITE_NAMES = {
    "bilibili.com": "哔哩哔哩",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "v.qq.com": "腾讯视频",
    "iqiyi.com": "爱奇艺",
    "youku.com": "优酷",
    "mgtv.com": "芒果TV",
    "ixigua.com": "西瓜视频",
    "douyin.com": "抖音",
    "netflix.com": "Netflix",
}


def as_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value.astimezone(UTC) if value is not None else None
    return value.replace(tzinfo=UTC)


@router.post("/sync")
def sync_progress(payload: ProgressSyncRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == payload.site_host.lower())) is not None:
        return {"status": "ignored", "message": "site is blocked"}
    progress_seconds = min(payload.progress_seconds, payload.duration)
    completed = progress_seconds / payload.duration >= 0.95
    incoming_time = as_utc(payload.client_updated_at) or datetime.now(UTC)
    observed_at = datetime.now(UTC)
    url_hash = payload.url_hash.lower()
    existing = db.scalar(select(PlaybackProgress).where(PlaybackProgress.user_id == user.id, PlaybackProgress.url_hash == url_hash))
    host = payload.site_host.lower()
    parsed_media = parse_media_title(payload.title)
    media_progress_id = existing.media_progress_id if existing is not None else None

    if existing is None:
        existing = PlaybackProgress(user_id=user.id, url_hash=url_hash, site_host=host, clean_url=payload.clean_url, title=payload.title, progress_seconds=0 if completed else progress_seconds, duration=payload.duration, completed=completed, client_updated_at=incoming_time)
        db.add(existing)
        watched_delta = min(progress_seconds, 30.0)
        accepted_update = True
    else:
        stored_time = as_utc(existing.client_updated_at)
        should_update = stored_time is None or incoming_time >= stored_time or progress_seconds > existing.progress_seconds
        if should_update:
            watched_delta = min(max(0.0, progress_seconds - existing.progress_seconds), 30.0)
            existing.clean_url = payload.clean_url
            existing.site_host = host
            existing.title = payload.title
            existing.progress_seconds = 0 if completed else progress_seconds
            existing.duration = payload.duration
            existing.completed = completed
            existing.client_updated_at = incoming_time
            accepted_update = True
        else:
            watched_delta = 0.0
            accepted_update = False

    if parsed_media is not None:
        media_state = existing
        if accepted_update:
            media_seconds = 0 if completed else progress_seconds
            media_duration = payload.duration
            media_completed = completed
            media_client_updated_at = incoming_time
        else:
            media_seconds = media_state.progress_seconds
            media_duration = media_state.duration
            media_completed = media_state.completed
            media_client_updated_at = as_utc(media_state.client_updated_at)
        media = save_media_progress(
            db,
            user_id=user.id,
            media=parsed_media,
            url_hash=url_hash,
            progress_seconds=media_seconds,
            duration=media_duration,
            completed=media_completed,
            client_updated_at=media_client_updated_at,
        )
        existing.media_progress_id = media.id
        if media_progress_id is not None and media_progress_id != media.id:
            db.flush()
            refresh_media_progress(db, {media_progress_id})
    elif existing.media_progress_id is not None:
        media_progress_id = existing.media_progress_id
        existing.media_progress_id = None
        db.flush()
        refresh_media_progress(db, {media_progress_id})

    site_name = next((name for domain, name in SITE_NAMES.items() if host == domain or host.endswith(f".{domain}")), host)
    insert_site = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    site_insert = insert_site(UserSite).values(
        user_id=user.id,
        site_host=host,
        site_name=site_name,
        last_watched_at=observed_at,
        watched_seconds=watched_delta,
    )
    db.execute(site_insert.on_conflict_do_update(
        index_elements=[UserSite.user_id, UserSite.site_host],
        set_={
            "last_watched_at": case(
                (UserSite.last_watched_at < observed_at, observed_at),
                else_=UserSite.last_watched_at,
            ),
            "watched_seconds": UserSite.watched_seconds + watched_delta,
        },
    ))

    db.commit()
    site = db.scalar(select(UserSite).where(UserSite.user_id == user.id, UserSite.site_host == host))
    if site is not None and not site.title_fetch_attempted:
        background_tasks.add_task(fetch_and_save_site_title, site.id)
    return {"status": "success", "message": "Progress updated"}


@router.get("/query", response_model=ProgressQueryResponse, response_model_exclude_unset=True)
def query_progress(url_hash: str = Query(min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$"), site_host: str | None = Query(default=None, max_length=255), title: str | None = Query(default=None, max_length=1000), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProgressQueryResponse:
    if site_host and db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == site_host.lower())) is not None:
        return ProgressQueryResponse(found=False, progress_seconds=None, duration=None, updated_at=None)
    parsed_media = parse_media_title(title) if title else None
    if parsed_media is not None:
        media = db.scalar(
            select(MediaProgress).where(
                MediaProgress.user_id == user.id,
                MediaProgress.title_key == parsed_media.title_key,
                MediaProgress.season == parsed_media.season,
                MediaProgress.episode == parsed_media.episode,
            )
        )
        if media is not None and media.last_url_hash.lower() != url_hash.lower():
            if media.completed:
                return ProgressQueryResponse(found=False, progress_seconds=None, duration=None, updated_at=None)
            return ProgressQueryResponse(
                found=True,
                progress_seconds=media.progress_seconds,
                duration=media.duration,
                updated_at=as_utc(media.updated_at),
                cross_site=True,
            )
    progress = db.scalar(select(PlaybackProgress).where(PlaybackProgress.user_id == user.id, PlaybackProgress.url_hash == url_hash.lower()))
    if progress is None or progress.completed:
        return ProgressQueryResponse(found=False, progress_seconds=None, duration=None, updated_at=None)
    return ProgressQueryResponse(found=True, progress_seconds=progress.progress_seconds, duration=progress.duration, updated_at=as_utc(progress.updated_at), cross_site=False)


@router.get("/media-list", response_model=MediaProgressListResponse)
def list_media_progress(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MediaProgressListResponse:
    base_query = select(MediaProgress).where(MediaProgress.user_id == user.id)
    if search and search.strip():
        base_query = base_query.where(MediaProgress.title.ilike(f"%{search.strip()}%"))
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(
        base_query.order_by(MediaProgress.updated_at.desc(), MediaProgress.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return MediaProgressListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            MediaProgressItem(
                id=item.id,
                title=item.title,
                season=item.season,
                episode=item.episode,
                progress_seconds=item.progress_seconds,
                duration=item.duration,
                updated_at=as_utc(item.updated_at),
                completed=item.completed,
            )
            for item in items
        ],
    )


@router.get("/list", response_model=ProgressListResponse)
def list_progress(search: str | None = Query(default=None, max_length=200), site_host: str | None = Query(default=None, max_length=255), page: int = Query(default=1, ge=1), page_size: int = Query(default=10, ge=1, le=100), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProgressListResponse:
    base_query = select(PlaybackProgress).where(PlaybackProgress.user_id == user.id)
    if site_host and site_host.strip():
        base_query = base_query.where(PlaybackProgress.site_host.ilike(f"%{site_host.strip().lower()}%"))
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        base_query = base_query.where(PlaybackProgress.title.ilike(search_pattern) | PlaybackProgress.clean_url.ilike(search_pattern))
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(base_query.order_by(PlaybackProgress.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return ProgressListResponse(total=total, page=page, page_size=page_size, items=[ProgressItem(id=item.id, clean_url=item.clean_url, title=item.title, progress_seconds=0 if item.completed else item.progress_seconds, duration=item.duration, updated_at=as_utc(item.updated_at), completed=item.completed) for item in items])


@router.delete("/records/{progress_id}")
def delete_progress(progress_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    progress = db.scalar(select(PlaybackProgress).where(PlaybackProgress.id == progress_id, PlaybackProgress.user_id == user.id))
    if progress is None:
        return {"status": "not_found"}
    media_progress_id = progress.media_progress_id
    db.delete(progress)
    db.flush()
    if media_progress_id is not None:
        refresh_media_progress(db, {media_progress_id})
    db.commit()
    return {"status": "deleted"}


@router.get("/blocked-sites")
def list_blocked_sites(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, list[str]]:
    return {"items": list(db.scalars(select(BlockedSite.site_host).where(BlockedSite.user_id == user.id).order_by(BlockedSite.site_host)))}


@router.post("/blocked-sites")
def block_site(payload: SiteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    host = payload.site_host.lower()
    if db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == host)) is None:
        db.add(BlockedSite(user_id=user.id, site_host=host))
        removed = db.scalars(
            select(PlaybackProgress).where(PlaybackProgress.user_id == user.id, PlaybackProgress.site_host == host)
        ).all()
        media_progress_ids = {item.media_progress_id for item in removed if item.media_progress_id is not None}
        db.query(PlaybackProgress).filter(PlaybackProgress.user_id == user.id, PlaybackProgress.site_host == host).delete(synchronize_session=False)
        refresh_media_progress(db, media_progress_ids)
        db.commit()
    return {"status": "blocked", "site_host": host}


@router.delete("/blocked-sites/{site_host}")
def unblock_site(site_host: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    blocked = db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == site_host.lower()))
    if blocked:
        db.delete(blocked)
        db.commit()
    return {"status": "unblocked", "site_host": site_host.lower()}
