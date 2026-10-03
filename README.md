# Multimodal AI Assistant

A production-ready, beautifully designed full-stack **Multimodal AI Assistant** built with React, FastAPI, SQLAlchemy, PostgreSQL + pgvector, and Google Gemini.

---

## 🌟 Key Features

- 🧠 **Google Gemini Multimodal AI**: Text generation, complex reasoning, and multimodal image analysis (photos, charts, UI screenshots).
- 📚 **Per-Conversation Document RAG (Retrieval-Augmented Generation)**:
  - **Universal Format Support**: Parses and indexes **PDF, Word (.docx/.doc), Excel (.xlsx/.xls), PowerPoint (.pptx/.ppt), CSV, JSON, Markdown, Code files (.py, .js, .ts, .html, .css, etc.), and plain text**.
  - **Strict Chat Isolation**: Documents uploaded in Chat A stay strictly bound to Chat A. Chat B will never see or leak documents from Chat A, and fresh chats remain completely clean. Returning to Chat A instantly restores its document context.
  - **Vector Search Engine**: Fast embeddings using `gemini-embedding-2` (3072-dimensional vectors) stored in PostgreSQL with `pgvector` (with automatic resilient local vector storage fallback).
- 🎙️ **Real-Time Speech-to-Text (STT)**:
  - **Zero-Latency Dictation**: Browser-native Web Speech API streams speech into the input box in real time as you talk with zero delay and zero quota consumption.
  - **Ultra-Fast AI Fallback**: Sub-second backend transcription using specialized models (`gemini-3.5-transcribe` and `gemini-3.1-flash-lite-preview`).
- 🔊 **Global Smart Audio Player (TTS)**:
  - Synthesizes assistant responses into natural speech.
  - **Zero Overlap**: Clicking "Listen" on any message immediately stops previous audio.
  - **Auto-Stop on Navigation**: Switching between conversations or clicking "New Chat" immediately stops any playing voice.
  - **Restart From Beginning**: Toggling playback off and on always restarts speech cleanly from the beginning.
- 🌐 **Real-Time Web Search Grounding**: Live web information retrieval with clickable citations and domain source links, backed by real-time DuckDuckGo search fallback if Google Search quota is reached.
- 💖 **Emotional-Support Assistance Mode**: Empathetic, supportive conversational persona with built-in safety screening and crisis helpline guidance (e.g. 988).
- 🎨 **Modern Responsive UI**: React 19 + Vite with rich dark-mode aesthetics, glassmorphism, responsive sidebar, document knowledge base drawer, and smooth micro-animations.

---

## 🏗️ Architecture & Project Structure

```text
Chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint & lifecycle
│   │   ├── config.py                   # Pydantic settings & environment configuration
│   │   ├── database.py                 # SQLAlchemy engine (PostgreSQL + pgvector / SQLite fallback)
│   │   │
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── chat.py             # Multimodal chat & isolated conversation RAG
│   │   │       ├── documents.py        # Document upload, extraction, CRUD & re-indexing
│   │   │       ├── audio.py            # STT transcription & TTS audio streaming
│   │   │       ├── conversations.py    # Conversation list, details & deletion
│   │   │       └── health.py           # System status & DB connection health check
│   │   │
│   │   ├── models/
│   │   │   ├── conversation.py         # Conversation schema
│   │   │   ├── message.py              # Message schema (roles, content, metadata)
│   │   │   ├── document.py             # Document schema with conversation_id scoping
│   │   │   └── document_chunk.py       # pgvector vector embeddings
│   │   │
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   │
│   │   └── services/
│   │       ├── gemini_service.py       # Google GenAI SDK client with resilient model cascading
│   │       ├── rag_service.py          # Vector similarity search & context assembler
│   │       ├── embedding_service.py    # Vector embeddings service (gemini-embedding-2)
│   │       ├── document_service.py     # Universal multi-format document parser & text chunker
│   │       ├── web_search_service.py   # Search grounding & live web fallback
│   │       ├── audio_service.py        # Speech transcription & gTTS speech synthesis
│   │       └── safety_service.py       # Emotional support prompt & crisis detection
│   │
│   ├── uploads/                        # Document uploads storage
│   ├── audio_cache/                    # Synthesized audio cache
│   ├── requirements.txt                # Backend dependencies
│   └── .env.example                    # Environment template
│
└── frontend/
    ├── src/
    │   ├── api/client.js               # Centralized fetch client
    │   ├── utils/
    │   │   └── audioManager.js         # Singleton global audio player controller
    │   ├── components/
    │   │   ├── Header.jsx              # Status, mode switches & knowledge base drawer toggle
    │   │   ├── Sidebar.jsx             # Conversation history & new chat
    │   │   ├── ChatArea.jsx            # Message stream & starter cards
    │   │   ├── MessageItem.jsx         # Bubble with TTS, markdown, & citations
    │   │   ├── InputArea.jsx           # Textarea, image uploader, voice recorder
    │   │   └── DocumentDrawer.jsx      # Scoped document drawer & management
    │   ├── App.jsx                     # Root React application
    │   ├── App.css                     # Component styles & animations
    │   └── index.css                   # Design system tokens & reset
    ├── package.json
    └── vite.config.js                  # Vite dev server & backend proxy
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Node.js 18+** & **npm**
- *(Optional)* **PostgreSQL** with `pgvector` enabled (local development automatically falls back to an embedded SQLite vector store if PostgreSQL is offline).

---

### 2. Configure Backend & API Key

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   - On Windows (PowerShell):
     ```powershell
     .\venv\Scripts\activate
     ```
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```

3. Ensure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your `.env` file inside `backend/`:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   PRIMARY_MODEL=gemini-3.1-flash-lite-preview
   EMBEDDING_MODEL=gemini-embedding-2
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chatbot
   ```
   > 💡 Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *Interactive API Docs:* http://127.0.0.1:8000/docs

---

### 3. Start the Frontend Application

1. Open a new terminal in the `frontend` directory:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. Open your browser and navigate to:
   ```text
   http://127.0.0.1:3001/
   ```

---

## 📖 Feature Walkthrough

### 1. Multimodal Vision Analysis 📷
- Click the **Image icon** next to the chat input to attach an image or screenshot (`.png`, `.jpg`, `.webp`).
- Ask questions like: *"What is in this screenshot?"* or *"Analyze this diagram."*
- **Strict Isolation**: Image questions focus exclusively on the attached image; document context is never injected into image analysis.

### 2. Per-Chat Document Knowledge Base (RAG) 📄
- Click the **Document icon** to open the **Documents Drawer**.
- Drag & drop or select documents (**PDF, DOCX, XLSX, PPTX, CSV, JSON, TXT, Code, Markdown**).
- **Chat Isolation**:
  - Documents uploaded in Chat 1 belong only to Chat 1.
  - Starting a new chat gives you a clean slate with zero document interference.
  - Returning to Chat 1 in the sidebar restores its private documents and continues document-grounded answers.
- Inspect chunks, edit document contents directly, or delete files with automatic vector clean-up.

### 3. Live Search Grounding 🌐
- Toggle **Web Search** in the header.
- Ask questions about current events or real-time data.
- The assistant grounds its answers with live web citations, backed by automatic fallback if API quotas are reached.

### 4. Voice Dictation & Text-to-Speech 🎙️🔊
- **Real-Time Voice-to-Text**: Click the **Mic button** and start speaking. Words appear live in the textarea with zero latency.
- **On-Demand Speech**: Click **"Listen"** on any assistant response to hear it spoken aloud.
- **Smart Control**: Clicking **"Stop"** stops playback and resets it to `0:00`. Clicking **"Listen"** again restarts cleanly from the beginning. Audio stops automatically whenever you switch chats.

### 5. Emotional-Support Assistance Mode 💖
- Toggle **Support Mode** in the header.
- Activates an empathetic, reflective persona designed for active listening and stress management.
- Includes safety screening that detects crisis keywords and provides immediate helpline assistance (e.g. 988).

---

## 🛡️ Security & Reliability
- API keys stay securely on the backend and are never sent to the browser.
- File uploads are validated against allowed MIME types and capped at 25MB.
- Dynamic environment variable reloading allows instant key updates without server restarts.
- Automatic model cascade prevents downtime if any single model encounters temporary rate limits.

---

## ⚠️ Known Limitations

| Area | Limitation |
|---|---|
| **API Quotas** | All AI features (chat, RAG embeddings, TTS, STT fallback, web search) depend on the Google Gemini free-tier quota. Heavy usage may hit rate limits and temporarily degrade responses. |
| **File Upload Size** | Documents are capped at **25 MB** per file. Very large PDFs or spreadsheets may be rejected or partially indexed. |
| **Voice Dictation (STT)** | Real-time dictation uses the browser's built-in Web Speech API, which is **only supported in Chromium-based browsers** (Chrome, Edge). Firefox and Safari are not supported. Only **English** is reliably supported; other languages may produce inaccurate transcriptions. |
| **Text-to-Speech (TTS)** | Audio is synthesized via gTTS and streamed from the backend. Very long responses may take a few seconds to start playing. |
| **Image Analysis** | Only `.png`, `.jpg`, and `.webp` images are supported. Maximum recommended image size is ~5 MB. PDFs with embedded images are extracted as text only (images inside PDFs are not vision-analyzed). |
| **Web Search** | Live search results depend on DuckDuckGo availability. Search grounding may occasionally return outdated or irrelevant snippets for highly specific queries. |
| **Database** | Without PostgreSQL + pgvector, the system falls back to a local SQLite vector store. SQLite fallback is slower and not recommended for large document collections (100+ pages). |
| **No User Authentication** | This project has **no login system**. All conversations and documents are stored locally and are accessible to anyone who can reach the running server. Do not deploy publicly without adding authentication. |
| **Local Deployment Only** | This app is designed to run **locally on your machine**. It is not configured for cloud/production deployment out of the box (no HTTPS, no auth, no rate limiting). |
