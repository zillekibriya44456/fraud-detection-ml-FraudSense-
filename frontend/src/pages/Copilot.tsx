import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Bot, User, Send, Zap, Terminal, RefreshCw, Paperclip,
  X, FileText, Image, FileSpreadsheet, Mail, Upload,
  ChevronDown, Shield, ExternalLink,
  Trash2, CheckCircle, XCircle, Eye
} from 'lucide-react';
import './Copilot.css';
import { soundManager } from '../audio/soundManager';
import { API_BASE } from '../lib/apiClient';

/* ── Types ─────────────────────────────────────────────────────────────────── */

interface UploadedFile {
  id: string;
  file: File;
  preview?: string;
  status: 'pending' | 'uploading' | 'analyzing' | 'done' | 'error';
  progress: number;
  result?: AnalysisResult;
  error?: string;
}

interface AnalysisResult {
  analysis_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  category: string;
  status: string;
  summary: string;
  extracted_text?: string;
  extracted_urls: string[];
  extracted_transactions?: Record<string, string>[];
  scanner_results?: ScannerResult[];
  model_predictions?: Record<string, unknown>[];
  risk_level: string;
  risk_indicators: string[];
  evidence: string[];
  warnings: string[];
  recommendations: string[];
  metadata: Record<string, unknown>;
  analyzed_at: string;
}

interface ScannerResult {
  scanner: string;
  risk_level?: string;
  risk_score?: number;
  evidence?: string[];
  warnings?: string[];
  recommendation?: string;
  scam_category?: string;
  detected_phrases?: string[];
  [key: string]: unknown;
}

interface Message {
  sender: 'user' | 'bot';
  text: string;
  tools?: string[];
  riskAssessment?: Record<string, unknown>;
  timestamp: string;
  attachments?: UploadedFile[];
  analysisResult?: AnalysisResult;
}

/* ── Constants ─────────────────────────────────────────────────────────────── */

const INITIAL_MESSAGE: Message = {
  sender: 'bot',
  text: "Hello! I am your FraudSense AI Intelligence Copilot. Ask me to scan payment URLs, analyze suspicious bank messages, verify UPI IDs, or explain why a transaction was flagged.\n\n📎 **New:** You can now upload files for analysis — QR images, screenshots, PDFs, CSV/Excel transactions, and email evidence. Click the attachment button or drag & drop files into the chat.",
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
};

const ACCEPTED_TYPES: Record<string, { label: string; icon: React.ReactNode; extensions: string[] }> = {
  images: { label: 'QR & Payment Images', icon: <Image size={14} />, extensions: ['.png', '.jpg', '.jpeg', '.webp', '.tiff', '.tif'] },
  documents: { label: 'PDF & Financial Documents', icon: <FileText size={14} />, extensions: ['.pdf', '.txt', '.docx'] },
  data: { label: 'CSV & Excel Transactions', icon: <FileSpreadsheet size={14} />, extensions: ['.csv', '.xlsx', '.json'] },
  evidence: { label: 'SMS, Email & Phishing Evidence', icon: <Mail size={14} />, extensions: ['.eml'] },
};

const ALL_EXTENSIONS = Object.values(ACCEPTED_TYPES).flatMap(t => t.extensions);
const MAX_SIZE_MB = 25;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function riskBadgeClass(risk: string): string {
  const r = risk?.toUpperCase() || '';
  if (r === 'CRITICAL') return 'badge-red';
  if (r === 'HIGH') return 'badge-red';
  if (r === 'SUSPICIOUS') return 'badge-amber';
  if (r === 'LOW') return 'badge-green';
  if (r === 'NONE') return 'badge-green';
  return 'badge-blue';
}

function getFileCategory(file: File): string {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  for (const [, cat] of Object.entries(ACCEPTED_TYPES)) {
    if (cat.extensions.includes(ext)) return cat.label;
  }
  return 'Other Supported Documents';
}

/* ── Component ─────────────────────────────────────────────────────────────── */

const Copilot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [attachments, setAttachments] = useState<UploadedFile[]>([]);
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isFirstRender = useRef(true);
  const isUserScrolledUp = useRef(false);

  useEffect(() => { soundManager.playEvent('copilot.opened'); }, []);

  /* ── Scroll management ── */
  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    isUserScrolledUp.current = scrollHeight - scrollTop - clientHeight > 60;
  }, []);

  const scrollToBottom = useCallback((smooth = true) => {
    if (!messagesContainerRef.current) return;
    const container = messagesContainerRef.current;
    if (smooth) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    } else {
      container.scrollTop = container.scrollHeight;
    }
  }, []);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      scrollToBottom(false);
      return;
    }
    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.sender === 'user' || !isUserScrolledUp.current) {
      scrollToBottom(true);
    }
  }, [messages, scrollToBottom]);

  /* ── File validation ── */
  const validateFile = (file: File): string | null => {
    const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');
    if (!ALL_EXTENSIONS.includes(ext)) {
      return `Unsupported format: ${ext}. Accepted: ${ALL_EXTENSIONS.join(', ')}`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File too large (${formatBytes(file.size)}). Max: ${MAX_SIZE_MB} MB.`;
    }
    if (file.size === 0) {
      return 'File is empty.';
    }
    return null;
  };

  /* ── Add files ── */
  const addFiles = (files: FileList | File[]) => {
    const newAttachments: UploadedFile[] = [];
    Array.from(files).forEach(file => {
      const error = validateFile(file);
      const id = `file-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;

      let preview: string | undefined;
      if (file.type.startsWith('image/')) {
        preview = URL.createObjectURL(file);
      }

      newAttachments.push({
        id,
        file,
        preview,
        status: error ? 'error' : 'pending',
        progress: 0,
        error: error || undefined,
      });
    });
    setAttachments(prev => [...prev, ...newAttachments]);
    if (newAttachments.some(a => !a.error)) {
      setShowUploadPanel(true);
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => {
      const file = prev.find(a => a.id === id);
      if (file?.preview) URL.revokeObjectURL(file.preview);
      return prev.filter(a => a.id !== id);
    });
  };

  const clearAttachments = () => {
    attachments.forEach(a => { if (a.preview) URL.revokeObjectURL(a.preview); });
    setAttachments([]);
    setShowUploadPanel(false);
  };

  /* ── Drag & Drop ── */
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragOver(false); };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  /* ── Upload single file ── */
  const uploadFile = async (attachment: UploadedFile): Promise<AnalysisResult | null> => {
    setAttachments(prev => prev.map(a =>
      a.id === attachment.id ? { ...a, status: 'uploading', progress: 20 } : a
    ));

    try {
      const formData = new FormData();
      formData.append('file', attachment.file);
      formData.append('user_prompt', input || '');

      setAttachments(prev => prev.map(a =>
        a.id === attachment.id ? { ...a, progress: 50, status: 'analyzing' } : a
      ));

      const res = await fetch(`${API_BASE}/v1/copilot/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(errData.detail || `Upload failed: ${res.status}`);
      }

      const result: AnalysisResult = await res.json();

      setAttachments(prev => prev.map(a =>
        a.id === attachment.id ? { ...a, status: 'done', progress: 100, result } : a
      ));

      return result;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setAttachments(prev => prev.map(a =>
        a.id === attachment.id ? { ...a, status: 'error', error: msg } : a
      ));
      return null;
    }
  };

  /* ── Send message + uploads ── */
  const handleSend = async (userMsg?: string) => {
    const textToSend = userMsg || input;
    const pendingFiles = attachments.filter(a => a.status === 'pending');
    if (!textToSend.trim() && pendingFiles.length === 0) return;
    if (loading) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgText = textToSend.trim()
      || (pendingFiles.length > 0
        ? `Analyze ${pendingFiles.length} uploaded file(s)`
        : '');

    const newMsg: Message = {
      sender: 'user',
      text: msgText,
      timestamp: time,
      attachments: pendingFiles.length > 0 ? [...pendingFiles] : undefined,
    };

    setMessages(prev => [...prev, newMsg]);
    if (!userMsg) setInput('');
    setLoading(true);
    isUserScrolledUp.current = false;

    // Upload files first
    if (pendingFiles.length > 0) {
      const results: AnalysisResult[] = [];
      for (const file of pendingFiles) {
        const result = await uploadFile(file);
        if (result) results.push(result);
      }

      if (results.length > 0) {
        for (const result of results) {
          const botMsg: Message = {
            sender: 'bot',
            text: _buildAnalysisSummary(result),
            tools: _getToolsUsed(result),
            analysisResult: result,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
          setMessages(prev => [...prev, botMsg]);
        }
        soundManager.playEvent('copilot.response_complete');
      } else {
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: 'File analysis failed. Please check the file format and try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }]);
        soundManager.playEvent('copilot.error');
      }

      clearAttachments();
    }

    // If the user provided text (either standalone or along with uploaded files), query Copilot
    if (textToSend.trim()) {
      try {
        const res = await fetch(`${API_BASE}/v1/copilot/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: textToSend }),
        });
        const data = await res.json();
        const botMsg: Message = {
          sender: 'bot',
          text: data.reply || 'Analysis complete.',
          tools: data.recommended_tools,
          riskAssessment: data.risk_assessment,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages(prev => [...prev, botMsg]);
        soundManager.playEvent('copilot.response_complete');
      } catch {
        if (pendingFiles.length === 0) {
          soundManager.playEvent('copilot.error');
          setMessages(prev => [...prev, {
            sender: 'bot',
            text: 'I experienced a network error connecting to the FraudSense AI engine. Please retry.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }]);
        }
      }
    }

    setLoading(false);
  };

  /* ── Result formatting helpers ── */
  function _buildAnalysisSummary(r: AnalysisResult): string {
    const lines: string[] = [];
    lines.push(`📄 **${r.filename}** — ${r.category}`);
    lines.push(`📊 **Risk Level:** ${r.risk_level} | Status: ${r.status}`);
    lines.push('');

    if (r.evidence.length > 0) {
      lines.push('**Evidence:**');
      r.evidence.slice(0, 8).forEach(e => lines.push(`  ✅ ${e}`));
    }

    if (r.warnings.length > 0) {
      lines.push('');
      lines.push('**⚠️ Warnings:**');
      r.warnings.slice(0, 8).forEach(w => lines.push(`  ⚠️ ${w}`));
    }

    if (r.recommendations.length > 0) {
      lines.push('');
      lines.push('**Recommendations:**');
      r.recommendations.slice(0, 5).forEach(rec => lines.push(`  → ${rec}`));
    }

    if (r.scanner_results && r.scanner_results.length > 0) {
      lines.push('');
      lines.push('**🔍 Scanner Results:**');
      r.scanner_results.forEach(s => {
        lines.push(`  • ${s.scanner}: ${s.risk_level || s.scam_category || 'completed'}`);
      });
    }

    lines.push('');
    lines.push(`_Analysis ID: ${r.analysis_id} | ${formatBytes(r.file_size_bytes)} | ${new Date(r.analyzed_at).toLocaleString()}_`);

    return lines.join('\n');
  }

  function _getToolsUsed(r: AnalysisResult): string[] {
    const tools: string[] = [];
    if (r.scanner_results) {
      r.scanner_results.forEach(s => {
        if (s.scanner.includes('URL')) tools.push('url_scanner');
        if (s.scanner.includes('QR')) tools.push('qr_scanner');
        if (s.scanner.includes('Scam')) tools.push('scam_analyzer');
      });
    }
    if (r.file_type === '.pdf') tools.push('pdf_extractor');
    if (['.csv', '.xlsx'].includes(r.file_type)) tools.push('data_analyzer');
    if (r.file_type === '.eml') tools.push('email_parser');
    if (r.metadata?.qr_type) tools.push('qr_decoder');
    return [...new Set(tools)];
  }

  const toggleExpand = (id: string) => {
    setExpandedResults(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  /* ── Render ──────────────────────────────────────────────────────────────── */
  return (
    <div
      className={`copilot-page ${isDragOver ? 'drag-over' : ''}`}
      role="region"
      aria-label="FraudSense AI Copilot Chat"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header */}
      <div className="copilot-header">
        <div className="flex-center gap-3">
          <div className="bot-avatar-large" aria-hidden="true">
            <Zap size={22} className="icon-blue" />
          </div>
          <div>
            <h2>FraudSense AI Copilot</h2>
            <p className="copilot-subtitle">Conversational Security Assistant &amp; Document Intelligence Agent</p>
          </div>
        </div>
        <span className="badge badge-green font-mono copilot-status-badge">COPILOT ACTIVE</span>
      </div>

      {/* Drag overlay */}
      {isDragOver && (
        <div className="drag-overlay">
          <div className="drag-overlay-content">
            <Upload size={48} />
            <p>Drop files here for analysis</p>
            <span className="text-xs text-muted">Images, PDFs, CSV, Excel, Email files</span>
          </div>
        </div>
      )}

      {/* Main Chat Panel */}
      <div className="glass-panel copilot-chat-container">
        {/* Messages */}
        <div
          className="chat-messages font-sans"
          ref={messagesContainerRef}
          onScroll={handleScroll}
          aria-live="polite"
          aria-atomic="false"
        >
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble-row ${m.sender}`}>
              <div className="avatar-box" aria-hidden="true">
                {m.sender === 'bot' ? <Bot size={18} className="text-blue" /> : <User size={18} />}
              </div>
              <div className="message-content">
                <div className="msg-header">
                  <span className="msg-author">{m.sender === 'bot' ? 'FraudSense Copilot' : 'Analyst'}</span>
                  <span className="msg-time">{m.timestamp}</span>
                </div>
                <div className="msg-body">{m.text}</div>

                {/* Attachments preview on user messages */}
                {m.attachments && m.attachments.length > 0 && (
                  <div className="msg-attachments">
                    {m.attachments.map(a => (
                      <div key={a.id} className="msg-attachment-chip">
                        <Paperclip size={12} />
                        <span>{a.file.name}</span>
                        <span className="text-xs text-muted">{formatBytes(a.file.size)}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Analysis Result Card (expandable) */}
                {m.analysisResult && (
                  <div className={`analysis-result-card risk-${m.analysisResult.risk_level.toLowerCase()}`}>
                    <div className="arc-header" onClick={() => toggleExpand(m.analysisResult!.analysis_id)}>
                      <div className="arc-title-row">
                        <Shield size={16} />
                        <span className="arc-filename">{m.analysisResult.filename}</span>
                        <span className={`badge ${riskBadgeClass(m.analysisResult.risk_level)}`}>
                          {m.analysisResult.risk_level}
                        </span>
                      </div>
                      <ChevronDown
                        size={16}
                        className={`arc-chevron ${expandedResults.has(m.analysisResult.analysis_id) ? 'rotated' : ''}`}
                      />
                    </div>

                    {expandedResults.has(m.analysisResult.analysis_id) && (
                      <div className="arc-details">
                        {/* Extracted URLs */}
                        {m.analysisResult.extracted_urls.length > 0 && (
                          <div className="arc-section">
                            <h5><ExternalLink size={13} /> Extracted URLs</h5>
                            <ul className="arc-url-list">
                              {m.analysisResult.extracted_urls.slice(0, 10).map((url, j) => (
                                <li key={j} className="font-mono text-xs">{url}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Extracted transactions preview */}
                        {m.analysisResult.extracted_transactions && m.analysisResult.extracted_transactions.length > 0 && (
                          <div className="arc-section">
                            <h5><FileSpreadsheet size={13} /> Data Preview ({m.analysisResult.metadata?.total_rows as number || '?'} rows)</h5>
                            <div className="arc-table-wrapper">
                              <table className="arc-table">
                                <thead>
                                  <tr>
                                    {Object.keys(m.analysisResult.extracted_transactions[0]).slice(0, 6).map(k => (
                                      <th key={k}>{k}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {m.analysisResult.extracted_transactions.slice(0, 3).map((row, ri) => (
                                    <tr key={ri}>
                                      {Object.values(row).slice(0, 6).map((v, ci) => (
                                        <td key={ci} className="font-mono">{String(v).slice(0, 30)}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Extracted text preview */}
                        {m.analysisResult.extracted_text && (
                          <div className="arc-section">
                            <h5><Eye size={13} /> Extracted Text</h5>
                            <pre className="arc-text-preview">
                              {m.analysisResult.extracted_text.slice(0, 800)}
                              {m.analysisResult.extracted_text.length > 800 && '...'}
                            </pre>
                          </div>
                        )}

                        {/* Scanner results */}
                        {m.analysisResult.scanner_results && m.analysisResult.scanner_results.length > 0 && (
                          <div className="arc-section">
                            <h5><Shield size={13} /> Scanner Reports</h5>
                            {m.analysisResult.scanner_results.map((sr, si) => (
                              <div key={si} className="arc-scanner-report">
                                <div className="arc-sr-header">
                                  <span className="font-mono text-xs">{sr.scanner}</span>
                                  {sr.risk_level && (
                                    <span className={`badge ${riskBadgeClass(sr.risk_level)}`}>{sr.risk_level}</span>
                                  )}
                                </div>
                                {sr.recommendation && (
                                  <p className="text-xs text-muted">{sr.recommendation}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Metadata */}
                        <div className="arc-section arc-meta-row">
                          <span className="text-xs text-muted font-mono">
                            ID: {m.analysisResult.analysis_id} · {formatBytes(m.analysisResult.file_size_bytes)} · {m.analysisResult.file_type} ·{' '}
                            {(m.analysisResult.metadata?.processing_ms as number)?.toFixed(0) || '?'}ms
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tool invocations */}
                {m.tools && m.tools.length > 0 && (
                  <div className="tool-invocation-bar">
                    <Terminal size={12} className="text-purple" />
                    <span className="text-xs text-muted font-mono">Invoked Tools: {m.tools.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-bubble-row bot">
              <div className="avatar-box" aria-hidden="true"><Bot size={18} className="text-blue" /></div>
              <div className="message-content">
                <div className="msg-body flex-center gap-2 text-muted">
                  <RefreshCw size={14} className="spin" /> Executing Security Pipeline...
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Upload Panel (expanded) */}
        {showUploadPanel && (
          <div className="upload-panel">
            <div className="upload-panel-header">
              <h4><Paperclip size={14} /> Attachments ({attachments.length})</h4>
              <div className="upload-panel-actions">
                <button className="icon-btn" title="Clear all" onClick={clearAttachments}><Trash2 size={14} /></button>
                <button className="icon-btn" title="Close" onClick={() => setShowUploadPanel(false)}><X size={14} /></button>
              </div>
            </div>

            <div className="upload-file-list">
              {attachments.map(a => (
                <div key={a.id} className={`upload-file-item status-${a.status}`}>
                  <div className="ufi-icon">
                    {a.preview ? (
                      <img src={a.preview} alt="" className="ufi-thumb" />
                    ) : (
                      <FileText size={18} />
                    )}
                  </div>
                  <div className="ufi-info">
                    <span className="ufi-name">{a.file.name}</span>
                    <span className="ufi-meta text-xs text-muted">
                      {formatBytes(a.file.size)} · {getFileCategory(a.file)}
                    </span>
                    {a.error && <span className="ufi-error text-xs">{a.error}</span>}
                  </div>
                  <div className="ufi-status">
                    {a.status === 'pending' && <span className="badge badge-blue">Ready</span>}
                    {a.status === 'uploading' && <RefreshCw size={14} className="spin text-blue" />}
                    {a.status === 'analyzing' && <RefreshCw size={14} className="spin text-amber" />}
                    {a.status === 'done' && <CheckCircle size={14} className="text-green" />}
                    {a.status === 'error' && <XCircle size={14} className="text-red" />}
                  </div>
                  <button className="icon-btn ufi-remove" onClick={() => removeAttachment(a.id)} title="Remove">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>

            {/* Accepted formats hint */}
            <div className="upload-formats-hint">
              {Object.values(ACCEPTED_TYPES).map((cat, i) => (
                <span key={i} className="format-chip" title={cat.extensions.join(', ')}>
                  {cat.icon} {cat.label}
                </span>
              ))}
              <span className="text-xs text-muted">Max {MAX_SIZE_MB} MB per file</span>
            </div>
          </div>
        )}

        {/* Prompt Suggestions */}
        <div className="prompt-suggestions" aria-label="Suggested Prompts">
          <button type="button" className="prompt-btn"
            onClick={() => handleSend('Is this payment link safe? https://bank-verify.xyz/login')}>
            "Scan https://bank-verify.xyz/login"
          </button>
          <button type="button" className="prompt-btn"
            onClick={() => handleSend('Analyze this SMS: Your account will be blocked within 24h due to KYC.')}>
            "Analyze KYC SMS alert"
          </button>
          <button type="button" className="prompt-btn"
            onClick={() => fileInputRef.current?.click()}>
            📎 Upload a file for analysis
          </button>
        </div>

        {/* Input Bar */}
        <div className="chat-input-bar">
          <button
            type="button"
            className={`attach-btn ${attachments.length > 0 ? 'has-files' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            title="Attach files"
            disabled={loading}
          >
            <Paperclip size={18} />
            {attachments.filter(a => a.status === 'pending').length > 0 && (
              <span className="attach-count">{attachments.filter(a => a.status === 'pending').length}</span>
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ALL_EXTENSIONS.join(',')}
            style={{ display: 'none' }}
            onChange={e => { if (e.target.files) addFiles(e.target.files); e.target.value = ''; }}
          />
          <input
            type="text"
            className="chat-input"
            placeholder={attachments.length > 0 ? 'Add a note about the files (optional)...' : 'Ask Copilot or paste suspicious link/message...'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            aria-label="Ask Copilot or paste suspicious link"
            disabled={loading}
          />
          <button
            type="button"
            className="btn-primary flex-center gap-2 chat-send-btn"
            onClick={() => handleSend()}
            disabled={loading || (!input.trim() && attachments.filter(a => a.status === 'pending').length === 0)}
            aria-label="Send message to Copilot"
          >
            {attachments.filter(a => a.status === 'pending').length > 0
              ? <><Upload size={16} /><span>Analyze</span></>
              : <><Send size={16} /><span>Send</span></>
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default Copilot;
