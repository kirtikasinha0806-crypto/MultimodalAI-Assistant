import os
import re
import uuid
import base64
import hashlib
import logging
from gtts import gTTS
from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

class AudioService:
    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Strip markdown syntax, code blocks, URLs, and asterisks for smooth speech synthesis."""
        # Remove code blocks
        clean = re.sub(r"```[\s\S]*?```", " [code snippet] ", text)
        clean = re.sub(r"`[^`]*`", "", clean)
        # Remove markdown URLs: [text](url) -> text
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
        # Remove pure URLs
        clean = re.sub(r"https?://\S+", "", clean)
        # Remove markdown heading hashes, asterisks, bullet points
        clean = re.sub(r"[#*_~>]+", "", clean)
        # Clean extra whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def synthesize_speech(text: str) -> str:
        """
        Synthesize text to speech using gTTS and return filename.
        Caches synthesized audio based on text hash to avoid regeneration.
        """
        spoken_text = AudioService.clean_text_for_speech(text)
        if not spoken_text:
            spoken_text = "I have no text to read."

        # Truncate for audio generation limit if very long
        if len(spoken_text) > 1500:
            spoken_text = spoken_text[:1500] + "... and more."

        text_hash = hashlib.md5(spoken_text.encode("utf-8")).hexdigest()
        filename = f"tts_{text_hash}.mp3"
        filepath = os.path.join(settings.AUDIO_DIR, filename)

        if not os.path.exists(filepath):
            try:
                tts = gTTS(text=spoken_text, lang="en", slow=False)
                tts.save(filepath)
            except Exception as e:
                logger.error(f"Failed to generate speech with gTTS: {e}")
                raise e

        return filename

    @staticmethod
    def transcribe_audio(audio_base64: str, mime_type: str = "audio/wav") -> str:
        """
        Transcribe user-recorded speech to text using Gemini multimodal audio understanding.
        """
        # Handle data URL prefix
        raw_b64 = audio_base64
        if "," in raw_b64:
            header, raw_b64 = raw_b64.split(",", 1)
            if "audio/" in header:
                mime_type = header.split(";")[0].replace("data:", "")

        audio_bytes = base64.b64decode(raw_b64)

        current_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        if not current_key:
            return "Microphone recording received. (Please set GEMINI_API_KEY in backend/.env for AI transcription)"

        try:
            client = genai.Client(api_key=current_key)
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type or "audio/wav")
            prompt = types.Part.from_text(
                text="Transcribe the spoken words in this audio recording accurately. "
                     "Return only the transcribed text, with proper punctuation, without adding any conversational intro or commentary."
            )

            # Try ultra-fast models supporting audio understanding in order of speed and quota availability
            models_to_try = [
                "gemini-3.5-transcribe",
                "gemini-3.1-flash-lite-preview",
                "gemini-3.5-flash-lite",
                "gemini-flash-lite-latest",
                "gemini-3-flash-preview",
                "gemini-3.8-flash"
            ]
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[types.Content(role="user", parts=[audio_part, prompt])]
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as ex:
                    logger.warning(f"Audio transcription with {model_name} failed: {ex}")

            raise Exception("Unable to transcribe audio with available models.")

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise e

audio_service = AudioService()
