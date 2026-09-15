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


def auth_headers() -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"username": "tester", "password": "Password123", "confirm_password": "Password123"})
    response = client.post("/api/v1/auth/login", json={"username": "tester", "password": "Password123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_register_login_and_progress_round_trip():
    headers = auth_headers()
    url_hash = "a" * 64
    sync = client.post("/api/v1/progress/sync", headers=headers, json={"url_hash": url_hash, "clean_url": "https://example.com/video", "title": "Example", "progress_seconds": 120, "duration": 600, "client_updated_at": datetime.now(UTC).isoformat(), "site_host": "example.com"})
    assert sync.status_code == 200

    query = client.get(f"/api/v1/progress/query?url_hash={url_hash}", headers=headers)
    assert query.status_code == 200
    assert query.json()["progress_seconds"] == 120

    history = client.get("/api/v1/progress/list", headers=headers)
    assert history.status_code == 200
    assert history.json()["total"] == 1


def test_completed_progress_is_not_offered_for_resume():
    headers = auth_headers()
    response = client.post("/api/v1/progress/sync", headers=headers, json={"url_hash": "b" * 64, "clean_url": "https://example.com/finished", "title": "Finished", "progress_seconds": 570, "duration": 600, "site_host": "example.com"})
    assert response.status_code == 200
    query = client.get(f"/api/v1/progress/query?url_hash={'b' * 64}", headers=headers)
    assert query.json() == {"found": False, "progress_seconds": None, "duration": None, "updated_at": None}


def test_register_accepts_unicode_username():
    response = client.post("/api/v1/auth/register", json={"username": "测试用户", "password": "Password123", "confirm_password": "Password123"})
    assert response.status_code == 200


def test_progress_history_can_search_title_or_url():
    headers = auth_headers()
    client.post("/api/v1/progress/sync", headers=headers, json={"url_hash": "c" * 64, "clean_url": "https://example.com/lesson", "title": "Python 入门", "progress_seconds": 30, "duration": 600, "site_host": "example.com"})
    client.post("/api/v1/progress/sync", headers=headers, json={"url_hash": "d" * 64, "clean_url": "https://example.com/documentary", "title": "旅行纪录片", "progress_seconds": 30, "duration": 600, "site_host": "example.com"})

    response = client.get("/api/v1/progress/list", params={"search": "Python", "page_size": 5}, headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Python 入门"


def test_blocked_site_ignores_sync_and_removes_existing_history():
    headers = auth_headers()
    payload = {"url_hash": "e" * 64, "clean_url": "https://blocked.example/video", "title": "Blocked", "progress_seconds": 30, "duration": 600, "site_host": "blocked.example"}
    assert client.post("/api/v1/progress/sync", headers=headers, json=payload).status_code == 200
    blocked = client.post("/api/v1/progress/blocked-sites", headers=headers, json={"site_host": "blocked.example"})
    assert blocked.status_code == 200
    history = client.get("/api/v1/progress/list", headers=headers)
    assert history.json()["total"] == 0
    ignored = client.post("/api/v1/progress/sync", headers=headers, json=payload)
    assert ignored.json()["status"] == "ignored"


def test_progress_can_be_deleted():
    headers = auth_headers()
    payload = {"url_hash": "f" * 64, "clean_url": "https://example.com/delete", "title": "Delete me", "progress_seconds": 30, "duration": 600, "site_host": "example.com"}
    client.post("/api/v1/progress/sync", headers=headers, json=payload)
    item = client.get("/api/v1/progress/list", headers=headers).json()["items"][0]
    response = client.delete(f"/api/v1/progress/records/{item['id']}", headers=headers)
    assert response.json()["status"] == "deleted"
