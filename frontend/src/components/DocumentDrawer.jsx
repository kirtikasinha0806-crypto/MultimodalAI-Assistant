import React, { useState, useRef } from 'react';
import { 
  X, 
  UploadCloud, 
  FileText, 
  Trash2, 
  Edit3, 
  Check, 
  Layers, 
  AlertCircle,
  FileCode,
  Eye
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function DocumentDrawer({
  isOpen,
  onClose,
  documents,
  currentConvId,
  onConversationCreated,
  onRefreshDocuments
}) {
  const [isUploading, setIsUploading] = useState(false);
  const [editingDocId, setEditingDocId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [viewingChunksDoc, setViewingChunksDoc] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  // Upload handler scoped to this conversation
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowed = [
      '.pdf', '.docx', '.doc', '.txt', '.md', '.csv', '.json',
      '.xlsx', '.xls', '.pptx', '.ppt', '.py', '.js', '.ts',
      '.html', '.css', '.xml', '.yaml', '.yml', '.rtf', '.log'
    ];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setUploadError(`Unsupported format "${ext}". Supported: PDF, Word, Excel, PPTX, CSV, JSON, MD, Code & Text.`);
      return;
    }

    try {
      setIsUploading(true);
      setUploadError('');

      let targetConvId = currentConvId;
      if (!targetConvId) {
        // Automatically create a dedicated conversation for this document
        const cleanTitle = file.name.replace(/\.[^/.]+$/, "");
        const newConv = await apiClient.createConversation(cleanTitle);
        targetConvId = newConv.id;
        if (onConversationCreated) {
          onConversationCreated(newConv.id);
        }
      }

      await apiClient.uploadDocument(file, null, targetConvId);
      await onRefreshDocuments(targetConvId);
    } catch (err) {
      console.error('Upload failed:', err);
      setUploadError(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  // Delete handler
  const handleDelete = async (docId) => {
    if (!window.confirm('Delete this document and all associated pgvector embeddings?')) {
      return;
    }
    try {
      await apiClient.deleteDocument(docId);
      await onRefreshDocuments();
    } catch (err) {
      alert('Failed to delete document: ' + err.message);
    }
  };

  // Open Edit Mode
  const startEdit = async (doc) => {
    setEditingDocId(doc.id);
    setEditTitle(doc.title);
    setEditContent('');
    try {
      const details = await apiClient.getDocument(doc.id);
      if (details?.chunks?.length > 0) {
        setEditContent(details.chunks.map(c => c.content).join('\n\n'));
      }
    } catch (err) {
      console.error('Failed to load doc content for editing:', err);
    }
  };

  // Save Edit (re-chunks and re-embeds)
  const saveEdit = async (docId) => {
    try {
      await apiClient.updateDocument(docId, {
        title: editTitle,
        content: editContent
      });
      setEditingDocId(null);
      await onRefreshDocuments();
    } catch (err) {
      alert('Failed to update document: ' + err.message);
    }
  };

  // View Chunks Modal / Section
  const handleViewChunks = async (docId) => {
    if (viewingChunksDoc?.id === docId) {
      setViewingChunksDoc(null);
      return;
    }
    try {
      const details = await apiClient.getDocument(docId);
      setViewingChunksDoc(details);
    } catch (err) {
      alert('Failed to load chunks: ' + err.message);
    }
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-title">
            <FileText size={20} color="#818cf8" />
            <span>Document Knowledge Base (RAG)</span>
          </div>
          <button className="icon-btn" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          {/* Upload Dropzone */}
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".pdf,.docx,.doc,.txt,.md,.csv,.json,.xlsx,.xls,.pptx,.ppt,.py,.js,.ts,.html,.css,.xml,.yaml,.yml,.rtf,.log"
            onChange={handleFileUpload}
          />
          <div 
            className="dropzone"
            onClick={() => !isUploading && fileInputRef.current?.click()}
          >
            <UploadCloud className="dropzone-icon" />
            <div className="dropzone-text">
              {isUploading ? "Extracting, chunking & indexing into pgvector..." : "Click to upload document"}
            </div>
            <div className="dropzone-sub">
              Supported formats: PDF, Word (DOCX/DOC), Excel (XLSX), PowerPoint (PPTX), CSV, JSON, Markdown, Code & Text
            </div>
          </div>

          {uploadError && (
            <div style={{ color: 'var(--rose-glow)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <AlertCircle size={14} />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Document List Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              DOCUMENTS IN THIS CHAT ({documents.length})
            </span>
          </div>

          {/* Document Cards */}
          <div className="doc-list">
            {documents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                No documents uploaded in this chat. Documents you upload here stay strictly private to this conversation and will never leak into other chats.
              </div>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="doc-card">
                  <div className="doc-card-top">
                    <div className="doc-info">
                      <div className="doc-type-icon">
                        <FileCode size={16} />
                      </div>
                      <div>
                        <div className="doc-title-text" title={doc.title}>
                          {doc.title}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {doc.filename}
                        </div>
                      </div>
                    </div>
                    <span className={`doc-status-badge ${doc.status}`}>
                      {doc.status}
                    </span>
                  </div>

                  {/* Edit Mode Inline */}
                  {editingDocId === doc.id ? (
                    <div className="edit-doc-box">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        placeholder="Document title"
                        style={{
                          background: 'var(--bg-surface-elevated)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '6px',
                          padding: '0.4rem 0.6rem',
                          fontSize: '0.84rem'
                        }}
                      />
                      <textarea
                        className="edit-textarea"
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        placeholder="Document text content (saving will re-chunk and regenerate vectors)"
                      />
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <button className="doc-btn" onClick={() => setEditingDocId(null)}>
                          Cancel
                        </button>
                        <button 
                          className="doc-btn" 
                          style={{ background: 'var(--primary-500)', color: '#fff', border: 'none' }}
                          onClick={() => saveEdit(doc.id)}
                        >
                          <Check size={12} />
                          <span>Save & Re-Index</span>
                        </button>
                      </div>
                    </div>
                  ) : null}

                  {/* Chunks Inspection View */}
                  {viewingChunksDoc?.id === doc.id && (
                    <div style={{ background: '#0a0e18', padding: '0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}>
                      <div style={{ fontWeight: 600, color: '#818cf8', marginBottom: '0.4rem' }}>
                        Indexed Chunks ({viewingChunksDoc.chunks?.length || 0}):
                      </div>
                      <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        {viewingChunksDoc.chunks?.map((ch) => (
                          <div key={ch.id} style={{ background: 'rgba(255,255,255,0.04)', padding: '0.4rem', borderRadius: '4px' }}>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Section #{ch.chunk_index + 1}</div>
                            <div style={{ color: 'var(--text-secondary)' }}>{ch.content}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="doc-meta-row">
                    <span>
                      <Layers size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      {doc.chunk_count} vector chunks
                    </span>
                    <div className="doc-actions">
                      <button 
                        className="doc-btn" 
                        onClick={() => handleViewChunks(doc.id)} 
                        title="View chunks"
                      >
                        <Eye size={12} />
                        <span>{viewingChunksDoc?.id === doc.id ? 'Hide' : 'Chunks'}</span>
                      </button>
                      <button 
                        className="doc-btn" 
                        onClick={() => startEdit(doc)} 
                        title="Edit and re-index"
                      >
                        <Edit3 size={12} />
                        <span>Edit</span>
                      </button>
                      <button 
                        className="doc-btn delete" 
                        onClick={() => handleDelete(doc.id)} 
                        title="Delete document and vectors"
                      >
                        <Trash2 size={12} />
                        <span>Delete</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
