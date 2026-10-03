from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentUpdate,
)
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List documents optionally filtered by conversation_id."""
    query = db.query(Document)
    if conversation_id:
        query = query.filter(Document.conversation_id == conversation_id)
    return query.order_by(Document.created_at.desc()).all()

@router.post("", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, TXT, DOCX), extract text, chunk, embed, and store in PostgreSQL + pgvector.
    Optionally scoped to a specific conversation_id.
    """
    doc = document_service.save_and_index_document(
        db, 
        file, 
        title=title, 
        conversation_id=conversation_id
    )
    return doc

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details and its indexed chunks."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update document metadata or content. If content is updated, old chunks and embeddings are replaced.
    """
    doc = document_service.update_document(
        db,
        document_id=document_id,
        title=update_data.title,
        new_content=update_data.content
    )
    return doc

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and all associated vector chunks from PostgreSQL/pgvector."""
    document_service.delete_document(db, document_id)
    return {"message": "Document and embeddings deleted successfully", "id": document_id}
