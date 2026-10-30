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
from datetime import UTC, datetime, timedelta

os.environ["CROSSVIDEO_DATABASE_URL"] = "sqlite:///./data/test-crossvideo.db"
os.environ["CROSSVIDEO_SECRET_KEY"] = "test-secret-key"

from jose import jwt
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


def test_authenticated_request_renews_token():
    headers = auth_headers()
    original_token = headers["Authorization"].removeprefix("Bearer ")
    original_payload = jwt.decode(original_token, "test-secret-key", algorithms=["HS256"])
    expiring_token = jwt.encode(
        {"sub": original_payload["sub"], "exp": datetime.now(UTC) + timedelta(days=1)},
        "test-secret-key",
        algorithm="HS256",
    )

    response = client.get("/api/v1/progress/list", headers={"Authorization": f"Bearer {expiring_token}"})

    assert response.status_code == 200
    refreshed_token = response.headers["x-access-token"]
    refreshed_payload = jwt.decode(refreshed_token, "test-secret-key", algorithms=["HS256"])
    assert refreshed_payload["sub"] == original_payload["sub"]
    assert refreshed_payload["exp"] > jwt.get_unverified_claims(expiring_token)["exp"]


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


def test_playback_websocket_pauses_only_earlier_same_video():
    headers = auth_headers()
    token = headers["Authorization"].removeprefix("Bearer ")
    playback = {
        "site_host": "video.example",
        "url_hash": "a" * 64,
        "title": "Same video",
        "playing": True,
    }

    with client.websocket_connect("/api/v1/ws/playback") as first:
        first.send_json({"type": "auth", "token": token, "client_id": "device-1"})
        assert first.receive_json()["type"] == "authenticated"
        first.send_json({"type": "play", **playback})
        assert first.receive_json()["type"] == "heartbeat_ack"
        dashboard = client.get("/api/v1/admin/dashboard", headers=headers).json()
        assert dashboard["online_device_count"] == 1
        assert dashboard["current_videos"][0]["title"] == "Same video"

        with client.websocket_connect("/api/v1/ws/playback") as second:
            second.send_json({"type": "auth", "token": token, "client_id": "device-2"})
            assert second.receive_json()["type"] == "authenticated"
            second.send_json({"type": "play", **playback})
            assert second.receive_json()["type"] == "heartbeat_ack"
            pause = first.receive_json()
            assert pause == {"type": "pause", "site_host": "video.example", "url_hash": "a" * 64}
            live = client.get("/api/v1/admin/dashboard", headers=headers).json()
            assert live["online_device_count"] == 2
            assert [video["title"] for video in live["current_videos"]] == ["Same video"]
