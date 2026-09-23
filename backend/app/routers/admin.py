from datetime import UTC, datetime, timedelta
import hashlib
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..db import get_db
from ..models import Favorite, PlaybackProgress, User, WatchLater
from ..schemas import (
    AdminHistoryItem,
    AdminHistoryListResponse,
    AdminUserInfoResponse,
    FavoriteCreateRequest,
    FavoriteItem,
    FavoriteListResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    WatchLaterCreateRequest,
    WatchLaterItem,
    WatchLaterListResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def extract_host(url: str, fallback_host: str | None = None) -> str | None:
    if fallback_host and fallback_host.strip():
        return fallback_host.strip().lower()
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else None
    except Exception:
        return None


# ----------------------------------------------------------------------
# 1. 认证接口 (Authentication)
# ----------------------------------------------------------------------

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def admin_register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        payload.validate_confirmation()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

    user = User(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists") from None
    return {"message": "Admin user registered successfully"}


@router.post("/auth/login", response_model=TokenResponse)
def admin_login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    now = datetime.now(UTC)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    locked_until = as_utc(user.locked_until)
    if locked_until and locked_until > now:
        retry_after = int((locked_until - now).total_seconds()) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"too many login attempts; retry in {retry_after} seconds",
            headers={"Retry-After": str(retry_after)},
        )
    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1
        delay = min(60, 2 ** max(0, user.failed_login_attempts - 1))
        user.locked_until = now + timedelta(seconds=delay)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"incorrect username or password; retry in {delay} seconds",
            headers={"Retry-After": str(delay), "WWW-Authenticate": "Bearer"},
        )
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id), username=user.username)


@router.get("/auth/me", response_model=AdminUserInfoResponse)
def get_admin_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AdminUserInfoResponse:
    history_count = db.scalar(select(func.count(PlaybackProgress.id)).where(PlaybackProgress.user_id == user.id)) or 0
    favorites_count = db.scalar(select(func.count(Favorite.id)).where(Favorite.user_id == user.id)) or 0
    watch_later_count = db.scalar(select(func.count(WatchLater.id)).where(WatchLater.user_id == user.id)) or 0

    return AdminUserInfoResponse(
        id=user.id,
        username=user.username,
        created_at=as_utc(user.created_at),
        history_count=history_count,
        favorites_count=favorites_count,
        watch_later_count=watch_later_count,
    )


# ----------------------------------------------------------------------
# 2. 历史记录 (History - from PlaybackProgress)
# ----------------------------------------------------------------------

@router.get("/history", response_model=AdminHistoryListResponse)
def list_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    site_host: str | None = Query(default=None, max_length=255),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminHistoryListResponse:
    base_query = select(PlaybackProgress).where(PlaybackProgress.user_id == user.id)
    if site_host and site_host.strip():
        base_query = base_query.where(PlaybackProgress.site_host.ilike(f"%{site_host.strip().lower()}%"))
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        base_query = base_query.where(PlaybackProgress.title.ilike(pattern) | PlaybackProgress.clean_url.ilike(pattern))

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(
        base_query.order_by(PlaybackProgress.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # Determine favorite status for these items
    fav_hashes = set()
    wl_hashes = set()
    if items:
        url_hashes = [i.url_hash for i in items]
        fav_hashes = set(
            db.scalars(
                select(Favorite.url_hash).where(
                    Favorite.user_id == user.id, Favorite.url_hash.in_(url_hashes)
                )
            ).all()
        )
        wl_hashes = set(
            db.scalars(
                select(WatchLater.url_hash).where(
                    WatchLater.user_id == user.id, WatchLater.url_hash.in_(url_hashes)
                )
            ).all()
        )

    return AdminHistoryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            AdminHistoryItem(
                id=item.id,
                site_host=item.site_host,
                clean_url=item.clean_url,
                title=item.title,
                progress_seconds=item.progress_seconds,
                duration=item.duration,
                completed=item.completed,
                updated_at=as_utc(item.updated_at),
                is_favorite=item.url_hash in fav_hashes,
                is_watch_later=item.url_hash in wl_hashes,
            )
            for item in items
        ],
    )


@router.delete("/history/{history_id}", status_code=status.HTTP_200_OK)
def delete_history_item(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    record = db.scalar(select(PlaybackProgress).where(PlaybackProgress.id == history_id, PlaybackProgress.user_id == user.id))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")
    db.delete(record)
    db.commit()
    return {"status": "deleted", "id": str(history_id)}


@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_all_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.query(PlaybackProgress).filter(PlaybackProgress.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return {"status": "cleared"}


# ----------------------------------------------------------------------
# 3. 收藏夹 (Favorites)
# ----------------------------------------------------------------------

@router.get("/favorites", response_model=FavoriteListResponse)
def list_favorites(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteListResponse:
    base_query = select(Favorite).where(Favorite.user_id == user.id)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        base_query = base_query.where(Favorite.title.ilike(pattern) | Favorite.clean_url.ilike(pattern))

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(
        base_query.order_by(Favorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # Determine watch later status for these favorite items
    wl_hashes = set()
    if items:
        url_hashes = [i.url_hash for i in items]
        wl_hashes = set(
            db.scalars(
                select(WatchLater.url_hash).where(
                    WatchLater.user_id == user.id, WatchLater.url_hash.in_(url_hashes)
                )
            ).all()
        )

    return FavoriteListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            FavoriteItem(
                id=item.id,
                site_host=item.site_host,
                clean_url=item.clean_url,
                title=item.title,
                duration=item.duration,
                progress_seconds=item.progress_seconds,
                created_at=as_utc(item.created_at),
                is_watch_later=item.url_hash in wl_hashes,
            )
            for item in items
        ],
    )


@router.post("/favorites", response_model=FavoriteItem, status_code=status.HTTP_200_OK)
def add_favorite(
    payload: FavoriteCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteItem:
    url_hash = compute_url_hash(payload.clean_url)
    site_host = extract_host(payload.clean_url, payload.site_host)

    fav = db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.url_hash == url_hash))
    if fav is None:
        fav = Favorite(
            user_id=user.id,
            url_hash=url_hash,
            site_host=site_host,
            clean_url=payload.clean_url,
            title=payload.title,
            duration=payload.duration,
            progress_seconds=payload.progress_seconds,
        )
        db.add(fav)
    else:
        fav.title = payload.title
        fav.site_host = site_host
        if payload.duration > 0:
            fav.duration = payload.duration
        if payload.progress_seconds > 0:
            fav.progress_seconds = payload.progress_seconds
    db.commit()
    db.refresh(fav)

    return FavoriteItem(
        id=fav.id,
        site_host=fav.site_host,
        clean_url=fav.clean_url,
        title=fav.title,
        duration=fav.duration,
        progress_seconds=fav.progress_seconds,
        created_at=as_utc(fav.created_at),
    )


@router.delete("/favorites/{fav_id}", status_code=status.HTTP_200_OK)
def delete_favorite(
    fav_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    fav = db.scalar(select(Favorite).where(Favorite.id == fav_id, Favorite.user_id == user.id))
    if fav is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"status": "deleted", "id": str(fav_id)}


# ----------------------------------------------------------------------
# 4. 稍后观看 (Watch Later)
# ----------------------------------------------------------------------

@router.get("/watchlater", response_model=WatchLaterListResponse)
def list_watch_later(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchLaterListResponse:
    base_query = select(WatchLater).where(WatchLater.user_id == user.id)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        base_query = base_query.where(WatchLater.title.ilike(pattern) | WatchLater.clean_url.ilike(pattern))

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    items = db.scalars(
        base_query.order_by(WatchLater.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # Determine favorite status for watch later items
    fav_hashes = set()
    if items:
        url_hashes = [i.url_hash for i in items]
        fav_hashes = set(
            db.scalars(
                select(Favorite.url_hash).where(
                    Favorite.user_id == user.id, Favorite.url_hash.in_(url_hashes)
                )
            ).all()
        )

    return WatchLaterListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            WatchLaterItem(
                id=item.id,
                site_host=item.site_host,
                clean_url=item.clean_url,
                title=item.title,
                duration=item.duration,
                progress_seconds=item.progress_seconds,
                created_at=as_utc(item.created_at),
                is_favorite=item.url_hash in fav_hashes,
            )
            for item in items
        ],
    )


@router.post("/watchlater", response_model=WatchLaterItem, status_code=status.HTTP_200_OK)
def add_watch_later(
    payload: WatchLaterCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchLaterItem:
    url_hash = compute_url_hash(payload.clean_url)
    site_host = extract_host(payload.clean_url, payload.site_host)

    wl = db.scalar(select(WatchLater).where(WatchLater.user_id == user.id, WatchLater.url_hash == url_hash))
    if wl is None:
        wl = WatchLater(
            user_id=user.id,
            url_hash=url_hash,
            site_host=site_host,
            clean_url=payload.clean_url,
            title=payload.title,
            duration=payload.duration,
            progress_seconds=payload.progress_seconds,
        )
        db.add(wl)
    else:
        wl.title = payload.title
        wl.site_host = site_host
        if payload.duration > 0:
            wl.duration = payload.duration
        if payload.progress_seconds > 0:
            wl.progress_seconds = payload.progress_seconds
    db.commit()
    db.refresh(wl)

    is_fav = db.scalar(select(Favorite.id).where(Favorite.user_id == user.id, Favorite.url_hash == url_hash)) is not None

    return WatchLaterItem(
        id=wl.id,
        site_host=wl.site_host,
        clean_url=wl.clean_url,
        title=wl.title,
        duration=wl.duration,
        progress_seconds=wl.progress_seconds,
        created_at=as_utc(wl.created_at),
        is_favorite=is_fav,
    )


@router.delete("/watchlater/{wl_id}", status_code=status.HTTP_200_OK)
def delete_watch_later(
    wl_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    wl = db.scalar(select(WatchLater).where(WatchLater.id == wl_id, WatchLater.user_id == user.id))
    if wl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch later record not found")
    db.delete(wl)
    db.commit()
    return {"status": "deleted", "id": str(wl_id)}
