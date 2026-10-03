import os
import base64
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from google import genai
from google.genai import types

from app.config import settings
from app.schemas.chat import Citation, DocumentReference
from app.services.safety_service import safety_service
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)

def get_base_system_instruction() -> str:
    current_date_str = datetime.now().strftime("%A, %B %d, %Y")
    return (
        f"You are a helpful, knowledgeable, and accurate multimodal AI personal assistant.\n"
        f"The current real-world date is: {current_date_str}.\n"
        "When answering questions:\n"
        "- Always be aware of the current date and modern era.\n"
        "- If DOCUMENT CONTEXT is provided, strictly prioritize it for document-specific questions.\n"
        "- Do not invent facts that are absent from the retrieved document context.\n"
        "- Clearly state if the uploaded documents do not contain enough information to fully answer.\n"
        "- When WEB CONTEXT or search grounding is provided, synthesize the facts and cite accurately.\n"
        "- Keep responses clear, well-structured, formatted in markdown, and concise."
    )

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.primary_model = settings.PRIMARY_MODEL
        self._client = None

    @property
    def client(self):
        current_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if current_key and (not self._client or self.api_key != current_key):
            try:
                self.api_key = current_key
                self._client = genai.Client(api_key=current_key)
            except Exception as e:
                logger.error(f"Failed to create Google GenAI client: {e}")
        return self._client

    def generate_response(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
        image_base64: Optional[str] = None,
        image_mime_type: Optional[str] = "image/jpeg",
        document_context: Optional[str] = None,
        enable_web_search: bool = False,
        emotional_support_mode: bool = False,
    ) -> Tuple[str, List[Citation], bool]:
        """
        Generate multimodal response using Gemini with RAG, web search grounding, or vision.
        Returns: (response_text, citations_list, web_search_used)
        """
        # 1. Immediate Safety / Crisis screening
        is_crisis, crisis_msg = safety_service.check_crisis(query)
        if is_crisis:
            return crisis_msg, [], False

        # 2. Check Client Availability
        if not self.client:
            return (
                "⚠️ **Gemini API Key Missing**\n\n"
                "Please configure your `GEMINI_API_KEY` in the `backend/.env` file to enable real Gemini AI responses.\n\n"
                "You can get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey).",
                [],
                False
            )

        # 3. Construct System Instruction with Real-Time Date
        if emotional_support_mode:
            system_instruction = safety_service.get_emotional_support_instruction()
        else:
            system_instruction = get_base_system_instruction()

        # 4. Construct Prompt Structure with Clear Source Separation
        prompt_sections = []

        if document_context and document_context.strip():
            prompt_sections.append(
                f"DOCUMENT CONTEXT:\n{document_context.strip()}\n"
                "(Instructions: Use this document context to answer the user query. Do not extrapolate unsupported claims.)"
            )

        prompt_sections.append(f"USER QUERY:\n{query.strip()}")
        final_prompt_text = "\n\n".join(prompt_sections)

        # 5. Assemble Contents (Conversation History + Current Turn)
        contents = []

        if conversation_history:
            recent_history = conversation_history[-8:]
            for turn in recent_history:
                role = "user" if turn.get("role") == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=turn.get("content", ""))]
                    )
                )

        current_parts = []

        if image_base64:
            try:
                raw_b64 = image_base64
                if "," in raw_b64:
                    header, raw_b64 = raw_b64.split(",", 1)
                    if "image/" in header:
                        extracted_mime = header.split(";")[0].replace("data:", "")
                        if extracted_mime:
                            image_mime_type = extracted_mime

                image_bytes = base64.b64decode(raw_b64)
                current_parts.append(
                    types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type or "image/jpeg")
                )
            except Exception as e:
                logger.error(f"Error decoding image attachment: {e}")

        current_parts.append(types.Part.from_text(text=final_prompt_text))
        contents.append(types.Content(role="user", parts=current_parts))

        # 6. Configure Tools (Google Search Grounding)
        tools = []
        if enable_web_search and not image_base64:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools if tools else None,
            temperature=0.7 if not document_context else 0.2,
        )

        try:
            candidate_models = [
                os.getenv("PRIMARY_MODEL") or self.primary_model or "gemini-3.8-flash",
                "gemini-3-flash-preview",
                "gemini-3.1-flash-lite-preview",
                "gemini-3.8-flash",
                "gemini-flash-latest",
            ]
            seen = set()
            models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

            response = None
            last_err = None
            citations = []
            web_used = False

            for model_name in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config,
                    )
                    if response and response.text:
                        break
                except Exception as ex:
                    last_err = ex
                    err_str = str(ex).lower()
                    logger.warning(f"Model {model_name} invocation failed: {ex}. Trying next fallback...")

                    # If Google Search Grounding quota exceeded, perform live DDGS search fallback
                    if tools and ("resource_exhausted" in err_str or "429" in err_str or "quota" in err_str):
                        logger.info("Google Search tool quota reached. Performing live web search fallback...")
                        live_web_context, live_citations = web_search_service.perform_live_search(query)
                        
                        # Rebuild contents with live web context
                        fallback_prompt_sections = []
                        if document_context and document_context.strip():
                            fallback_prompt_sections.append(f"DOCUMENT CONTEXT:\n{document_context.strip()}")
                        if live_web_context:
                            fallback_prompt_sections.append(f"WEB CONTEXT (Live Search Results):\n{live_web_context}")
                        fallback_prompt_sections.append(f"USER QUERY:\n{query.strip()}")
                        new_prompt_text = "\n\n".join(fallback_prompt_sections)
                        new_contents = [c for c in contents[:-1]]
                        new_contents.append(
                            types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=new_prompt_text)]
                            )
                        )
                        contents = new_contents
                        citations = live_citations
                        web_used = bool(live_citations)
                        config.tools = None
                        tools = None

                        try:
                            response = self.client.models.generate_content(
                                model=model_name,
                                contents=contents,
                                config=config,
                            )
                            if response and response.text:
                                break
                        except Exception as retry_ex:
                            last_err = retry_ex
                            continue

            if not response or not response.text:
                raise last_err or Exception("Empty response returned by Gemini model.")

            # Extract citations from Google Search grounding if present
            if response.candidates and len(response.candidates) > 0 and not citations:
                cand = response.candidates[0]
                citations = web_search_service.extract_grounding_citations(cand)
                if citations:
                    web_used = True

            return response.text, citations, web_used

        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            return (
                f"I encountered an error communicating with Gemini: {str(e)}.\n\n"
                f"Please verify your `GEMINI_API_KEY` and network connection.",
                [],
                False
            )

gemini_service = GeminiService()
