# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import re
import threading
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

from .auth import create_access_token
from .config import get_settings
from .db import SessionLocal
from .models import User

router = APIRouter()
HEARTBEAT_TIMEOUT_SECONDS = 300
HOST_PATTERN = re.compile(r"^[A-Za-z0-9.-]{1,255}$")
HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


@dataclass
class PlaybackConnection:
    websocket: WebSocket
    user_id: int
    client_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(UTC))
    site_host: str | None = None
    url_hash: str | None = None
    title: str = ""
    playing: bool = False
    play_started_at: datetime | None = None


class PlaybackManager:
    def __init__(self) -> None:
        self.connections: dict[WebSocket, PlaybackConnection] = {}
        self.lock = threading.Lock()

    async def connect(self, connection: PlaybackConnection) -> None:
        with self.lock:
            self.connections[connection.websocket] = connection

    async def disconnect(self, websocket: WebSocket) -> None:
        with self.lock:
            self.connections.pop(websocket, None)

    async def update(self, connection: PlaybackConnection, message: dict) -> None:
        now = datetime.now(UTC)
        kind = message.get("type")
        if kind not in {"heartbeat", "play", "pause"}:
            return
        host = message.get("site_host")
        url_hash = message.get("url_hash")
        if kind in {"play", "pause"} and (host is None or url_hash is None):
            return
        if host is not None and (not isinstance(host, str) or not HOST_PATTERN.fullmatch(host)):
            return
        if url_hash is not None and (not isinstance(url_hash, str) or not HASH_PATTERN.fullmatch(url_hash)):
            return

        pause_targets: list[PlaybackConnection] = []
        with self.lock:
            connection.last_heartbeat = now
            connection.site_host = host.lower() if isinstance(host, str) else None
            connection.url_hash = url_hash.lower() if isinstance(url_hash, str) else None
            title = message.get("title", "")
            connection.title = title[:1000] if isinstance(title, str) else ""
            if kind == "play":
                connection.playing = True
                connection.play_started_at = now
                for other in list(self.connections.values()):
                    if (
                        other.user_id == connection.user_id
                        and other.websocket is not connection.websocket
                        and other.playing
                        and other.site_host == connection.site_host
                        and other.url_hash == connection.url_hash
                    ):
                        other.playing = False
                        pause_targets.append(other)
            elif kind == "pause":
                connection.playing = False
            else:
                connection.playing = bool(message.get("playing", False))

        for other in pause_targets:
            try:
                await other.websocket.send_json({"type": "pause", "site_host": connection.site_host, "url_hash": connection.url_hash})
            except (RuntimeError, WebSocketDisconnect):
                await self.disconnect(other.websocket)

    def snapshot(self, user_id: int) -> list[PlaybackConnection]:
        now = datetime.now(UTC)
        with self.lock:
            return [
                replace(connection)
                for connection in self.connections.values()
                if connection.user_id == user_id
                and (now - connection.last_heartbeat).total_seconds() <= HEARTBEAT_TIMEOUT_SECONDS
            ]


playback_manager = PlaybackManager()


def authenticate_token(token: str) -> User | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        user_id = int(payload.get("sub", ""))
    except (JWTError, TypeError, ValueError):
        return None

    with SessionLocal() as db:
        return db.scalar(select(User).where(User.id == user_id))


@router.websocket("/api/v1/ws/playback")
async def playback_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    connection: PlaybackConnection | None = None
    try:
        try:
            auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        except TimeoutError:
            await websocket.close(code=1008, reason="authentication timeout")
            return
        if not isinstance(auth_message, dict) or auth_message.get("type") != "auth":
            await websocket.close(code=1008, reason="authentication required")
            return

        user = authenticate_token(str(auth_message.get("token", "")))
        client_id = auth_message.get("client_id")
        if user is None or not isinstance(client_id, str) or not client_id or len(client_id) > 128:
            await websocket.close(code=1008, reason="invalid authentication")
            return

        connection = PlaybackConnection(websocket=websocket, user_id=user.id, client_id=client_id)
        await playback_manager.connect(connection)
        await websocket.send_json({"type": "authenticated", "access_token": create_access_token(user.id)})

        while True:
            try:
                elapsed = (datetime.now(UTC) - connection.last_heartbeat).total_seconds()
                timeout = max(0.1, HEARTBEAT_TIMEOUT_SECONDS - elapsed)
                message = await asyncio.wait_for(websocket.receive_json(), timeout=timeout)
            except TimeoutError:
                await websocket.close(code=1001, reason="heartbeat timeout")
                break
            if isinstance(message, dict):
                await playback_manager.update(connection, message)
                await websocket.send_json({"type": "heartbeat_ack"})
    except (WebSocketDisconnect, TimeoutError):
        pass
    finally:
        if connection is not None:
            await playback_manager.disconnect(websocket)
