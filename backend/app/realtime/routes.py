import asyncio
import json
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from redis import Redis as SyncRedis
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import SessionLocal
from app.domain.models import Board
from app.realtime.broker import channel_for_board

router = APIRouter(tags=["realtime"])
connections: dict[int, set[WebSocket]] = defaultdict(set)


def can_access(board_id: int, user_id: int | None) -> bool:
    if not user_id:
        return False
    db: Session = SessionLocal()
    try:
        board = db.scalar(select(Board).options(selectinload(Board.workspace), selectinload(Board.members)).where(Board.id == board_id))
        return bool(board and (board.workspace.owner_id == user_id or any(member.id == user_id for member in board.members)))
    finally:
        db.close()


def consume_ticket(ticket: str) -> int | None:
    if not ticket:
        return None
    client = SyncRedis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    try:
        value = client.getdel(f"teamflow:ws-ticket:{ticket}")
        return int(value) if value else None
    except Exception:
        return None
    finally:
        client.close()


async def relay_from_redis(board_id: int, websocket: WebSocket, ready: asyncio.Event) -> None:
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=None)
    pubsub = client.pubsub()
    try:
        await pubsub.subscribe(channel_for_board(board_id))
        ready.set()
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            payload = message.get("data")
            if isinstance(payload, bytes):
                payload = payload.decode()
            await websocket.send_text(payload if isinstance(payload, str) else json.dumps(payload))
    finally:
        await pubsub.unsubscribe(channel_for_board(board_id))
        await getattr(pubsub, "aclose")()
        await getattr(client, "aclose")()


@router.websocket("/ws/boards/{board_id}")
async def board_events(websocket: WebSocket, board_id: int):
    user_id = consume_ticket(websocket.query_params.get("ticket", ""))
    if not can_access(board_id, user_id):
        await websocket.close(code=1008, reason="Authentication required")
        return
    await websocket.accept()
    connections[board_id].add(websocket)
    ready = asyncio.Event()
    relay_task = asyncio.create_task(relay_from_redis(board_id, websocket, ready))
    try:
        await asyncio.wait_for(ready.wait(), timeout=2)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        relay_task.cancel()
        await asyncio.gather(relay_task, return_exceptions=True)
        connections[board_id].discard(websocket)
        if not connections[board_id]:
            connections.pop(board_id, None)
