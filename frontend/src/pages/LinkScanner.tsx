import { useState } from 'react';
import { Globe, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight, Lock, RefreshCw } from 'lucide-react';
import './LinkScanner.css';
import { soundManager } from '../audio/soundManager';
import { API_BASE } from '../lib/apiClient';

interface URLResult {
  url: string;
  domain: string;
  scheme: string;
  risk_level: string;
  risk_score: number;
  evidence: string[];
  warnings: string[];
  recommendation: string;
  is_https: boolean;
  has_ip_host: boolean;
  possible_brand_impersonation?: string;
  scanned_at: string;
}

const LinkScanner = () => {
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<URLResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleScan = async (targetUrl?: string) => {
    const urlToScan = targetUrl || urlInput;
    if (!urlToScan.trim()) return;

    soundManager.playEvent('url.started');
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/v1/scans/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlToScan }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'URL Scan Failed');
      }
      setResult(data);

      const r = (data.risk_level || '').toUpperCase();
      if (r === 'CRITICAL') soundManager.playEvent('url.critical_risk');
      else if (r === 'HIGH') soundManager.playEvent('url.high_risk');
      else if (r === 'SUSPICIOUS' || r === 'MEDIUM') soundManager.playEvent('url.medium_risk');
      else soundManager.playEvent('url.low_risk');
    } catch (err: any) {
      soundManager.playEvent('url.error');
      setError(err.message || 'Error communicating with security scanner.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="link-scanner-page">
      <div className="scanner-header">
        <div>
          <h2>Universal Financial Link Scanner</h2>
          <p>Scans payment links, net banking portals, UPI URLs, and invoices for phishing and brand impersonation.</p>
        </div>
        <div className="security-badge flex-center gap-2">
          <Lock size={14} className="text-blue" />
          <span>SSRF & Isolated Sandbox Active</span>
        </div>
      </div>

      {/* INPUT PANEL */}
      <div className="glass-panel input-panel">
        <div className="search-input-wrapper">
          <Globe className="search-icon icon-blue" size={20} />
          <input
            type="text"
            className="url-text-input font-mono"
            placeholder="Paste suspicious payment URL (e.g., https://paytm-security-update.online/verify)..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleScan()}
          />
          <button className="btn-primary flex-center gap-2" onClick={() => handleScan()} disabled={loading}>
            {loading ? <RefreshCw size={16} className="spin" /> : <ArrowRight size={16} />}
            <span>{loading ? 'Scanning...' : 'Scan URL'}</span>
          </button>
        </div>

        <div className="quick-samples">
          <span className="text-xs text-muted">TRY SAMPLE TEST URLS:</span>
          <button className="sample-btn" onClick={() => { setUrlInput('https://chase-bank-security-verify.xyz/login'); handleScan('https://chase-bank-security-verify.xyz/login'); }}>
            Chase Phishing Sample
          </button>
          <button className="sample-btn" onClick={() => { setUrlInput('http://192.168.1.100/pay'); handleScan('http://192.168.1.100/pay'); }}>
            Raw IP Payment
          </button>
          <button className="sample-btn" onClick={() => { setUrlInput('https://stripe.com'); handleScan('https://stripe.com'); }}>
            Legitimate Domain (Stripe)
          </button>
        </div>
      </div>

      {/* ERROR DISPLAY */}
      {error && (
        <div className="glass-panel error-box">
          <ShieldAlert size={20} className="text-red" />
          <div>
            <strong>Scan Exception / Blocked Signal</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* RESULTS DISPLAY */}
      {result && (
        <div className="results-wrapper">
          <div className="glass-panel result-summary-card">
            <div className="res-header flex-between">
              <div>
                <span className="text-xs text-muted font-mono">TARGET DOMAIN</span>
                <h3 className="font-mono">{result.domain}</h3>
              </div>
              <div className={`badge ${result.risk_level === 'HIGH' || result.risk_level === 'CRITICAL' ? 'badge-red' : result.risk_level === 'SUSPICIOUS' ? 'badge-amber' : 'badge-green'}`}>
                {result.risk_level} RISK ({(result.risk_score * 100).toFixed(0)}%)
              </div>
            </div>

            <div className="recommendation-banner mt-3">
              <strong>SAFETY ADVISORY:</strong> {result.recommendation}
            </div>

            <div className="meta-grid mt-4">
              <div className="meta-item">
                <span className="meta-label">Protocol</span>
                <span className="meta-val font-mono">{result.is_https ? 'HTTPS Encrypted' : 'HTTP (Insecure)'}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Host Format</span>
                <span className="meta-val font-mono">{result.has_ip_host ? 'Raw IP Address' : 'Standard FQDN'}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Impersonation Check</span>
                <span className="meta-val font-mono">{result.possible_brand_impersonation ? `Flagged (${result.possible_brand_impersonation.toUpperCase()})` : 'Clear'}</span>
              </div>
            </div>
          </div>

          <div className="glass-panel result-details-card">
            <h4>Security Evidence & Risk Signals</h4>
            
            {result.warnings.length > 0 && (
              <div className="evidence-group">
                <span className="group-title text-amber flex-center gap-1">
                  <AlertTriangle size={14} /> Risk Warnings ({result.warnings.length})
                </span>
                <ul className="evidence-list">
                  {result.warnings.map((w, i) => (
                    <li key={i} className="warning-item">
                      <AlertTriangle size={14} className="text-amber flex-shrink-0" />
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="evidence-group mt-3">
              <span className="group-title text-green flex-center gap-1">
                <CheckCircle2 size={14} /> Positive Security Signals
              </span>
              <ul className="evidence-list">
                {result.evidence.length > 0 ? (
                  result.evidence.map((ev, i) => (
                    <li key={i} className="positive-item">
                      <CheckCircle2 size={14} className="text-green flex-shrink-0" />
                      <span>{ev}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-muted text-xs">No clear positive signals verified.</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LinkScanner;
