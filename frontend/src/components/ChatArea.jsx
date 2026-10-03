import React, { useEffect, useRef } from 'react';
import MessageItem from './MessageItem';
import { Sparkles, FileText, Search, Heart, Camera } from 'lucide-react';

export default function ChatArea({
  messages,
  isLoading,
  onSelectPrompt,
  onRegenerateLast
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const starterPrompts = [
    {
      icon: <FileText size={16} color="#818cf8" />,
      title: "Analyze Uploaded Documents",
      sub: "Ask questions and extract insights using pgvector RAG"
    },
    {
      icon: <Camera size={16} color="#f472b6" />,
      title: "Understand Images & Visuals",
      sub: "Attach a photo, diagram, or chart and ask questions"
    },
    {
      icon: <Search size={16} color="#38bdf8" />,
      title: "Real-Time Web Search",
      sub: "Find current events, latest updates, and cited sources"
    },
    {
      icon: <Heart size={16} color="#fb7185" />,
      title: "Supportive Emotional Sounding Board",
      sub: "Share your thoughts, journal, or reflect on your day"
    }
  ];

  return (
    <div className="messages-container">
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="empty-logo">
            <Sparkles size={34} />
          </div>
          <div>
            <h1 className="empty-title">How can I assist you today?</h1>
            <p className="empty-desc">
              Your personal multimodal AI assistant. Upload documents for RAG question-answering, attach images, transcribe speech, or search the live web.
            </p>
          </div>

          <div className="prompts-grid">
            {starterPrompts.map((p, idx) => (
              <div 
                key={idx} 
                className="prompt-card"
                onClick={() => onSelectPrompt(p.title)}
              >
                <div className="prompt-card-title">
                  {p.icon}
                  <span>{p.title}</span>
                </div>
                <div className="prompt-card-sub">{p.sub}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageItem
            key={msg.id || index}
            message={msg}
            isLast={index === messages.length - 1}
            onRegenerate={onRegenerateLast}
          />
        ))
      )}

      {/* Loading Shimmer Indicator */}
      {isLoading && (
        <div className="message-row assistant">
          <div className="avatar assistant-avatar">
            <Sparkles size={18} />
          </div>
          <div className="message-bubble">
            <div className="message-card" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div className="skeleton-pulse">
                <div className="pulse-dot" />
                <div className="pulse-dot" />
                <div className="pulse-dot" />
              </div>
              <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
                Gemini is synthesizing response...
              </span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
