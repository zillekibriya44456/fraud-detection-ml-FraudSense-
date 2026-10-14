import { useState } from 'react';
import { MessageSquare, AlertTriangle, RefreshCw, Send } from 'lucide-react';
import './ScamAnalyzer.css';
import { soundManager } from '../audio/soundManager';

interface TextResult {
  scam_category: string;
  risk_level: string;
  risk_score: number;
  detected_phrases: string[];
  urgency_detected: boolean;
  financial_request: boolean;
  recommendation: string;
}

const ScamAnalyzer = () => {
  const [inputText, setInputText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<TextResult | null>(null);

  const handleAnalyze = async (sample?: string) => {
    const textToScan = sample || inputText;
    if (!textToScan.trim()) return;

    soundManager.playEvent('sms.started');
    setAnalyzing(true);
    setResult(null);

    try {
      const res = await fetch('/api/v1/scans/sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToScan }),
      });
      const data = await res.json();
      setResult(data);

      const r = (data.risk_level || '').toUpperCase();
      if (r === 'CRITICAL') soundManager.playEvent('sms.critical_risk');
      else if (r === 'HIGH') soundManager.playEvent('sms.high_risk');
      else if (r === 'SUSPICIOUS' || r === 'MEDIUM') soundManager.playEvent('sms.medium_risk');
      else soundManager.playEvent('sms.low_risk');
    } catch {
      soundManager.playEvent('transaction.failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="scam-analyzer-page">
      <div className="analyzer-header">
        <div>
          <h2>SMS, Email & Scam Conversation Analyzer</h2>
          <p>Scans messages, emails, social engineering scripts, and screenshot text for credential harvesting and financial fraud signals.</p>
        </div>
      </div>

      <div className="scam-grid">
        <div className="glass-panel text-input-card">
          <div className="card-title">
            <MessageSquare size={20} className="icon-purple" />
            <h3>Paste Message / Email / Chat Text</h3>
          </div>

          <textarea
            className="scam-textarea font-mono"
            rows={7}
            placeholder="Paste suspicious SMS, email, or chat conversation here..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />

          <div className="scam-actions">
            <button className="btn-primary flex-center gap-2" onClick={() => handleAnalyze()} disabled={analyzing}>
              {analyzing ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
              <span>{analyzing ? 'Analyzing NLP Signals...' : 'Analyze Message'}</span>
            </button>
          </div>

          <div className="sample-box">
            <span className="text-xs text-muted">PRESET TEST SCENARIOS:</span>
            <div className="sample-buttons mt-2">
              <button className="sample-btn" onClick={() => { setInputText('URGENT: Your Bank account has been suspended due to pending KYC verification. Click http://bank-kyc-verify.top immediately or your account will be blocked within 24 hours.'); handleAnalyze('URGENT: Your Bank account has been suspended due to pending KYC verification. Click http://bank-kyc-verify.top immediately or your account will be blocked within 24 hours.'); }}>
                Fake KYC Suspension SMS
              </button>
              <button className="sample-btn" onClick={() => { setInputText('Congratulations! You won $5,000 in cashback. Verify your 6-digit OTP 849201 to claim reward instantly.'); handleAnalyze('Congratulations! You won $5,000 in cashback. Verify your 6-digit OTP 849201 to claim reward instantly.'); }}>
                OTP Reward Scam
              </button>
            </div>
          </div>
        </div>

        {result && (
          <div className="glass-panel text-result-card">
            <div className="res-header flex-between">
              <div>
                <span className="text-xs text-muted font-mono">SCAM CLASSIFICATION</span>
                <h3 className="font-mono text-blue">{result.scam_category}</h3>
              </div>
              <span className={`badge ${result.risk_level === 'CRITICAL' || result.risk_level === 'HIGH' ? 'badge-red' : result.risk_level === 'SUSPICIOUS' ? 'badge-amber' : 'badge-green'}`}>
                {result.risk_level} RISK ({(result.risk_score * 100).toFixed(0)}%)
              </span>
            </div>

            <div className="advisory-banner mt-3">
              <strong>SAFETY ACTION:</strong> {result.recommendation}
            </div>

            <div className="flagged-signals mt-4">
              <h4>Flagged NLP Risk Markers</h4>
              <ul className="signals-list mt-2">
                {result.detected_phrases.map((p, i) => (
                  <li key={i}><AlertTriangle size={14} className="text-amber" /> {p}</li>
                ))}
                {result.urgency_detected && (
                  <li><AlertTriangle size={14} className="text-red" /> High-pressure urgency tactic detected</li>
                )}
                {result.financial_request && (
                  <li><AlertTriangle size={14} className="text-red" /> Unsolicited financial payout or credential request</li>
                )}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScamAnalyzer;
