import os
import json

os.environ["CROSSVIDEO_DATABASE_URL"] = "sqlite:///./data/test-crossvideo.db"
os.environ["CROSSVIDEO_SECRET_KEY"] = "test-secret-key"

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.models import CaptchaChallenge
from app.main import app
from app.routers import ai

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def avoid_external_title_requests(monkeypatch):
    from app.routers import progress

    monkeypatch.setattr(progress, "fetch_and_save_site_title", lambda _site_id: None)


def captcha_fields() -> dict:
    challenge = client.get("/api/v1/auth/captcha").json()
    with SessionLocal() as db:
        stored = db.get(CaptchaChallenge, challenge["challenge_id"])
        clicks = stored.target_points
    return {"captcha_id": challenge["challenge_id"], "captcha_clicks": clicks}


def auth_headers() -> dict[str, str]:
    client.post("/api/v1/auth/register", json={
        "username": "ai-user",
        "password": "Password123",
        "confirm_password": "Password123",
        **captcha_fields(),
    })
    response = client.post("/api/v1/auth/login", json={
        "username": "ai-user",
        "password": "Password123",
        **captcha_fields(),
    })
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_ai_chat_persists_history_and_uses_provider_token_counts(monkeypatch):
    monkeypatch.setattr(ai, "get_settings", lambda: SimpleNamespace(
        deepseek_api_key="test-key",
        monthly_ai_token_quota=1000,
        deepseek_model="deepseek-chat",
        deepseek_base_url="https://api.deepseek.com",
    ))
    calls = []

    def fake_chat(messages, max_tokens):
        calls.append((messages, max_tokens))
        if messages[0]["content"] == ai.CLASSIFIER_SYSTEM_PROMPT:
            return '{"allowed": true}', 5

    monkeypatch.setattr(ai, "_deepseek_chat", fake_chat)
    monkeypatch.setattr(ai, "_deepseek_chat_stream", lambda _messages, _max_tokens: iter([
        ("可以从人物弧光来理解这段剧情。", None),
        ("", 17),
    ]))
    headers = auth_headers()
    response = client.post("/api/v1/ai/chat", headers=headers, json={"message": "分析一下电影里的角色成长"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers.get("x-access-token")
    events = [json.loads(line.removeprefix("data: ")) for line in response.text.splitlines() if line.startswith("data: ")]
    assert events[0] == {"type": "delta", "content": "可以从人物弧光来理解这段剧情。"}
    assert events[-1]["type"] == "done"
    assert events[-1]["tokens_used"] == 22
    assert events[-1]["used_tokens"] == 22
    assert len(calls) == 1

    history = client.get("/api/v1/ai/chat/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["messages"] == [
        {"role": "user", "content": "分析一下电影里的角色成长"},
        {"role": "assistant", "content": "可以从人物弧光来理解这段剧情。"},
    ]
    assert history.json()["remaining_tokens"] == 978
    admin_history = client.get("/api/v1/admin/ai/chat/history", headers=headers)
    assert admin_history.status_code == 200
    assert admin_history.json()["messages"] == history.json()["messages"]

    assert client.delete("/api/v1/ai/chat/history", headers=headers).status_code == 200
    assert client.get("/api/v1/ai/chat/history", headers=headers).json()["messages"] == []


def test_ai_refuses_non_film_topics_without_generating_an_answer(monkeypatch):
    monkeypatch.setattr(ai, "get_settings", lambda: SimpleNamespace(
        deepseek_api_key="test-key",
        monthly_ai_token_quota=1000,
        deepseek_model="deepseek-chat",
        deepseek_base_url="https://api.deepseek.com",
    ))
    calls = []

    def fake_chat(messages, _max_tokens):
        calls.append(messages)
        return '{"allowed": false}', 4

    monkeypatch.setattr(ai, "_deepseek_chat", fake_chat)
    response = client.post("/api/v1/ai/chat", headers=auth_headers(), json={"message": "帮我写一个 Python 程序"})
    assert response.status_code == 200
    events = [json.loads(line.removeprefix("data: ")) for line in response.text.splitlines() if line.startswith("data: ")]
    assert "只回答电影" in events[-1]["answer"]
    assert events[-1]["tokens_used"] == 4
    assert len(calls) == 1


def test_ai_chat_requires_deepseek_configuration(monkeypatch):
    monkeypatch.setattr(ai, "get_settings", lambda: SimpleNamespace(
        deepseek_api_key="",
        monthly_ai_token_quota=1000,
    ))
    response = client.post("/api/v1/ai/chat", headers=auth_headers(), json={"message": "聊聊电影"})
    assert response.status_code == 503
