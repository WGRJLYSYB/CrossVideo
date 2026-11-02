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

import pytest
os.environ["CROSSVIDEO_DATABASE_URL"] = "sqlite:///./data/test-crossvideo.db"
os.environ["CROSSVIDEO_SECRET_KEY"] = "test-secret-key"

from jose import jwt
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.models import CaptchaChallenge, User
from app.main import app


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def avoid_external_title_requests(monkeypatch):
    from app.routers import progress

    monkeypatch.setattr(progress, "fetch_and_save_site_title", lambda _site_id: None)


def captcha_fields(prefix: str = "/api/v1") -> dict:
    challenge = client.get(f"{prefix}/auth/captcha").json()
    with SessionLocal() as db:
        stored = db.get(CaptchaChallenge, challenge["challenge_id"])
        clicks = stored.target_points
    return {"captcha_id": challenge["challenge_id"], "captcha_clicks": clicks}


def auth_headers() -> dict[str, str]:
    client.post("/api/v1/auth/register", json={
        "username": "tester",
        "password": "Password123",
        "confirm_password": "Password123",
        **captcha_fields(),
    })
    response = client.post("/api/v1/auth/login", json={
        "username": "tester",
        "password": "Password123",
        **captcha_fields(),
    })
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


def test_progress_sync_checks_site_title_only_once(monkeypatch):
    from app import site_tasks
    from app.db import SessionLocal
    from app.models import UserSite
    from app.site_tasks import fetch_and_save_site_title
    from app.routers import progress

    calls = []

    def fetch_title(site_host):
        calls.append(site_host)
        return "Example site"

    monkeypatch.setattr(site_tasks, "fetch_homepage_title", fetch_title)
    monkeypatch.setattr(progress, "fetch_and_save_site_title", fetch_and_save_site_title)
    headers = auth_headers()
    payload = {
        "url_hash": "1" * 64,
        "clean_url": "https://example.com/video",
        "title": "Example video",
        "progress_seconds": 30,
        "duration": 600,
        "site_host": "example.com",
    }

    assert client.post("/api/v1/progress/sync", headers=headers, json=payload).status_code == 200
    assert calls == ["example.com"]
    with SessionLocal() as db:
        site = db.query(UserSite).filter_by(site_host="example.com").one()
        assert site.title_fetch_attempted
        assert site.site_name == "Example site"

    payload["url_hash"] = "2" * 64
    assert client.post("/api/v1/progress/sync", headers=headers, json=payload).status_code == 200
    assert calls == ["example.com"]


def test_failed_site_title_check_is_still_marked_complete(monkeypatch):
    from app import site_tasks
    from app.models import UserSite
    from app.site_tasks import fetch_and_save_site_title
    from app.routers import progress

    monkeypatch.setattr(site_tasks, "fetch_homepage_title", lambda _host: None)
    monkeypatch.setattr(progress, "fetch_and_save_site_title", fetch_and_save_site_title)
    headers = auth_headers()
    response = client.post("/api/v1/progress/sync", headers=headers, json={
        "url_hash": "9" * 64,
        "clean_url": "https://unavailable.example/video",
        "title": "Video",
        "progress_seconds": 10,
        "duration": 60,
        "site_host": "unavailable.example",
    })
    assert response.status_code == 200
    with SessionLocal() as db:
        site = db.query(UserSite).filter_by(site_host="unavailable.example").one()
        assert site.title_fetch_attempted
        assert site.site_name == "unavailable.example"


def test_site_title_parser_and_private_address_guard():
    from app.site_tasks import _TitleParser, fetch_homepage_title

    parser = _TitleParser()
    parser.feed("<html><title>Film &amp; Story</title></html>")
    assert "".join(parser.title_parts) == "Film & Story"
    assert fetch_homepage_title("127.0.0.1") is None


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
    response = client.post("/api/v1/auth/register", json={
        "username": "测试用户",
        "password": "Password123",
        "confirm_password": "Password123",
        **captcha_fields(),
    })
    assert response.status_code == 200


def test_captcha_is_required_and_single_use():
    fields = captcha_fields()
    fields["captcha_clicks"] = [{"x": 1, "y": 1}, {"x": 2, "y": 2}]
    payload = {
        "username": "captcha-user",
        "password": "Password123",
        "confirm_password": "Password123",
        **fields,
    }

    failed = client.post("/api/v1/auth/register", json=payload)
    assert failed.status_code == 400
    replay = client.post("/api/v1/auth/register", json=payload)
    assert replay.status_code == 400


def test_totp_setup_requires_code_and_login_requires_second_factor():
    headers = auth_headers()
    setup = client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]

    import pyotp
    enabled = client.post("/api/v1/auth/2fa/enable", headers=headers, json={"code": pyotp.TOTP(secret).now()})
    assert enabled.status_code == 200
    with SessionLocal() as db:
        user = db.query(User).filter_by(username="tester").one()
        assert user.totp_enabled
        assert user.totp_secret != secret

    response = client.post("/api/v1/auth/login", json={
        "username": "tester",
        "password": "Password123",
        **captcha_fields(),
    })
    assert response.status_code == 200
    assert response.json()["requires_2fa"] is True
    assert response.json()["access_token"] is None
    challenge_headers = {"Authorization": f"Bearer {response.json()['challenge_token']}"}
    assert client.get("/api/v1/progress/list", headers=challenge_headers).status_code == 401

    verified = client.post("/api/v1/auth/login/2fa", json={
        "challenge_token": response.json()["challenge_token"],
        "code": pyotp.TOTP(secret).now(),
    })
    assert verified.status_code == 200
    assert verified.json()["access_token"]


def test_email_activation_and_password_reset(monkeypatch):
    from app.models import EmailActionToken, User
    from app.routers import auth as auth_router
    from app.verification import record_email_send_attempt

    sent = []

    def fake_send(db, user_id, purpose, email, subject, path, token, _template):
        record_email_send_attempt(db, user_id, purpose)
        sent.append((email, subject, path, token))

    monkeypatch.setattr(
        auth_router,
        "send_action_email",
        fake_send,
    )
    headers = auth_headers()
    request = client.post("/api/v1/auth/email", headers=headers, json={"email": "tester@example.com"})
    assert request.status_code == 200
    assert sent[-1][2] == "verify-email"
    limited = client.post("/api/v1/auth/email", headers=headers, json={"email": "tester@example.com"})
    assert limited.status_code == 429
    assert len(sent) == 1
    settings = client.get("/api/v1/auth/settings", headers=headers)
    assert settings.status_code == 200
    assert settings.json()["pending_email"] == "tester@example.com"
    with SessionLocal() as db:
        user = db.query(User).filter_by(username="tester").one()
        assert user.email is None

    confirmed = client.post("/api/v1/auth/email/confirm", json={"token": sent[-1][3]})
    assert confirmed.status_code == 200
    with SessionLocal() as db:
        user = db.query(User).filter_by(username="tester").one()
        assert user.email == "tester@example.com"
        assert user.email_verified

    client.post("/api/v1/auth/register", json={
        "username": "other-user",
        "password": "Password123",
        "confirm_password": "Password123",
        **captcha_fields(),
    })
    other_login = client.post("/api/v1/auth/login", json={
        "username": "other-user",
        "password": "Password123",
        **captcha_fields(),
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    conflict = client.post("/api/v1/auth/email", headers=other_headers, json={"email": "tester@example.com"})
    assert conflict.status_code == 409

    reset_requested = client.post("/api/v1/auth/password-reset/request", json={"email": "tester@example.com"})
    assert reset_requested.status_code == 200
    assert sent[-1][2] == "reset-password"
    repeated_reset = client.post("/api/v1/auth/password-reset/request", json={"email": "tester@example.com"})
    assert repeated_reset.status_code == 200
    assert len(sent) == 2
    reset = client.post("/api/v1/auth/password-reset/confirm", json={
        "token": sent[-1][3],
        "new_password": "NewPassword123",
        "confirm_password": "NewPassword123",
    })
    assert reset.status_code == 200
    relogin = client.post("/api/v1/auth/login", json={
        "username": "tester",
        "password": "NewPassword123",
        **captcha_fields(),
    })
    assert relogin.status_code == 200
    assert relogin.json()["access_token"]

    with SessionLocal() as db:
        assert db.query(EmailActionToken).filter_by(purpose="reset_password").one().used_at is not None


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
