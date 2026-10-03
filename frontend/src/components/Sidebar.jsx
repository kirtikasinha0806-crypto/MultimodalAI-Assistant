import React from 'react';
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  Bot,
  Sparkles
} from 'lucide-react';

export default function Sidebar({
  conversations,
  currentConvId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isOpen
}) {
  if (!isOpen) return null;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <span>AI Assistant</span>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewConversation}>
        <Plus size={18} />
        <span>New Chat</span>
      </button>

      <div className="conversations-list">
        {conversations.length === 0 ? (
          <div style={{ padding: '1.5rem 1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            No recent conversations. Start a new chat!
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${conv.id === currentConvId ? 'active' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', overflow: 'hidden' }}>
                <MessageSquare size={16} style={{ flexShrink: 0, opacity: 0.7 }} />
                <span className="conv-title">{conv.title}</span>
              </div>
              <button
                className="conv-delete-btn"
                title="Delete conversation"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConversation(conv.id);
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
