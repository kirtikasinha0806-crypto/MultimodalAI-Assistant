import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base, is_postgres
from app.config import settings

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# Support native pgvector on PostgreSQL while enabling JSON fallback on SQLite
embedding_column_type = (
    Vector(settings.EMBEDDING_DIMENSION) if is_postgres else JSON
)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(embedding_column_type, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    document = relationship("Document", back_populates="chunks")
