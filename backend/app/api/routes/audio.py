import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas.audio import (
    AudioTranscriptionRequest,
    AudioTranscriptionResponse,
    AudioSynthesisRequest,
    AudioSynthesisResponse,
)
from app.services.audio_service import audio_service

router = APIRouter(prefix="/audio", tags=["audio"])

@router.post("/transcribe", response_model=AudioTranscriptionResponse)
def transcribe_audio(payload: AudioTranscriptionRequest):
    """Transcribe speech audio to text using Gemini multimodal audio model."""
    try:
        text = audio_service.transcribe_audio(
            audio_base64=payload.audio_base64,
            mime_type=payload.mime_type or "audio/wav"
        )
        return AudioTranscriptionResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")

@router.post("/synthesize", response_model=AudioSynthesisResponse)
def synthesize_speech(payload: AudioSynthesisRequest):
    """Synthesize text into speech MP3 using gTTS."""
    try:
        filename = audio_service.synthesize_speech(payload.text)
        audio_url = f"{settings.API_V1_STR}/audio/file/{filename}"
        return AudioSynthesisResponse(audio_url=audio_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@router.get("/file/{filename}")
def stream_audio(filename: str):
    """Stream generated audio MP3 file."""
    # Sanitize filename
    safe_name = os.path.basename(filename)
    filepath = os.path.join(settings.AUDIO_DIR, safe_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/mpeg")
