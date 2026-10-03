from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Citation(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None

class DocumentReference(BaseModel):
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    score: Optional[float] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message text")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image string")
    image_mime_type: Optional[str] = Field("image/jpeg", description="MIME type of image")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio string")
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to restrict search to")
    emotional_support_mode: bool = Field(False, description="Enable empathetic emotional-assistance mode")
    enable_web_search: Optional[bool] = Field(None, description="Force or auto-detect web search")

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    audio_url: Optional[str] = None
    citations: List[Citation] = []
    document_sources: List[DocumentReference] = []
    web_search_used: bool = False
    rag_used: bool = False
    mode: str = "default"
