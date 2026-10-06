"""
SignVista — Chat Routes

WS   /api/chat/ws                 — authenticated real-time messaging (`?ticket=`)
GET  /api/chat/contacts           — conversations for the current user
GET  /api/chat/messages/{id}      — message history with a contact (paginated)
POST /api/chat/send               — send a message over HTTP (fallback for WS)

WebSocket protocol: send `{"receiver_id": str, "content": str, "type": "text"|"sign"}`;
the server replies with the stored message (sender and receiver both receive it)
or `{"error": "..."}`.
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from typing import Dict, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.dependencies import authenticate_websocket, get_current_user
from app.models import ChatMessage, User
from app.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

OFFICIAL_BOT_ID = "official_bot"
MAX_MESSAGE_CHARS = 2000
WS_POLICY_VIOLATION = 1008


class ChatSendRequest(BaseModel):
    receiver_id: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=MAX_MESSAGE_CHARS)
    type: str = Field("text", pattern="^(text|sign)$")

    @field_validator("content")
    @classmethod
    def _content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


# ─── Connection manager ───────────────────────────────────────────

class ConnectionManager:
    """Tracks every open socket per user (a user may have several tabs)."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        async with self._lock:
            self.active_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        async with self._lock:
            conns = self.active_connections.get(user_id)
            if conns is not None:
                conns.discard(websocket)
                if not conns:
                    del self.active_connections[user_id]

    def is_online(self, user_id: str) -> bool:
        return bool(self.active_connections.get(user_id))

    async def send_personal_message(self, message: dict, user_id: str):
        for ws in list(self.active_connections.get(user_id, ())):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                await self.disconnect(ws, user_id)


manager = ConnectionManager()


def _serialize(m: ChatMessage) -> Dict:
    return {
        "id": m.id,
        "sender_id": m.sender_id,
        "receiver_id": m.receiver_id,
        "content": m.content,
        "timestamp": m.timestamp,
        "type": m.type,
        "is_read": m.is_read,
    }


def _store_message(sender_id: str, receiver_id: str, content: str, msg_type: str) -> Dict:
    """Validate and persist a message. Raises ValueError with a user-facing reason."""
    if receiver_id == sender_id:
        raise ValueError("You can't message yourself")
    if receiver_id == OFFICIAL_BOT_ID:
        raise ValueError("The SignVista Team account doesn't accept replies")
    if not limiter.hit(f"chat:{sender_id}", limit=30, window_seconds=60):
        raise ValueError("You're sending messages too quickly")
    with SessionLocal() as db:
        if db.query(User.id).filter(User.user_id == receiver_id).first() is None:
            raise ValueError("Recipient not found")
        msg = ChatMessage(
            id=uuid.uuid4().hex,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            type=msg_type,
            timestamp=time.time(),
            is_read=False,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return _serialize(msg)


async def _deliver(payload: Dict) -> None:
    await manager.send_personal_message(payload, payload["sender_id"])
    await manager.send_personal_message(payload, payload["receiver_id"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user = await run_in_threadpool(authenticate_websocket, websocket)
    if user is None:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return
    user_id = user["user_id"]

    await manager.connect(websocket, user_id)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                req = ChatSendRequest(**json.loads(raw))
            except Exception:
                await websocket.send_json({"error": "Invalid message format"})
                continue
            try:
                payload = await run_in_threadpool(_store_message, user_id, req.receiver_id, req.content, req.type)
            except ValueError as e:
                await websocket.send_json({"error": str(e)})
                continue
            except Exception:
                logger.exception("Failed to store chat message")
                await websocket.send_json({"error": "Message could not be sent"})
                continue
            await _deliver(payload)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception(f"Chat WebSocket error for {user_id}")
    finally:
        await manager.disconnect(websocket, user_id)


@router.post("/send")
async def send_message(request: ChatSendRequest, current_user: Dict = Depends(get_current_user)):
    """HTTP fallback for sending a message."""
    try:
        payload = await run_in_threadpool(_store_message, current_user["user_id"], request.receiver_id,
                                          request.content, request.type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await _deliver(payload)
    return payload


@router.get("/contacts")
def get_contacts(current_user: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Conversations the user has, newest first (plus the welcome bot for new users)."""
    user_id = current_user["user_id"]

    sent = db.query(ChatMessage.receiver_id).filter(ChatMessage.sender_id == user_id).distinct()
    rcvd = db.query(ChatMessage.sender_id).filter(ChatMessage.receiver_id == user_id).distinct()
    contact_ids = {r[0] for r in sent} | {r[0] for r in rcvd}

    if not contact_ids:
        return [{
            "id": OFFICIAL_BOT_ID, "name": "SignVista Team", "status": "online",
            "last_message": "Welcome to SignVista!", "last_message_time": time.time(), "unread_count": 0,
        }]

    users = db.query(User).filter(User.user_id.in_(contact_ids)).all()
    unread = dict(
        db.query(ChatMessage.sender_id, func.count(ChatMessage.id))
        .filter(ChatMessage.receiver_id == user_id, ChatMessage.is_read.is_(False))
        .group_by(ChatMessage.sender_id)
        .all()
    )

    contacts = []
    for u in users:
        last_msg = (
            db.query(ChatMessage)
            .filter(or_(
                and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == u.user_id),
                and_(ChatMessage.sender_id == u.user_id, ChatMessage.receiver_id == user_id),
            ))
            .order_by(ChatMessage.timestamp.desc())
            .first()
        )
        contacts.append({
            "id": u.user_id,
            "name": u.name,
            "status": "online" if manager.is_online(u.user_id) else "offline",
            "last_message": last_msg.content if last_msg else "",
            "last_message_time": last_msg.timestamp if last_msg else 0,
            "unread_count": unread.get(u.user_id, 0),
        })

    return sorted(contacts, key=lambda x: x["last_message_time"], reverse=True)


@router.get("/messages/{contact_id}")
def get_messages(
    contact_id: str,
    before: Optional[float] = Query(None, description="Return messages older than this timestamp"),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat history with a contact, oldest first. Marks incoming messages as read."""
    user_id = current_user["user_id"]

    if contact_id == OFFICIAL_BOT_ID:
        return [{
            "id": "welcome", "sender_id": OFFICIAL_BOT_ID, "receiver_id": user_id,
            "content": "Welcome to SignVista! You can find users to practice with on the community tab.",
            "timestamp": current_user.get("created_at") or time.time(), "type": "text", "is_read": True,
        }]

    q = db.query(ChatMessage).filter(or_(
        and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == contact_id),
        and_(ChatMessage.sender_id == contact_id, ChatMessage.receiver_id == user_id),
    ))
    if before is not None:
        q = q.filter(ChatMessage.timestamp < before)
    messages = list(reversed(q.order_by(ChatMessage.timestamp.desc()).limit(limit).all()))

    unread = [m for m in messages if m.receiver_id == user_id and not m.is_read]
    if unread:
        for m in unread:
            m.is_read = True
        db.commit()

    return [_serialize(m) for m in messages]
