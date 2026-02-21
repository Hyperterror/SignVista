import json
import time
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter()

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
            # Parse incoming JSON message
            message_data = json.loads(data)
            
            # Broadcast the message to the intended receiver
            receiver_id = message_data.get("receiver_id")
            if receiver_id:
                # Construct clean payload
                payload = {
                    "id": message_data.get("id", str(time.time())),
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "content": message_data.get("content", ""),
                    "timestamp": time.time(),
                    "type": message_data.get("type", "text")
                }
                
                # Send back to sender for their own UI update confirmation
                await manager.send_personal_message(payload, user_id)
                
                # Send to receiver if online
                await manager.send_personal_message(payload, receiver_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Return mock active users (everyone online right now)
@router.get("/contacts")
async def get_contacts():
    # Return everyone connected + some mocked offline users for UI testing
    active_ids = list(manager.active_connections.keys())
    
    contacts = [
        {"id": "user_1", "name": "Aarav Sharma", "status": "online" if "user_1" in active_ids else "offline", "last_message": "Hey!", "last_message_time": time.time() - 3600},
        {"id": "user_2", "name": "Ishani Gupta", "status": "online" if "user_2" in active_ids else "away", "last_message": "Did you see the new ISL sign?", "last_message_time": time.time() - 86400},
        {"id": "user_3", "name": "Vivek Mehra", "status": "offline", "last_message": "Let's practice tomorrow.", "last_message_time": time.time() - 172800},
    ]
    return contacts

@router.get("/messages/{contact_id}")
async def get_messages(contact_id: str):
    # Historical DB logic would go here. For now returning empty list to let WS handle realtime 
    return []
