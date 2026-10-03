from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    modality: str
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationListSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True

class ConversationSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
