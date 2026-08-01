"""
WebSocket endpoint broadcasting realtime evaluation-queue progress to
connected dashboard clients (e.g. "AI Evaluation" page live status).
"""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Realtime"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:  # noqa: BLE001
                stale.append(connection)
        for c in stale:
            self.disconnect(c)


manager = ConnectionManager()


@router.websocket("/ws/evaluation-progress")
async def evaluation_progress_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Clients may send pings/keepalive; server pushes updates via
            # `manager.broadcast()` called from the evaluation pipeline/tasks.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
