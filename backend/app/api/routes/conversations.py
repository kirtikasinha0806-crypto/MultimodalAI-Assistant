from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import (
    ConversationSchema,
    ConversationListSchema,
    ConversationCreate,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationListSchema])
def list_conversations(db: Session = Depends(get_db)):
    """List all conversations ordered by recent activity."""
    conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    results = []
    for c in conversations:
        count = db.query(Message).filter(Message.conversation_id == c.id).count()
        results.append(
            ConversationListSchema(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=count
            )
        )
    return results

@router.post("", response_model=ConversationSchema)
def create_conversation(data: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new empty conversation."""
    conversation = Conversation(title=data.title or "New Conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.get("/{conversation_id}", response_model=ConversationSchema)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation details and full message history."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully", "id": conversation_id}
