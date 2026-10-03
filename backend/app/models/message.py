import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    modality = Column(String(20), default="text")  # 'text', 'image', 'audio', 'document'
    extra_metadata = Column(JSON, default=dict)  # Stores sources, web citations, image paths, audio urls
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")
