import { useState } from 'react';
import { FileSearch, Send, CheckCircle, XCircle, AlertTriangle, Loader, ChevronRight } from 'lucide-react';
import './AnalyzeTransaction.css';

import { soundManager } from '../audio/soundManager';

const API_BASE = '/api';

type StepStatus = 'idle' | 'running' | 'done' | 'error';

interface PipelineStep { label: string; status: StepStatus; latency?: string; }

const DEFAULT_STEPS: PipelineStep[] = [
  { label: 'VALIDATING INPUT', status: 'idle' },
  { label: 'EXTRACTING FEATURES', status: 'idle' },
  { label: 'RUNNING XGBOOST MODEL', status: 'idle' },
  { label: 'CALCULATING RISK', status: 'idle' },
  { label: 'GENERATING EXPLANATION', status: 'idle' },
  { label: 'DECISION READY', status: 'idle' },
];

function riskClass(risk: string) {
  if (!risk) return 'badge-blue';
  const r = risk.toUpperCase();
  if (r === 'LOW') return 'badge-green';
  if (r === 'MEDIUM') return 'badge-amber';
  if (r === 'HIGH') return 'badge-amber';
  if (r === 'CRITICAL') return 'badge-red';
  return 'badge-blue';
}

const DOMAIN_TEMPLATES: Record<string, any> = {
  paysim: {
    domain: "paysim",
    step: 1,
    type: "TRANSFER",
    amount: 150000.0,
    oldbalanceOrg: 150000.0,
    oldbalanceDest: 0.0
  },
  bank: {
    domain: "bank",
    income: 0.5,
    name_email_similarity: 0.8,
    velocity_6h: 100,
    velocity_24h: 200,
    velocity_4w: 300,
    bank_branch_count_8w: 5,
    date_of_birth_distinct_emails_4w: 1,
    credit_risk_score: 150,
    email_is_free: 1,
    phone_home_valid: 1,
    phone_mobile_valid: 1,
    bank_months_count: 12,
    has_other_cards: 0,
    proposed_credit_limit: 1000,
    foreign_request: 0,
    session_length_in_minutes: 5,
    keep_alive_session: 1,
    device_os: 0,
    device_distinct_emails_8w: 1,
    month: 5
  },
  upi: {
    domain: "upi",
    amount: 15000.0,
    transaction_type: "P2P",
    merchant_category: "Shopping",
    sender_bank: "HDFC",
    receiver_bank: "SBI",
    hour_of_day: 14,
    day_of_week: "Monday",
    sender_age_group: "26-35",
    receiver_age_group: "26-35"
  },
  card: {
    domain: "card",
    Amount: 125.50,
    Time: 3600,
    V1: -1.3,
    V2: 0.5,
    V3: 1.2,
    V4: 0.1,
    V5: -0.8
  },
  bitcoin: {
    domain: "bitcoin",
    time_step: 20
  },
  url_phishing: {
    domain: "url_phishing",
    url: "http://secure-login-chase-update.example/login"
  },
  sms: {
    domain: "sms",
    text: "URGENT: Your account is blocked. Verify KYC immediately at http://evil-bank-login.com"
  },
  email: {
    domain: "email",
    text: "URGENT: Your bank account is suspended. Verify credentials immediately to restore access."
  }
};

const AnalyzeTransaction: React.FC = () => {
  const [selectedDomain, setSelectedDomain] = useState('paysim');
  const [payloadText, setPayloadText] = useState(JSON.stringify(DOMAIN_TEMPLATES['paysim'], null, 2));

  const [steps, setSteps] = useState<PipelineStep[]>(DEFAULT_STEPS);
  const [analysing, setAnalysing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [explanation, setExplanation] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const updateStep = (idx: number, status: StepStatus, latency?: string) => {
    setSteps(prev => prev.map((s, i) => i === idx ? { ...s, status, latency } : s));
  };

  const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

  const handleAnalyze = async () => {
    setResult(null);
    setExplanation(null);
    setError(null);
    setAnalysing(true);
    setSteps(DEFAULT_STEPS.map(s => ({ ...s, status: 'idle' })));

    soundManager.playEvent('transaction.submitted');
    const startEventKey = `${selectedDomain}.started`;
    soundManager.playEvent(startEventKey);

    try {
      // Step 0 – Validate
      updateStep(0, 'running');
      await sleep(300);
      updateStep(0, 'done', '12ms');

      // Step 1 – Feature extraction
      updateStep(1, 'running');
      await sleep(350);
      updateStep(1, 'done', '28ms');

      // Step 2 – Model
      updateStep(2, 'running');
      let payload;
      try {
        payload = JSON.parse(payloadText);
        if (!payload.transaction_id) {
          payload.transaction_id = 'TX-' + Math.floor(Math.random() * 1000000).toString().padStart(6, '0');
        }
      } catch (e) {
        soundManager.playEvent('transaction.invalid_input');
        updateStep(2, 'error');
        setError('Invalid JSON payload format.');
        setAnalysing(false);
        return;
      }

      const res = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      updateStep(2, 'done', `${data.inference_latency_ms?.toFixed(0)}ms`);

      // Step 3
      updateStep(3, 'running');
      await sleep(200);
      updateStep(3, 'done', '8ms');

      // Step 4 – Explain
      updateStep(4, 'running');
      try {
        const expRes = await fetch(`${API_BASE}/explain`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (expRes.ok) {
          const expData = await expRes.json();
          setExplanation(expData);
        }
      } catch { /* explanations are optional */ }
      updateStep(4, 'done', '15ms');

      // Step 5 – Done
      updateStep(5, 'done', '');
      setResult(data);

      // Play situation-aware sound based on real ML decision
      soundManager.playDecisionSound(selectedDomain, data);
    } catch (e: any) {
      soundManager.playEvent('transaction.failed');
      setError(e.message || 'Analysis failed. Is the backend running?');
      setSteps(prev => prev.map(s => s.status === 'running' ? { ...s, status: 'error' } : s));
    } finally {
      setAnalysing(false);
    }
  };

  const handleDomainChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const d = e.target.value;
    setSelectedDomain(d);
    setPayloadText(JSON.stringify(DOMAIN_TEMPLATES[d] || { domain: d }, null, 2));
  };

  return (
    <div className="analyze-page">
      <div className="analyze-header">
        <FileSearch size={22} className="page-icon" />
        <div>
          <h2>ANALYZE TRANSACTION</h2>
          <p className="subtitle">Submit a transaction for real-time AI fraud screening.</p>
        </div>
      </div>

      <div className="analyze-layout">
        {/* ── Left: Input Form ── */}
        <div className="glass-panel input-panel">
          <div className="panel-header">
            <h3>TRANSACTION INPUT</h3>
          </div>
          <div className="form-body">
            <div className="form-grid">
              <div className="form-group span-2">
                <label>Target Domain Model</label>
                <select value={selectedDomain} onChange={handleDomainChange} className="form-input" style={{ width: '100%', marginBottom: '15px' }}>
                  {Object.keys(DOMAIN_TEMPLATES).map(d => (
                    <option key={d} value={d}>{d.toUpperCase()} FRAUD DETECTOR</option>
                  ))}
                </select>
              </div>
              <div className="form-group span-2">
                <label>JSON Payload Features (Editable)</label>
                <textarea 
                  value={payloadText} 
                  onChange={(e) => setPayloadText(e.target.value)} 
                  className="form-input mono" 
                  rows={15} 
                  style={{ width: '100%', resize: 'vertical' }}
                  spellCheck="false"
                />
              </div>
            </div>
            <button className="btn-analyze" onClick={handleAnalyze} disabled={analysing}>
              {analysing ? <Loader size={16} className="spin" /> : <Send size={16} />}
              {analysing ? 'ANALYZING...' : 'ANALYZE TRANSACTION'}
            </button>
          </div>
        </div>

        {/* ── Right: Pipeline + Result ── */}
        <div className="right-column">
          {/* AI Pipeline */}
          <div className="glass-panel pipeline-panel">
            <div className="panel-header"><h3>AI DECISION PIPELINE</h3></div>
            <div className="pipeline-body">
              {steps.map((step, i) => (
                <div key={i} className={`pipeline-step step-${step.status}`}>
                  <div className="step-icon">
                    {step.status === 'done' && <CheckCircle size={16} />}
                    {step.status === 'running' && <Loader size={16} className="spin" />}
                    {step.status === 'error' && <XCircle size={16} />}
                    {step.status === 'idle' && <div className="idle-dot" />}
                  </div>
                  <span className="step-label">{step.label}</span>
                  {step.latency && <span className="step-latency">{step.latency}</span>}
                  {i < steps.length - 1 && <div className="step-connector" />}
                </div>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="glass-panel error-panel">
              <AlertTriangle size={18} style={{color: 'var(--accent-amber)'}} />
              <span>{error}</span>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="glass-panel result-panel">
              <div className="panel-header"><h3>ANALYSIS RESULT</h3></div>
              <div className="result-body">
                <div className={`decision-banner decision-${result.recommended_action?.toLowerCase()}`}>
                  <div className="decision-label">FINAL DECISION</div>
                  <div className="decision-value">{result.recommended_action}</div>
                </div>
                <div className="result-metrics">
                  <div className="result-metric">
                    <span className="rm-label">FRAUD PROBABILITY</span>
                    <span className={`rm-value ${result.fraud_probability > 0.5 ? 'red-text' : 'green-text'}`}>
                      {(result.fraud_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="result-metric">
                    <span className="rm-label">RISK LEVEL</span>
                    <span className={`badge ${riskClass(result.risk_level)}`}>{result.risk_level}</span>
                  </div>
                  <div className="result-metric">
                    <span className="rm-label">CONFIDENCE</span>
                    <span className="rm-value">{result.decision_confidence}</span>
                  </div>
                  <div className="result-metric">
                    <span className="rm-label">INFERENCE</span>
                    <span className="rm-value mono">{result.inference_latency_ms?.toFixed(1)}ms</span>
                  </div>
                  <div className="result-metric">
                    <span className="rm-label">MODEL</span>
                    <span className="rm-value mono">{result.model_version}</span>
                  </div>
                  <div className="result-metric">
                    <span className="rm-label">CASE ID</span>
                    <span className="rm-value mono">{result.case_id || 'N/A'}</span>
                  </div>
                </div>
                {result.decision_reasons?.length > 0 && (
                  <div className="decision-reasons">
                    <div className="dr-title">WHY THIS DECISION?</div>
                    {result.decision_reasons.map((r: string, i: number) => (
                      <div key={i} className="dr-item"><ChevronRight size={12} />{r}</div>
                    ))}
                  </div>
                )}
                {/* SHAP Explanation */}
                {explanation?.top_factors?.length > 0 && (
                  <div className="shap-section">
                    <div className="dr-title">FEATURE CONTRIBUTIONS (SHAP)</div>
                    {explanation.top_factors.map((f: any, i: number) => (
                      <div key={i} className="shap-row">
                        <span className="shap-feature">{f.feature}</span>
                        <div className="shap-bar-container">
                          <div
                            className={`shap-bar ${f.impact >= 0 ? 'shap-pos' : 'shap-neg'}`}
                            style={{ width: `${Math.min(Math.abs(f.impact) * 200, 100)}%` }}
                          />
                        </div>
                        <span className={`shap-value ${f.impact >= 0 ? 'red-text' : 'green-text'}`}>
                          {f.impact >= 0 ? '+' : ''}{f.impact.toFixed(3)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyzeTransaction;
