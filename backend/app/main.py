import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.api.routes import chat, conversations, documents, audio, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB tables
    logger.info("Starting up Multimodal AI Assistant...")
    init_db()
    yield
    logger.info("Shutting down Multimodal AI Assistant...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multimodal AI Personal Assistant API with RAG, Vision, Audio, and Search Grounding",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
api_prefix = settings.API_V1_STR
app.include_router(chat.router, prefix=api_prefix)
app.include_router(conversations.router, prefix=api_prefix)
app.include_router(documents.router, prefix=api_prefix)
app.include_router(audio.router, prefix=api_prefix)
app.include_router(health.router, prefix=api_prefix)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "api_docs": "/docs",
        "api_version": "v1"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
