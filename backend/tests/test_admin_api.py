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

import os
from datetime import UTC, datetime

os.environ["CROSSVIDEO_DATABASE_URL"] = "sqlite:///./data/test-crossvideo.db"
os.environ["CROSSVIDEO_SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def admin_auth_headers(username: str = "admin_user") -> dict[str, str]:
    client.post(
        "/api/v1/admin/auth/register",
        json={"username": username, "password": "Password123", "confirm_password": "Password123"},
    )
    res = client.post("/api/v1/admin/auth/login", json={"username": username, "password": "Password123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_auth_register_and_login():
    reg = client.post(
        "/api/v1/admin/auth/register",
        json={"username": "superadmin", "password": "Password123", "confirm_password": "Password123"},
    )
    assert reg.status_code == 201

    # Duplicate registration should return 409
    dup = client.post(
        "/api/v1/admin/auth/register",
        json={"username": "superadmin", "password": "Password123", "confirm_password": "Password123"},
    )
    assert dup.status_code == 409

    # Successful login
    login_res = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "superadmin", "password": "Password123"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["username"] == "superadmin"

    # Profile /me
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = client.get("/api/v1/admin/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "superadmin"
    assert me_data["history_count"] == 0
    assert me_data["favorites_count"] == 0
    assert me_data["watch_later_count"] == 0


def test_admin_history_pagination_search_and_delete():
    headers = admin_auth_headers("history_user")

    # Add playback progress data directly via userscript sync endpoint to simulate history
    for i in range(15):
        url_hash = f"{i:02d}" + "a" * 62
        client.post(
            "/api/v1/progress/sync",
            headers=headers,
            json={
                "url_hash": url_hash,
                "clean_url": f"https://bilibili.com/video/BV{i}",
                "title": f"Video Title {i} {'Python' if i % 2 == 0 else 'Vue'}",
                "progress_seconds": 100 + i,
                "duration": 500,
                "site_host": "bilibili.com",
            },
        )

    # Test pagination (page 1, size 10)
    res = client.get("/api/v1/admin/history?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 15
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 10

    # Test page 2
    res2 = client.get("/api/v1/admin/history?page=2&page_size=10", headers=headers)
    assert res2.status_code == 200
    assert len(res2.json()["items"]) == 5

    # Test search filter
    search_res = client.get("/api/v1/admin/history?search=Python", headers=headers)
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 8

    # Test single delete
    item_id = body["items"][0]["id"]
    del_res = client.delete(f"/api/v1/admin/history/{item_id}", headers=headers)
    assert del_res.status_code == 200

    check_res = client.get("/api/v1/admin/history", headers=headers)
    assert check_res.json()["total"] == 14


def test_admin_favorites_crud():
    headers = admin_auth_headers("fav_user")

    # Add favorite
    fav_payload = {
        "clean_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Never Gonna Give You Up",
        "site_host": "youtube.com",
        "duration": 213,
        "progress_seconds": 45,
    }
    create_res = client.post("/api/v1/admin/favorites", headers=headers, json=fav_payload)
    assert create_res.status_code == 200
    fav_item = create_res.json()
    assert fav_item["title"] == "Never Gonna Give You Up"
    assert fav_item["site_host"] == "youtube.com"

    # List favorites
    list_res = client.get("/api/v1/admin/favorites?page=1&page_size=10", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["id"] == fav_item["id"]

    # Delete favorite
    del_res = client.delete(f"/api/v1/admin/favorites/{fav_item['id']}", headers=headers)
    assert del_res.status_code == 200

    after_del = client.get("/api/v1/admin/favorites", headers=headers)
    assert after_del.json()["total"] == 0


def test_admin_watch_later_crud_and_favorite_status():
    headers = admin_auth_headers("wl_user")

    # Add watch later
    wl_payload = {
        "clean_url": "https://www.bilibili.com/video/BV1xx411c7mD",
        "title": "Learn FastAPI & Vue 3",
        "site_host": "bilibili.com",
        "duration": 1800,
        "progress_seconds": 120,
    }
    create_res = client.post("/api/v1/admin/watchlater", headers=headers, json=wl_payload)
    assert create_res.status_code == 200
    wl_item = create_res.json()
    assert wl_item["title"] == "Learn FastAPI & Vue 3"
    assert wl_item["is_favorite"] is False

    # Also add it to favorites
    client.post(
        "/api/v1/admin/favorites",
        headers=headers,
        json={
            "clean_url": wl_payload["clean_url"],
            "title": wl_payload["title"],
            "site_host": wl_payload["site_host"],
            "duration": wl_payload["duration"],
            "progress_seconds": wl_payload["progress_seconds"],
        },
    )

    # Now query watch later again, is_favorite should be True
    list_res = client.get("/api/v1/admin/watchlater", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["is_favorite"] is True

    # Delete watch later
    del_res = client.delete(f"/api/v1/admin/watchlater/{wl_item['id']}", headers=headers)
    assert del_res.status_code == 200
    assert client.get("/api/v1/admin/watchlater", headers=headers).json()["total"] == 0


def test_bulk_delete_is_limited_and_scoped_to_current_user():
    owner_headers = admin_auth_headers("bulk_owner")
    other_headers = admin_auth_headers("bulk_other")
    owner_items = [
        client.post(
            "/api/v1/admin/favorites",
            headers=owner_headers,
            json={"clean_url": f"https://example.com/{i}", "title": f"Favorite {i}"},
        ).json()
        for i in range(2)
    ]
    other_item = client.post(
        "/api/v1/admin/favorites",
        headers=other_headers,
        json={"clean_url": "https://other.example/video", "title": "Other user's favorite"},
    ).json()

    deleted = client.post(
        "/api/v1/admin/favorites/bulk-delete",
        headers=owner_headers,
        json={"ids": [owner_items[0]["id"], other_item["id"], owner_items[0]["id"]]},
    )
    assert deleted.status_code == 200
    assert deleted.json()["deleted_count"] == 1
    assert client.get("/api/v1/admin/favorites", headers=owner_headers).json()["total"] == 1
    assert client.get("/api/v1/admin/favorites", headers=other_headers).json()["total"] == 1
    too_many = client.post(
        "/api/v1/admin/favorites/bulk-delete",
        headers=owner_headers,
        json={"ids": list(range(1, 52))},
    )
    assert too_many.status_code == 422


def test_bulk_delete_history_and_watchlater():
    owner_headers = admin_auth_headers("bulk_lists_owner")
    other_headers = admin_auth_headers("bulk_lists_other")
    history_id = client.post(
        "/api/v1/progress/sync",
        headers=owner_headers,
        json={
            "url_hash": "1" * 64,
            "clean_url": "https://example.com/history",
            "title": "History record",
            "progress_seconds": 10,
            "duration": 120,
            "site_host": "example.com",
        },
    )
    assert history_id.status_code == 200
    own_history = client.get("/api/v1/admin/history", headers=owner_headers).json()["items"][0]["id"]
    other_history_payload = {
        "url_hash": "2" * 64,
        "clean_url": "https://other.example/history",
        "title": "Other user's history",
        "progress_seconds": 10,
        "duration": 120,
        "site_host": "other.example",
    }
    client.post("/api/v1/progress/sync", headers=other_headers, json=other_history_payload)
    other_history = client.get("/api/v1/admin/history", headers=other_headers).json()["items"][0]["id"]

    deleted_history = client.post(
        "/api/v1/admin/history/bulk-delete",
        headers=owner_headers,
        json={"ids": [own_history, other_history]},
    )
    assert deleted_history.json()["deleted_count"] == 1
    assert client.get("/api/v1/admin/history", headers=other_headers).json()["total"] == 1

    own_later = client.post(
        "/api/v1/admin/watchlater",
        headers=owner_headers,
        json={"clean_url": "https://example.com/later", "title": "Later"},
    ).json()["id"]
    other_later = client.post(
        "/api/v1/admin/watchlater",
        headers=other_headers,
        json={"clean_url": "https://other.example/later", "title": "Other later"},
    ).json()["id"]
    deleted_later = client.post(
        "/api/v1/admin/watchlater/bulk-delete",
        headers=owner_headers,
        json={"ids": [own_later, other_later]},
    )
    assert deleted_later.json()["deleted_count"] == 1
    assert client.get("/api/v1/admin/watchlater", headers=other_headers).json()["total"] == 1


def test_platforms_are_recorded_and_blocklist_accepts_url():
    headers = admin_auth_headers("site_user")
    sync = client.post(
        "/api/v1/progress/sync",
        headers=headers,
        json={
            "url_hash": "e" * 64,
            "clean_url": "https://www.bilibili.com/video/BV1",
            "title": "A video",
            "progress_seconds": 18,
            "duration": 120,
            "site_host": "www.bilibili.com",
        },
    )
    assert sync.status_code == 200
    platforms = client.get("/api/v1/admin/platforms", headers=headers)
    assert platforms.json()[0]["site_host"] == "www.bilibili.com"
    assert platforms.json()[0]["site_name"] == "哔哩哔哩"

    blocked = client.post(
        "/api/v1/admin/blocked-sites",
        headers=headers,
        json={"site_host": "https://www.bilibili.com/videos"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["site_host"] == "www.bilibili.com"
    assert client.get("/api/v1/admin/history", headers=headers).json()["total"] == 0
    removed = client.delete("/api/v1/admin/blocked-sites/www.bilibili.com", headers=headers)
    assert removed.status_code == 200


def test_recent_platform_candidates_are_limited_to_ten():
    headers = admin_auth_headers("recent_sites_user")
    for index in range(11):
        host = f"site{index}.example"
        client.post(
            "/api/v1/progress/sync",
            headers=headers,
            json={
                "url_hash": f"{index:064x}",
                "clean_url": f"https://{host}/video",
                "title": f"Video {index}",
                "progress_seconds": 10,
                "duration": 120,
                "site_host": host,
            },
        )

    platforms = client.get("/api/v1/admin/platforms", headers=headers)
    assert platforms.status_code == 200
    assert len(platforms.json()) == 10


def test_dashboard_aggregates_sites_and_reports_live_playback():
    headers = admin_auth_headers("dashboard_user")
    client.post(
        "/api/v1/progress/sync",
        headers=headers,
        json={
            "url_hash": "d" * 64,
            "clean_url": "https://example.com/video",
            "title": "Dashboard video",
            "progress_seconds": 18,
            "duration": 120,
            "site_host": "example.com",
        },
    )
    response = client.get("/api/v1/admin/dashboard", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["online_device_count"] == 0
    assert data["current_videos"] == []
    assert data["sites"] == [{
        "site_host": "example.com",
        "site_name": "example.com",
        "video_count": 1,
        "watched_seconds": 18.0,
    }]


def test_favorites_and_watchlater_can_filter_by_site():
    headers = admin_auth_headers("site_filter_user")
    client.post(
        "/api/v1/admin/favorites",
        headers=headers,
        json={"clean_url": "https://a.example/video", "title": "A", "site_host": "a.example"},
    )
    client.post(
        "/api/v1/admin/favorites",
        headers=headers,
        json={"clean_url": "https://b.example/video", "title": "B", "site_host": "b.example"},
    )
    client.post(
        "/api/v1/admin/watchlater",
        headers=headers,
        json={"clean_url": "https://a.example/later", "title": "A later", "site_host": "a.example"},
    )
    client.post(
        "/api/v1/admin/watchlater",
        headers=headers,
        json={"clean_url": "https://b.example/later", "title": "B later", "site_host": "b.example"},
    )

    favorites = client.get("/api/v1/admin/favorites", params={"site_host": "a.example"}, headers=headers)
    watch_later = client.get("/api/v1/admin/watchlater", params={"site_host": "b.example"}, headers=headers)
    assert favorites.json()["total"] == 1
    assert favorites.json()["items"][0]["title"] == "A"
    assert watch_later.json()["total"] == 1
    assert watch_later.json()["items"][0]["title"] == "B later"
