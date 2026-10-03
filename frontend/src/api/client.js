const API_BASE = '/api/v1';

export const apiClient = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Conversations
  async listConversations() {
    const res = await fetch(`${API_BASE}/conversations`);
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },

  async createConversation(title = 'New Conversation') {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },

  async getConversation(id) {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    if (!res.ok) throw new Error('Failed to load conversation');
    return res.json();
  },

  async deleteConversation(id) {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete conversation');
    return res.json();
  },

  // Chat
  async sendMessage({
    message,
    conversation_id,
    image_base64,
    image_mime_type,
    audio_base64,
    document_ids,
    emotional_support_mode,
    enable_web_search,
  }) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id,
        image_base64,
        image_mime_type,
        audio_base64,
        document_ids,
        emotional_support_mode,
        enable_web_search,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Chat request failed');
    }
    return res.json();
  },

  // Documents
  async listDocuments(conversationId) {
    const url = conversationId 
      ? `${API_BASE}/documents?conversation_id=${encodeURIComponent(conversationId)}` 
      : `${API_BASE}/documents`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async uploadDocument(file, title, conversationId) {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (conversationId) formData.append('conversation_id', conversationId);

    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Document upload failed');
    }
    return res.json();
  },

  async getDocument(id) {
    const res = await fetch(`${API_BASE}/documents/${id}`);
    if (!res.ok) throw new Error('Failed to fetch document');
    return res.json();
  },

  async updateDocument(id, { title, content }) {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to update document');
    }
    return res.json();
  },

  async deleteDocument(id) {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  },

  // Audio STT & TTS
  async transcribeAudio(audioBase64, mimeType = 'audio/webm') {
    const res = await fetch(`${API_BASE}/audio/transcribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audio_base64: audioBase64, mime_type: mimeType }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Transcription failed');
    }
    return res.json();
  },

  async synthesizeSpeech(text) {
    const res = await fetch(`${API_BASE}/audio/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Speech synthesis failed');
    }
    return res.json();
  },
};
