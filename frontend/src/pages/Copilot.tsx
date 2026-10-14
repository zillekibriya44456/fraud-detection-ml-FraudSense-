import { useState, useRef, useEffect } from 'react';
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

const Copilot = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      text: "Hello! I am your FraudSense AI Intelligence Copilot. Ask me to scan payment URLs, analyze suspicious bank messages, verify UPI IDs, or explain why a transaction was flagged.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    soundManager.playEvent('copilot.opened');
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (userMsg?: string) => {
    const textToSend = userMsg || input;
    if (!textToSend.trim() || loading) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newMsg: Message = { sender: 'user', text: textToSend, timestamp: time };

    setMessages((prev) => [...prev, newMsg]);
    if (!userMsg) setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/v1/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend })
      });
      const data = await res.json();
      const botMsg: Message = {
        sender: 'bot',
        text: data.reply,
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
    <div className="copilot-page">
      <div className="copilot-header">
        <div className="flex-center gap-3">
          <div className="bot-avatar-large">
            <Zap size={22} className="icon-blue" />
          </div>
          <div>
            <h2>FraudSense AI Copilot</h2>
            <p>Conversational Security Assistant & Tool Execution Agent</p>
          </div>
        </div>
        <span className="badge badge-green font-mono">COPILOT ACTIVE</span>
      </div>

      <div className="glass-panel copilot-chat-container">
        <div className="chat-messages font-sans">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble-row ${m.sender}`}>
              <div className="avatar-box">
                {m.sender === 'bot' ? <Bot size={18} className="text-blue" /> : <User size={18} />}
              </div>
              <div className="message-content">
                <div className="msg-header">
                  <span className="msg-author">{m.sender === 'bot' ? 'FraudSense Copilot' : 'Analyst'}</span>
                  <span className="msg-time">{m.timestamp}</span>
                </div>
                <div className="msg-body">{m.text}</div>

                {m.tools && m.tools.length > 0 && (
                  <div className="tool-invocation-bar mt-2">
                    <Terminal size={12} className="text-purple" />
                    <span className="text-xs text-muted font-mono">Invoked Tools: {m.tools.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble-row bot">
              <div className="avatar-box"><Bot size={18} className="text-blue" /></div>
              <div className="message-content">
                <div className="msg-body flex-center gap-2 text-muted">
                  <RefreshCw size={14} className="spin" /> Executing Security Pipeline...
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* PROMPT SUGGESTIONS */}
        <div className="prompt-suggestions">
          <button className="prompt-btn" onClick={() => handleSend('Is this payment link safe? https://bank-verify.xyz/login')}>
            "Scan https://bank-verify.xyz/login"
          </button>
          <button className="prompt-btn" onClick={() => handleSend('Analyze this SMS: Your account will be blocked within 24h due to KYC.')}>
            "Analyze KYC SMS alert"
          </button>
          <button className="prompt-btn" onClick={() => handleSend('Why was transaction TX-90412 blocked?')}>
            "Explain TX-90412 block"
          </button>
        </div>

        {/* INPUT BOX */}
        <div className="chat-input-bar">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask Copilot or paste suspicious link/message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button className="btn-primary flex-center gap-2" onClick={() => handleSend()} disabled={loading}>
            <Send size={16} />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Copilot;
