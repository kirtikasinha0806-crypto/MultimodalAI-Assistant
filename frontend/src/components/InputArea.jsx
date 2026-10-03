import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Image as ImageIcon, 
  Mic, 
  Square, 
  Paperclip, 
  X,
  FileText
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function InputArea({
  onSendMessage,
  isLoading,
  onOpenDocuments,
  documentCount = 0
}) {
  const [text, setText] = useState('');
  const [imageAttachment, setImageAttachment] = useState(null); // { base64, mimeType, preview, name }
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const speechRecognitionRef = useRef(null);
  const speechTranscriptRef = useRef('');
  const mediaStreamRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  // Handle Image Selection
  const handleImageFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please select a valid image file (PNG, JPG, WEBP).');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('Image file size must be less than 10MB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setImageAttachment({
        base64: reader.result,
        mimeType: file.type,
        preview: reader.result,
        name: file.name
      });
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleRemoveImage = () => {
    setImageAttachment(null);
  };

  // Audio Recording (Real-time Web Speech with Fast Gemini Fallback)
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];
      speechTranscriptRef.current = '';

      // 1. Instant Real-Time Streaming Dictation (Web Speech API)
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = navigator.language || 'en-US';

          const initialText = text;
          recognition.onresult = (event) => {
            let combined = '';
            for (let i = 0; i < event.results.length; ++i) {
              combined += event.results[i][0].transcript;
            }
            if (combined.trim()) {
              speechTranscriptRef.current = combined.trim();
              const prefix = initialText && !initialText.endsWith(' ') ? `${initialText} ` : initialText;
              setText(`${prefix}${combined.trim()}`);
            }
          };

          recognition.onerror = (e) => {
            console.warn('SpeechRecognition notice:', e.error);
          };

          recognition.start();
          speechRecognitionRef.current = recognition;
        } catch (e) {
          console.warn('Could not initialize SpeechRecognition:', e);
        }
      }

      // 2. Audio Stream Recording (For Gemini Backend Fallback)
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all audio tracks
        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
        }

        // If Web Speech already transcribed speech instantly, finish without extra API calls
        if (speechTranscriptRef.current && speechTranscriptRef.current.length > 0) {
          return;
        }

        // Fallback to high-speed Gemini audio transcription
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size < 500) return;

        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64Audio = reader.result;
          try {
            setIsTranscribing(true);
            const res = await apiClient.transcribeAudio(base64Audio, 'audio/webm');
            if (res?.text) {
              setText((prev) => (prev ? `${prev} ${res.text}` : res.text));
            }
          } catch (err) {
            console.error('Transcription error:', err);
            if (!text.trim()) {
              alert('Voice transcription failed. You can type your query directly.');
            }
          } finally {
            setIsTranscribing(false);
          }
        };
        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordDuration(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Unable to access microphone. Please grant microphone permissions in your browser.');
    }
  };

  const stopRecording = () => {
    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
      speechRecognitionRef.current = null;
    }

    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerIntervalRef.current);
    }
  };

  // Format seconds to MM:SS
  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remaining = secs % 60;
    return `${mins}:${remaining < 10 ? '0' : ''}${remaining}`;
  };

  // Submit message
  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed && !imageAttachment) return;
    if (isLoading) return;

    onSendMessage({
      message: trimmed || 'What is in this image?',
      image_base64: imageAttachment?.base64,
      image_mime_type: imageAttachment?.mimeType,
      image_preview: imageAttachment?.preview
    });

    setText('');
    setImageAttachment(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-area-wrapper">
      <div className="input-container">
        {/* Attached Image Preview */}
        {imageAttachment && (
          <div className="attachment-preview-box">
            <img 
              src={imageAttachment.preview} 
              alt="Attachment" 
              className="preview-thumb" 
            />
            <div className="preview-meta">
              <span className="preview-title">{imageAttachment.name}</span>
              <span className="preview-sub">Image attached for vision analysis</span>
            </div>
            <button 
              className="remove-attach-btn" 
              onClick={handleRemoveImage}
              title="Remove image"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Audio Recording Active Bar */}
        {isRecording && (
          <div className="recording-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div className="rec-pulse-dot" />
              <span style={{ fontSize: '0.86rem', fontWeight: 600, color: '#f43f5e' }}>
                Recording Audio...
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className="rec-timer">{formatTime(recordDuration)}</span>
              <button 
                className="action-pill-btn" 
                style={{ background: '#f43f5e', color: '#fff', border: 'none' }}
                onClick={stopRecording}
              >
                <Square size={12} fill="white" />
                <span>Finish</span>
              </button>
            </div>
          </div>
        )}

        {/* Transcribing indicator */}
        {isTranscribing && (
          <div style={{ fontSize: '0.8rem', color: 'var(--cyan-glow)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span>Transcribing speech to text with Gemini...</span>
          </div>
        )}

        {/* Input Bar */}
        <div className="input-main-row">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              imageAttachment 
                ? "Ask a question about this image..." 
                : isRecording
                ? "Listening... speak now"
                : "Type your message, ask about documents, or speak..."
            }
            disabled={isLoading}
          />

          <div className="input-actions-row">
            {/* Image Upload Button */}
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept="image/*"
              onChange={handleImageFileChange}
            />
            <button
              className="icon-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Attach image for vision analysis"
              disabled={isLoading || isRecording}
            >
              <ImageIcon size={18} />
            </button>

            {/* Document Manager trigger */}
            <button
              className="icon-btn"
              onClick={onOpenDocuments}
              title={`Open document knowledge base (${documentCount} indexed)`}
              disabled={isLoading || isRecording}
            >
              <FileText size={18} />
            </button>

            {/* Voice Recording Button */}
            {isRecording ? (
              <button
                className="icon-btn"
                style={{ color: 'var(--rose-glow)', borderColor: 'rgba(244, 63, 94, 0.4)' }}
                onClick={stopRecording}
                title="Stop recording"
              >
                <Square size={18} fill="currentColor" />
              </button>
            ) : (
              <button
                className="icon-btn"
                onClick={startRecording}
                title="Record speech to text"
                disabled={isLoading}
              >
                <Mic size={18} />
              </button>
            )}

            {/* Send Button */}
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={isLoading || (!text.trim() && !imageAttachment)}
              title="Send message"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
