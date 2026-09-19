from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import BlockedSite, PlaybackProgress, User
from ..schemas import ProgressItem, ProgressListResponse, ProgressQueryResponse, ProgressSyncRequest, SiteRequest

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


def as_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value.astimezone(UTC) if value is not None else None
    return value.replace(tzinfo=UTC)


@router.post("/sync")
def sync_progress(payload: ProgressSyncRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == payload.site_host.lower())) is not None:
        return {"status": "ignored", "message": "site is blocked"}
    progress_seconds = min(payload.progress_seconds, payload.duration)
    completed = progress_seconds / payload.duration >= 0.95
    incoming_time = as_utc(payload.client_updated_at) or datetime.now(UTC)
    existing = db.scalar(select(PlaybackProgress).where(PlaybackProgress.user_id == user.id, PlaybackProgress.url_hash == payload.url_hash))

    if existing is None:
        existing = PlaybackProgress(user_id=user.id, url_hash=payload.url_hash, site_host=payload.site_host.lower(), clean_url=payload.clean_url, title=payload.title, progress_seconds=0 if completed else progress_seconds, duration=payload.duration, completed=completed, client_updated_at=incoming_time)
        db.add(existing)
    else:
        stored_time = as_utc(existing.client_updated_at)
        should_update = stored_time is None or incoming_time >= stored_time or progress_seconds > existing.progress_seconds
        if should_update:
            existing.clean_url = payload.clean_url
            existing.site_host = payload.site_host.lower()
            existing.title = payload.title
            existing.progress_seconds = 0 if completed else progress_seconds
            existing.duration = payload.duration
            existing.completed = completed
            existing.client_updated_at = incoming_time

    db.commit()
    return {"status": "success", "message": "Progress updated"}


@router.get("/query", response_model=ProgressQueryResponse)
def query_progress(url_hash: str = Query(min_length=64, max_length=64, pattern=r"^[a-fA-F0-9]{64}$"), site_host: str | None = Query(default=None, max_length=255), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProgressQueryResponse:
    if site_host and db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == site_host.lower())) is not None:
        return ProgressQueryResponse(found=False)
    progress = db.scalar(select(PlaybackProgress).where(PlaybackProgress.user_id == user.id, PlaybackProgress.url_hash == url_hash))
    if progress is None or progress.completed:
        return ProgressQueryResponse(found=False)
    return ProgressQueryResponse(found=True, progress_seconds=progress.progress_seconds, duration=progress.duration, updated_at=as_utc(progress.updated_at))


@router.get("/list", response_model=ProgressListResponse)
def list_progress(search: str | None = Query(default=None, max_length=200), site_host: str | None = Query(default=None, max_length=255), page: int = Query(default=1, ge=1), page_size: int = Query(default=10, ge=1, le=100), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProgressListResponse:
    base_query = select(PlaybackProgress).where(PlaybackProgress.user_id == user.id)
    if site_host and site_host.strip():
        base_query = base_query.where(PlaybackProgress.site_host == site_host.strip().lower())
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        base_query = base_query.where(PlaybackProgress.title.ilike(search_pattern) | PlaybackProgress.clean_url.ilike(search_pattern))
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(base_query.order_by(PlaybackProgress.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return ProgressListResponse(total=total, page=page, page_size=page_size, items=[ProgressItem(id=item.id, clean_url=item.clean_url, title=item.title, progress_seconds=0 if item.completed else item.progress_seconds, duration=item.duration, updated_at=as_utc(item.updated_at)) for item in items])


@router.delete("/records/{progress_id}")
def delete_progress(progress_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    progress = db.scalar(select(PlaybackProgress).where(PlaybackProgress.id == progress_id, PlaybackProgress.user_id == user.id))
    if progress is None:
        return {"status": "not_found"}
    db.delete(progress)
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
        db.query(PlaybackProgress).filter(PlaybackProgress.user_id == user.id, PlaybackProgress.site_host == host).delete(synchronize_session=False)
        db.commit()
    return {"status": "blocked", "site_host": host}


@router.delete("/blocked-sites/{site_host}")
def unblock_site(site_host: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    blocked = db.scalar(select(BlockedSite).where(BlockedSite.user_id == user.id, BlockedSite.site_host == site_host.lower()))
    if blocked:
        db.delete(blocked)
        db.commit()
    return {"status": "unblocked", "site_host": site_host.lower()}
