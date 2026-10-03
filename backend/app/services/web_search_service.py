import re
import logging
from typing import List, Tuple, Optional
from ddgs import DDGS
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)

SEARCH_TRIGGER_PATTERNS = [
    r"\b(latest|current|recent|today|news|update|upcoming|scheduled)\b",
    r"\b(who is currently|who won|score|weather|stock|price|exchange rate)\b",
    r"\b(2025|2026)\b",
    r"\b(release date|what happened to|where is now)\b",
]

class WebSearchService:
    @staticmethod
    def should_search_web(query: str, explicit_flag: Optional[bool] = None) -> bool:
        """Determine whether web search grounding is appropriate for the query."""
        if explicit_flag is not None:
            return explicit_flag

        lower_query = query.lower()
        for pattern in SEARCH_TRIGGER_PATTERNS:
            if re.search(pattern, lower_query):
                return True
        return False

    @staticmethod
    def extract_grounding_citations(candidate) -> List[Citation]:
        """Extract web citations and sources from Gemini grounding metadata."""
        citations = []
        if not candidate:
            return citations

        metadata = getattr(candidate, "grounding_metadata", None)
        if not metadata:
            return citations

        chunks = getattr(metadata, "grounding_chunks", None) or []
        for ch in chunks:
            web = getattr(ch, "web", None)
            if web:
                uri = getattr(web, "uri", "")
                title = getattr(web, "title", "") or uri
                if uri and not any(c.url == uri for c in citations):
                    citations.append(Citation(title=title, url=uri))

        return citations

    @staticmethod
    def perform_live_search(query: str, max_results: int = 5) -> Tuple[str, List[Citation]]:
        """
        Perform live web search via DDGS to fetch up-to-date real-time articles,
        snippets, and citations. Used when Google Search tool reaches API quota.
        """
        citations = []
        context_snippets = []

        try:
            results = list(DDGS().text(query, max_results=max_results))
            for r in results:
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")

                if href and title:
                    citations.append(Citation(title=title, url=href, snippet=body[:150]))
                    context_snippets.append(f"Title: {title}\nURL: {href}\nSummary: {body}")

            formatted_context = "\n\n---\n\n".join(context_snippets)
            return formatted_context, citations
        except Exception as e:
            logger.warning(f"Live web search failed: {e}")
            return "", []

web_search_service = WebSearchService()
