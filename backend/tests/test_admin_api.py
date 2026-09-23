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
