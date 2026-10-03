import logging
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)

# Pattern to detect when user specifically refers to document/file/report content
DOC_QUERY_PATTERN = re.compile(
    r"\b(document|documents|doc|docs|pdf|pdfs|file|files|attachment|attachments|uploaded|upload|"
    r"sheet|sheets|spreadsheet|spreadsheets|excel|xlsx|csv|presentation|powerpoint|pptx|slide|slides|"
    r"paper|papers|resume|report|reports|manual|handbook|contract|invoice|chapter|page|section|"
    r"in the doc|in the document|in the file|in the pdf|according to the doc|according to the document|"
    r"from the document|from the file|from the pdf|summarize the doc|summarize the document|"
    r"summarize the pdf|summarize the file|what is written in|what does the file say|what does the document say|"
    r"analyse it|analyze it|analyse this|analyze this|review it|review this|summarize it|summarize this|"
    r"break it down|explain it|key takeaways|what is in it|what does it say)\b",
    re.IGNORECASE
)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Main multimodal chat endpoint handling:
    - Text queries
    - Vision (image input)
    - Document RAG (retrieval-augmented generation)
    - Google Search grounding
    - Emotional-support mode
    - Conversation history
    """
    query = payload.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Manage Conversation Session
    conv_id = payload.conversation_id
    conversation = None
    if conv_id:
        conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()

    if not conversation:
        # Generate friendly title from first 6 words of message
        title_words = query.split()[:6]
        title = " ".join(title_words)
        if len(title) > 60:
            title = title[:57] + "..."
        conversation = Conversation(title=title or "New Chat")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conv_id = conversation.id

    # 2. Retrieve Conversation History for Context
    past_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .limit(10)
        .all()
    )
    history_turns = [{"role": m.role, "content": m.content} for m in past_messages]

    # 3. Determine User Modality
    modality = "text"
    if payload.image_base64:
        modality = "image"
    elif payload.audio_base64:
        modality = "audio"

    # 4. Save User Message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=query,
        modality=modality,
        extra_metadata={
            "has_image": bool(payload.image_base64),
            "document_ids": payload.document_ids or []
        }
    )
    db.add(user_msg)
    db.commit()

    # 5. RAG Retrieval Logic
    # Strict per-conversation isolation rules:
    # 1. Vision & Emotional: NEVER inject document context
    # 2. Strict conversation scoping:
    #    - If documents were uploaded in THIS conversation (conv_id), ONLY search those documents.
    #    - If no documents exist for this conversation, do NOT search documents from other chats!
    document_context = ""
    document_sources = []
    rag_used = False

    is_vision_turn = bool(payload.image_base64)
    is_emotional_turn = bool(payload.emotional_support_mode)

    if not is_vision_turn and not is_emotional_turn:
        # Check if this specific conversation has attached documents
        conv_docs = (
            db.query(Document)
            .filter(Document.status == "ready", Document.conversation_id == conv_id)
            .all()
        )
        
        target_doc_ids = None
        has_accessible_docs = False

        if conv_docs:
            # Strictly restrict to documents uploaded in THIS conversation!
            target_doc_ids = [d.id for d in conv_docs]
            has_accessible_docs = True
        elif payload.document_ids and len(payload.document_ids) > 0:
            # User explicitly requested specific document IDs
            target_doc_ids = payload.document_ids
            has_accessible_docs = True
        else:
            # No documents belong to this conversation! Completely isolated!
            has_accessible_docs = False

        if has_accessible_docs and target_doc_ids:
            query_mentions_docs = bool(DOC_QUERY_PATTERN.search(query))
            
            # Check if this specific conversation has previously used document RAG
            prior_turn_used_rag = any(
                isinstance(m.extra_metadata, dict) and m.extra_metadata.get("rag_used")
                for m in past_messages
            )

            # In this conversation, if docs exist, run RAG if:
            # - User explicitly asked about documents / analysis ("analyse it", "summarize", etc.)
            # - OR user has already been discussing documents in this chat
            # - OR there are very few messages in a conversation where documents were uploaded
            if query_mentions_docs or prior_turn_used_rag or len(past_messages) <= 2:
                doc_ctx, doc_refs = rag_service.build_rag_context(
                    db,
                    query=query,
                    document_ids=target_doc_ids,
                    top_k=4,
                    min_score=0.45
                )
                if doc_ctx:
                    document_context = doc_ctx
                    document_sources = doc_refs
                    rag_used = True

    # 6. Web Search Grounding Decision
    should_search = web_search_service.should_search_web(
        query=query,
        explicit_flag=payload.enable_web_search
    )

    # 7. Generate Response via Gemini Service
    response_text, citations, web_search_used = gemini_service.generate_response(
        query=query,
        conversation_history=history_turns,
        image_base64=payload.image_base64,
        image_mime_type=payload.image_mime_type,
        document_context=document_context,
        enable_web_search=should_search,
        emotional_support_mode=payload.emotional_support_mode,
    )

    # 8. Determine Active Mode
    active_mode = "default"
    if payload.emotional_support_mode:
        active_mode = "emotional_support"
    elif payload.image_base64:
        active_mode = "multimodal_vision"
    elif rag_used and web_search_used:
        active_mode = "rag_and_web"
    elif rag_used:
        active_mode = "rag"
    elif web_search_used:
        active_mode = "web_search"

    # 9. Save Assistant Response in Database
    assistant_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=response_text,
        modality="text",
        extra_metadata={
            "citations": [c.model_dump() for c in citations],
            "document_sources": [d.model_dump() for d in document_sources],
            "web_search_used": web_search_used,
            "rag_used": rag_used,
            "mode": active_mode
        }
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    # Update conversation updated_at
    conversation.updated_at = assistant_msg.created_at
    db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        message_id=assistant_msg.id,
        response=response_text,
        audio_url=None,  # Synthesized on-demand via Listen button
        citations=citations,
        document_sources=document_sources,
        web_search_used=web_search_used,
        rag_used=rag_used,
        mode=active_mode
    )
