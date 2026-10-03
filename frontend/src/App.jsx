import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import InputArea from './components/InputArea';
import DocumentDrawer from './components/DocumentDrawer';
import { apiClient } from './api/client';
import { audioManager } from './utils/audioManager';
import './App.css';

export default function App() {
  const [health, setHealth] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Assistant Modes
  const [emotionalMode, setEmotionalMode] = useState(false);
  const [webSearchMode, setWebSearchMode] = useState(false);

  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [docDrawerOpen, setDocDrawerOpen] = useState(false);

  // 1. Initial Load: Health, Conversations, Documents
  useEffect(() => {
    checkHealth();
    loadConversations();
    loadDocuments();
  }, []);

  const checkHealth = async () => {
    try {
      const data = await apiClient.getHealth();
      setHealth(data);
    } catch (err) {
      console.warn('Backend currently offline or starting up...');
      setHealth({ status: 'offline' });
    }
  };

  const loadConversations = async () => {
    try {
      const list = await apiClient.listConversations();
      setConversations(list);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const loadDocuments = async (convId = currentConvId) => {
    try {
      if (!convId) {
        setDocuments([]);
        return;
      }
      const docs = await apiClient.listDocuments(convId);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  // 2. Load Conversation Messages and Its Private Documents
  const selectConversation = async (convId) => {
    audioManager.stop();
    setCurrentConvId(convId);
    try {
      const conv = await apiClient.getConversation(convId);
      setMessages(conv.messages || []);
      await loadDocuments(convId);
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
    }
  };

  // 3. New Conversation (Clean Slate)
  const handleNewConversation = () => {
    audioManager.stop();
    setCurrentConvId(null);
    setMessages([]);
    setDocuments([]);
  };

  // 4. Delete Conversation
  const handleDeleteConversation = async (convId) => {
    audioManager.stop();
    try {
      await apiClient.deleteConversation(convId);
      if (currentConvId === convId) {
        handleNewConversation();
      }
      await loadConversations();
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // 5. Send Message
  const handleSendMessage = async ({
    message,
    image_base64,
    image_mime_type,
    image_preview
  }) => {
    if (isLoading) return;

    // Optimistically show user message
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      modality: image_base64 ? 'image' : 'text',
      extra_metadata: {
        has_image: !!image_base64,
        image_preview: image_preview || image_base64
      },
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const res = await apiClient.sendMessage({
        message,
        conversation_id: currentConvId,
        image_base64,
        image_mime_type,
        emotional_support_mode: emotionalMode,
        enable_web_search: webSearchMode ? true : null
      });

      // Update current conversation ID if newly created
      if (!currentConvId && res.conversation_id) {
        setCurrentConvId(res.conversation_id);
      }

      // Add assistant message
      const assistantMsg = {
        id: res.message_id,
        role: 'assistant',
        content: res.response,
        modality: 'text',
        extra_metadata: {
          citations: res.citations,
          document_sources: res.document_sources,
          web_search_used: res.web_search_used,
          rag_used: res.rag_used,
          mode: res.mode
        },
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, assistantMsg]);
      await loadConversations();
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Error communicating with assistant:** ${err.message || 'Please check your connection and GEMINI_API_KEY.'}`,
        modality: 'text',
        extra_metadata: {},
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // 6. Regenerate Last Assistant Message
  const handleRegenerateLast = () => {
    // Find the last user message
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMsg) {
      handleSendMessage({
        message: lastUserMsg.content,
        image_base64: lastUserMsg.extra_metadata?.image_preview
      });
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar with Conversation History */}
      <Sidebar
        conversations={conversations}
        currentConvId={currentConvId}
        onSelectConversation={selectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
      />

      {/* Main Chat Interface */}
      <main className="main-chat">
        <Header
          health={health}
          emotionalMode={emotionalMode}
          setEmotionalMode={setEmotionalMode}
          webSearchMode={webSearchMode}
          setWebSearchMode={setWebSearchMode}
          onOpenDocuments={() => setDocDrawerOpen(true)}
          documentCount={documents.length}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
        />

        <ChatArea
          messages={messages}
          isLoading={isLoading}
          onSelectPrompt={(text) => handleSendMessage({ message: text })}
          onRegenerateLast={handleRegenerateLast}
        />

        <InputArea
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          onOpenDocuments={() => setDocDrawerOpen(true)}
          documentCount={documents.length}
        />
      </main>

      {/* Document Knowledge Base Drawer (RAG) */}
      <DocumentDrawer
        isOpen={docDrawerOpen}
        onClose={() => setDocDrawerOpen(false)}
        documents={documents}
        currentConvId={currentConvId}
        onConversationCreated={async (newId) => {
          setCurrentConvId(newId);
          await loadConversations();
        }}
        onRefreshDocuments={loadDocuments}
      />
    </div>
  );
}
