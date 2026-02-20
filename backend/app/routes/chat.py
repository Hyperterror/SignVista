from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time

router = APIRouter()

class Message(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: float
    type: str = "text"

class Contact(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None
    status: str = "offline"
    last_message: Optional[str] = None
    last_message_time: Optional[float] = None

# Mock Data
MOCK_CONTACTS = [
    {"id": "user_1", "name": "Aarav Sharma", "status": "online", "last_message": "Hey, how are you?", "last_message_time": time.time() - 3600},
    {"id": "user_2", "name": "Ishani Gupta", "status": "away", "last_message": "Did you see the new ISL sign for 'Future'?", "last_message_time": time.time() - 86400},
    {"id": "user_3", "name": "Vivek Mehra", "status": "offline", "last_message": "Let's practice tomorrow.", "last_message_time": time.time() - 172800},
    {"id": "user_4", "name": "Meera Iyer", "status": "online", "last_message": "Awesome work on the dashboard!", "last_message_time": time.time() - 500},
]

MOCK_MESSAGES = {
    "user_1": [
        {"id": "m1", "sender_id": "user_1", "receiver_id": "me", "content": "Hey, how are you?", "timestamp": time.time() - 3600, "type": "text"},
        {"id": "m2", "sender_id": "me", "receiver_id": "user_1", "content": "I'm good, just practicing some signs.", "timestamp": time.time() - 3500, "type": "text"},
    ]
}

@router.get("/contacts", response_model=List[Contact])
async def get_contacts():
    return MOCK_CONTACTS

@router.get("/messages/{contact_id}", response_model=List[Message])
async def get_messages(contact_id: str):
    if contact_id not in MOCK_MESSAGES:
        return []
    return MOCK_MESSAGES[contact_id]

@router.post("/send")
async def send_message(msg: Message):
    # In a real app, we'd save to DB here
    return {"status": "sent", "message_id": msg.id}
