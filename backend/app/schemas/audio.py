from pydantic import BaseModel
from typing import Optional

class AudioTranscriptionRequest(BaseModel):
    audio_base64: str
    mime_type: Optional[str] = "audio/wav"

class AudioTranscriptionResponse(BaseModel):
    text: str
    status: str = "success"

class AudioSynthesisRequest(BaseModel):
    text: str
    voice: Optional[str] = "default"

class AudioSynthesisResponse(BaseModel):
    audio_url: str
    format: str = "mp3"
    status: str = "success"
