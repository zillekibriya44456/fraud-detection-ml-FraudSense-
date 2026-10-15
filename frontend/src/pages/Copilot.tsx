import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, User, Send, Zap, Terminal, RefreshCw } from 'lucide-react';
import './Copilot.css';
import { soundManager } from '../audio/soundManager';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  tools?: string[];
  riskAssessment?: any;
  timestamp: string;
}

const INITIAL_MESSAGE: Message = {
  sender: 'bot',
  text: "Hello! I am your FraudSense AI Intelligence Copilot. Ask me to scan payment URLs, analyze suspicious bank messages, verify UPI IDs, or explain why a transaction was flagged.",
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
};

const Copilot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isFirstRender = useRef(true);
  const isUserScrolledUp = useRef(false);

  // Sound effect on mount
  useEffect(() => {
    soundManager.playEvent('copilot.opened');
  }, []);

  // Track if user manually scrolled up
  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    // Consider scrolled up if more than 60px away from bottom
    isUserScrolledUp.current = scrollHeight - scrollTop - clientHeight > 60;
  }, []);

  // Safe internal scroll — scrolls ONLY the chat container, NEVER outer window or main layout
  const scrollToBottom = useCallback((smooth = true) => {
    if (!messagesContainerRef.current) return;
    const container = messagesContainerRef.current;
    if (smooth) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    } else {
      container.scrollTop = container.scrollHeight;
    }
  }, []);

  // Controlled scroll when messages change
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      // Immediate scroll inside chat container without animation to avoid page jump
      scrollToBottom(false);
      return;
    }

    const lastMsg = messages[messages.length - 1];
    // Always scroll if user sent the message, or if user is near bottom
    if (lastMsg?.sender === 'user' || !isUserScrolledUp.current) {
      scrollToBottom(true);
    }
  }, [messages, scrollToBottom]);

  const handleSend = async (userMsg?: string) => {
    const textToSend = userMsg || input;
    if (!textToSend.trim() || loading) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newMsg: Message = { sender: 'user', text: textToSend, timestamp: time };

    setMessages((prev) => [...prev, newMsg]);
    if (!userMsg) setInput('');
    setLoading(true);
    isUserScrolledUp.current = false;

    try {
      const res = await fetch('/api/v1/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend })
      });
      const data = await res.json();
      const botMsg: Message = {
        sender: 'bot',
        text: data.reply || "Analysis complete.",
        tools: data.recommended_tools,
        riskAssessment: data.risk_assessment,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
      soundManager.playEvent('copilot.response_complete');
    } catch {
      soundManager.playEvent('copilot.error');
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: "I experienced a network error connecting to the FraudSense AI engine. Please retry.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="copilot-page" role="region" aria-label="FraudSense AI Copilot Chat">
      {/* Header */}
      <div className="copilot-header">
        <div className="flex-center gap-3">
          <div className="bot-avatar-large" aria-hidden="true">
            <Zap size={22} className="icon-blue" />
          </div>
          <div>
            <h2>FraudSense AI Copilot</h2>
            <p className="copilot-subtitle">Conversational Security Assistant &amp; Tool Execution Agent</p>
          </div>
        </div>
        <span className="badge badge-green font-mono copilot-status-badge">COPILOT ACTIVE</span>
      </div>

      {/* Main Chat Panel */}
      <div className="glass-panel copilot-chat-container">
        {/* Messages List */}
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

        {/* Prompt Suggestions */}
        <div className="prompt-suggestions" aria-label="Suggested Prompts">
          <button
            type="button"
            className="prompt-btn"
            onClick={() => handleSend('Is this payment link safe? https://bank-verify.xyz/login')}
          >
            "Scan https://bank-verify.xyz/login"
          </button>
          <button
            type="button"
            className="prompt-btn"
            onClick={() => handleSend('Analyze this SMS: Your account will be blocked within 24h due to KYC.')}
          >
            "Analyze KYC SMS alert"
          </button>
          <button
            type="button"
            className="prompt-btn"
            onClick={() => handleSend('Why was transaction TX-90412 blocked?')}
          >
            "Explain TX-90412 block"
          </button>
        </div>

        {/* Input Bar */}
        <div className="chat-input-bar">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask Copilot or paste suspicious link/message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            aria-label="Ask Copilot or paste suspicious link"
            disabled={loading}
          />
          <button
            type="button"
            className="btn-primary flex-center gap-2 chat-send-btn"
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            aria-label="Send message to Copilot"
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Copilot;
