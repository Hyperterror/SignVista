import json
import time
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..models import ChatMessage, User
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # Maps user_id to their active WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            receiver_id = message_data.get("receiver_id")
            if receiver_id:
                msg_id = message_data.get("id", str(time.time()))
                content = message_data.get("content", "")
                msg_type = message_data.get("type", "text")
                msg_time = time.time()
                
                # Save message to database
                with SessionLocal() as db:
                    new_msg = ChatMessage(
                        id=msg_id,
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        content=content,
                        type=msg_type,
                        timestamp=msg_time,
                        is_read=False
                    )
                    db.add(new_msg)
                    db.commit()
                
                # Construct clean payload for broadcast
                payload = {
                    "id": msg_id,
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "content": content,
                    "timestamp": msg_time,
                    "type": msg_type
                }
                
                # Send to sender for UI confirmation
                await manager.send_personal_message(payload, user_id)
                # Send to receiver if online
                await manager.send_personal_message(payload, receiver_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.get("/contacts")
async def get_contacts(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch distinct contacts the user has messaged."""
    user_id = current_user["user_id"]
    
    # Get distinct contacts
    sent_msgs = db.query(ChatMessage.receiver_id).filter(ChatMessage.sender_id == user_id).distinct()
    rcvd_msgs = db.query(ChatMessage.sender_id).filter(ChatMessage.receiver_id == user_id).distinct()
    
    contact_ids = {row[0] for row in sent_msgs}.union({row[0] for row in rcvd_msgs})
    
    if not contact_ids:
        # Provide a default official mock user if completely new, so the UI isn't empty
        return [
            {"id": "official_bot", "name": "SignVista Team", "status": "online", "last_message": "Welcome to SignVista!", "last_message_time": time.time()}
        ]
        
    users = db.query(User).filter(User.user_id.in_(contact_ids)).all()
    active_ids = list(manager.active_connections.keys())
    contacts = []
    
    for u in users:
        # Get last message for this conversation
        last_msg = db.query(ChatMessage).filter(
            ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == u.user_id)) |
            ((ChatMessage.sender_id == u.user_id) & (ChatMessage.receiver_id == user_id))
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        contacts.append({
            "id": u.user_id,
            "name": u.name,
            "status": "online" if u.user_id in active_ids else "offline",
            "last_message": last_msg.content if last_msg else "",
            "last_message_time": last_msg.timestamp if last_msg else 0
        })
        
    return sorted(contacts, key=lambda x: x["last_message_time"], reverse=True)

@router.get("/messages/{contact_id}")
async def get_messages(contact_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch complete chat history between current user and contact."""
    user_id = current_user["user_id"]
    
    # Special handling for mock team bot
    if contact_id == "official_bot":
        return [{
            "id": "mock_1", "sender_id": "official_bot", "receiver_id": user_id, 
            "content": "Welcome to SignVista! You can find users to practice with on the community tab.", 
            "timestamp": time.time() - 3600, "type": "text", "is_read": True
        }]

    messages = db.query(ChatMessage).filter(
        ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == contact_id)) |
        ((ChatMessage.sender_id == contact_id) & (ChatMessage.receiver_id == user_id))
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    # Mark incoming messages as read
    unread_msgs = [m for m in messages if m.receiver_id == user_id and not m.is_read]
    if unread_msgs:
        for m in unread_msgs:
            m.is_read = True
        db.commit()
    
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "timestamp": m.timestamp,
            "type": m.type,
            "is_read": m.is_read
        }
        for m in messages
    ]
