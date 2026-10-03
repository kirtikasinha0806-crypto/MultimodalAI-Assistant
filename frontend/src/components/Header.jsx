import React from 'react';
import { 
  Sparkles, 
  Heart, 
  Globe, 
  FileText, 
  Menu,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

export default function Header({
  health,
  emotionalMode,
  setEmotionalMode,
  webSearchMode,
  setWebSearchMode,
  onOpenDocuments,
  documentCount = 0,
  onToggleSidebar,
  sidebarOpen
}) {
  const isHealthy = health?.status === 'healthy';
  const isPostgres = health?.database?.is_postgres;

  return (
    <header className="chat-header">
      <div className="header-left">
        <button 
          className="icon-btn" 
          onClick={onToggleSidebar}
          title={sidebarOpen ? "Collapse sidebar" : "Open sidebar"}
        >
          <Menu size={18} />
        </button>

        <div className="header-title-wrap">
          <div className="header-title">Multimodal AI Assistant</div>
          <div className="header-status">
            <span className={`status-dot ${isHealthy ? '' : 'offline'}`} />
            <span>
              {isHealthy 
                ? `${health?.gemini?.primary_model || 'Gemini 3.8 Flash'} • ${isPostgres ? 'pgvector' : 'Vector RAG Ready'}`
                : 'Connecting to Backend...'}
            </span>
          </div>
        </div>
      </div>

      <div className="header-controls">
        {/* Emotional Support Mode Switch */}
        <button 
          className={`mode-toggle-btn ${emotionalMode ? 'active-emotional' : ''}`}
          onClick={() => setEmotionalMode(!emotionalMode)}
          title="Toggle supportive empathetic personal assistance mode"
        >
          <Heart size={15} fill={emotionalMode ? "currentColor" : "none"} />
          <span>{emotionalMode ? "Support Mode ON" : "Support Mode"}</span>
        </button>

        {/* Web Search Grounding Switch */}
        <button 
          className={`mode-toggle-btn ${webSearchMode ? 'active-search' : ''}`}
          onClick={() => setWebSearchMode(!webSearchMode)}
          title="Enable real-time Google Search grounding"
        >
          <Globe size={15} />
          <span>{webSearchMode ? "Web Search ON" : "Web Search"}</span>
        </button>

        {/* Documents Knowledge Base Drawer Button */}
        <button 
          className="icon-btn" 
          onClick={onOpenDocuments}
          title="Manage uploaded documents & RAG knowledge base"
        >
          <FileText size={18} />
          {documentCount > 0 && <span className="badge-count">{documentCount}</span>}
        </button>
      </div>
    </header>
  );
}
