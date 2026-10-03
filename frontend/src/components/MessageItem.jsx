import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Bot, 
  User, 
  Volume2, 
  VolumeX, 
  Copy, 
  Check, 
  RotateCw, 
  FileText, 
  ExternalLink,
  Heart,
  Globe,
  Eye,
  Layers
} from 'lucide-react';
import { apiClient } from '../api/client';
import { audioManager } from '../utils/audioManager';

export default function MessageItem({ message, onRegenerate, isLast }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const audioUrlRef = useRef(null);

  const metadata = message.extra_metadata || {};
  const citations = metadata.citations || [];
  const documentSources = metadata.document_sources || [];
  const mode = metadata.mode || 'default';

  // Synchronize playback state with the global audio manager
  useEffect(() => {
    const unsubscribe = audioManager.subscribe((activeMsgId, isPlaying) => {
      setIsPlayingAudio(activeMsgId === message.id && isPlaying);
    });
    return () => unsubscribe();
  }, [message.id]);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleToggleAudio = async () => {
    if (isPlayingAudio) {
      audioManager.stop();
      return;
    }

    try {
      let url = audioUrlRef.current;
      if (!url) {
        setAudioLoading(true);
        const res = await apiClient.synthesizeSpeech(message.content);
        if (res?.audio_url) {
          url = res.audio_url;
          audioUrlRef.current = url;
        }
      }

      if (url) {
        await audioManager.play(message.id, url);
      }
    } catch (err) {
      console.error('Audio playback error:', err);
    } finally {
      setAudioLoading(false);
    }
  };

  // Render Mode Badge
  const renderModeBadge = () => {
    if (mode === 'emotional_support') {
      return (
        <span className="mode-badge badge-emotional">
          <Heart size={12} /> Supportive Mode
        </span>
      );
    }
    if (mode === 'rag' || (documentSources.length > 0 && !metadata.web_search_used)) {
      return (
        <span className="mode-badge badge-rag">
          <Layers size={12} /> Document Grounded
        </span>
      );
    }
    if (mode === 'web_search' || (metadata.web_search_used && documentSources.length === 0)) {
      return (
        <span className="mode-badge badge-web">
          <Globe size={12} /> Web Grounded
        </span>
      );
    }
    if (mode === 'rag_and_web') {
      return (
        <span className="mode-badge badge-rag">
          <Layers size={12} /> Docs + Web Grounded
        </span>
      );
    }
    if (mode === 'multimodal_vision') {
      return (
        <span className="mode-badge badge-vision">
          <Eye size={12} /> Vision Analysis
        </span>
      );
    }
    return null;
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="avatar assistant-avatar">
          <Bot size={20} />
        </div>
      )}

      <div className="message-bubble">
        {!isUser && renderModeBadge()}

        <div className="message-card">
          {/* User image attachment preview */}
          {isUser && metadata.has_image && metadata.image_preview && (
            <img 
              src={metadata.image_preview} 
              alt="Attached content" 
              className="attached-image-view" 
            />
          )}

          {/* Text Content */}
          <div className="markdown-content">
            {isUser ? (
              <p style={{ whiteSpace: 'pre-wrap' }}>{message.content}</p>
            ) : (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            )}
          </div>

          {/* Document Sources Section */}
          {!isUser && documentSources.length > 0 && (
            <div className="sources-container">
              <div className="sources-header">
                <FileText size={13} />
                <span>Document Sources ({documentSources.length})</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                {documentSources.map((doc, idx) => (
                  <div key={idx} className="doc-source-card">
                    <div className="doc-source-title">
                      <span>📄 {doc.document_title}</span>
                      <span style={{ opacity: 0.6, fontSize: '0.72rem' }}>
                        (Section #{doc.chunk_index + 1})
                      </span>
                    </div>
                    {doc.content && (
                      <div className="doc-source-snippet">"{doc.content}"</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Web Search Grounding Citations Section */}
          {!isUser && citations.length > 0 && (
            <div className="sources-container">
              <div className="sources-header">
                <Globe size={13} />
                <span>Web Sources & Citations ({citations.length})</span>
              </div>
              <div className="citations-wrap">
                {citations.map((cite, idx) => (
                  <a
                    key={idx}
                    href={cite.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="citation-chip"
                    title={cite.url}
                  >
                    <span>{cite.title || cite.url}</span>
                    <ExternalLink size={11} style={{ flexShrink: 0 }} />
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Assistant Actions Bar: TTS Listen, Copy, Regenerate */}
        {!isUser && (
          <div className="message-actions">
            <button
              className={`action-pill-btn ${isPlayingAudio ? 'playing' : ''}`}
              onClick={handleToggleAudio}
              disabled={audioLoading}
              title={isPlayingAudio ? "Stop audio playback" : "Listen to response with voice"}
            >
              {audioLoading ? (
                <span>Generating audio...</span>
              ) : isPlayingAudio ? (
                <>
                  <VolumeX size={13} />
                  <span>Stop</span>
                  <div className="audio-playing-indicator">
                    <div className="wave-bar" />
                    <div className="wave-bar" />
                    <div className="wave-bar" />
                  </div>
                </>
              ) : (
                <>
                  <Volume2 size={13} />
                  <span>Listen</span>
                </>
              )}
            </button>

            <button className="action-pill-btn" onClick={handleCopy} title="Copy response to clipboard">
              {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            {isLast && onRegenerate && (
              <button className="action-pill-btn" onClick={onRegenerate} title="Regenerate response">
                <RotateCw size={13} />
                <span>Regenerate</span>
              </button>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="avatar user-avatar">
          <User size={18} />
        </div>
      )}
    </div>
  );
}
