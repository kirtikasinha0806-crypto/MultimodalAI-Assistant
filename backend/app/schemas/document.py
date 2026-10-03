from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentChunkSchema(BaseModel):
    id: str
    chunk_index: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    conversation_id: Optional[str] = None
    filename: str
    title: str
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkSchema] = []

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
