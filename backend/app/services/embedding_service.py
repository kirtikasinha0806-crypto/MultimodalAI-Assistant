import os
import logging
import hashlib
from typing import List
import numpy as np
from google import genai
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._client = None

    @property
    def client(self):
        current_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if current_key and (not self._client or self.api_key != current_key):
            try:
                self.api_key = current_key
                self._client = genai.Client(api_key=current_key)
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client for embeddings: {e}")
        return self._client

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Deterministic pseudo-embedding fallback in case API key is missing or quota exceeded.
        Ensures development/testing runs smoothly.
        """
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a single piece of text."""
        cleaned_text = text.strip()
        if not cleaned_text:
            return [0.0] * self.dimension

        if self.client:
            models_to_try = [
                os.getenv("EMBEDDING_MODEL") or self.model or "gemini-embedding-2",
                "gemini-embedding-2",
                "gemini-embedding-001"
            ]
            seen = set()
            models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

            for emb_model in models_to_try:
                try:
                    response = self.client.models.embed_content(
                        model=emb_model,
                        contents=cleaned_text,
                    )
                    if response.embeddings and len(response.embeddings) > 0:
                        values = response.embeddings[0].values
                        return values
                except Exception as e:
                    logger.warning(f"Embedding model {emb_model} call failed: {e}. Trying fallback...")
        
        return self._fallback_embedding(cleaned_text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        return [self.get_embedding(t) for t in texts]

embedding_service = EmbeddingService()
