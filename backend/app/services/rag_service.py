import logging
from typing import List, Tuple, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import is_postgres
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.chat import DocumentReference
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class RAGService:
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def search_similar_chunks(
        db: Session,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = None
    ) -> List[Tuple[DocumentChunk, float, str]]:
        """
        Search for most similar document chunks to the query.
        Returns List of (DocumentChunk, similarity_score, document_title).
        """
        k = top_k or settings.TOP_K_CHUNKS
        query_vector = embedding_service.get_embedding(query)

        # Check if there are any indexed documents
        base_query = db.query(DocumentChunk, Document.title).join(
            Document, Document.id == DocumentChunk.document_id
        ).filter(Document.status == "ready")

        if document_ids:
            base_query = base_query.filter(Document.id.in_(document_ids))

        # 1. Native PostgreSQL + pgvector execution
        if is_postgres:
            try:
                # pgvector cosine_distance returns (1 - cosine_similarity)
                # distance ranges from 0 (identical) to 2 (opposite)
                results = base_query.order_by(
                    DocumentChunk.embedding.cosine_distance(query_vector)
                ).limit(k).all()

                formatted_results = []
                for chunk, doc_title in results:
                    # Calculate approximate similarity score
                    sim_score = 1.0
                    if chunk.embedding is not None:
                        sim_score = max(0.0, RAGService.cosine_similarity(query_vector, chunk.embedding))
                    formatted_results.append((chunk, sim_score, doc_title))
                return formatted_results
            except Exception as e:
                logger.warning(f"PostgreSQL pgvector search query failed ({e}), falling back to in-memory vector search.")

        # 2. In-memory vector calculation (SQLite fallback or error recovery)
        all_chunks = base_query.all()
        if not all_chunks:
            return []

        scored_chunks = []
        for chunk, doc_title in all_chunks:
            chunk_vec = chunk.embedding
            if chunk_vec is None:
                continue
            # If JSON serialized as string or list
            if isinstance(chunk_vec, list):
                score = RAGService.cosine_similarity(query_vector, chunk_vec)
                scored_chunks.append((chunk, score, doc_title))

        # Sort descending by similarity
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:k]

    @staticmethod
    def build_rag_context(
        db: Session,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = None,
        min_score: float = 0.50
    ) -> Tuple[str, List[DocumentReference]]:
        """
        Retrieve chunks and build a structured context prompt section.
        Only chunks meeting the minimum relevance score are included.
        """
        matches = RAGService.search_similar_chunks(db, query, document_ids=document_ids, top_k=top_k)

        if not matches:
            return "", []

        context_parts = []
        doc_references = []

        for chunk, score, doc_title in matches:
            # Filter out chunks that are irrelevant to the user query
            if score < min_score:
                continue

            context_parts.append(
                f"[Document: \"{doc_title}\" | Section #{chunk.chunk_index + 1}]\n{chunk.content}"
            )
            doc_references.append(
                DocumentReference(
                    document_id=chunk.document_id,
                    document_title=doc_title,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content[:300] + ("..." if len(chunk.content) > 300 else ""),
                    score=round(score, 3)
                )
            )

        if not doc_references:
            return "", []

        context_string = "\n\n---\n\n".join(context_parts)
        return context_string, doc_references

rag_service = RAGService()
