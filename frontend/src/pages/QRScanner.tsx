import { useState } from 'react';
import { QrCode, ShieldAlert, AlertTriangle, RefreshCw, Smartphone } from 'lucide-react';
import './QRScanner.css';
import { soundManager } from '../audio/soundManager';

interface QRResult {
  qr_type: string;
  payee_id?: string;
  payee_name?: string;
  amount?: number;
  risk_level: string;
  risk_score: number;
  evidence: string[];
  warnings: string[];
  recommendation: string;
}

const QRScanner = () => {
  const [payload, setPayload] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QRResult | null>(null);

  const handleScan = async (rawPayload?: string) => {
    const textToScan = rawPayload || payload;
    if (!textToScan.trim()) return;

    soundManager.playEvent('qr.started');
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch('/api/v1/scans/qr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: textToScan }),
      });
      const data = await res.json();
      setResult(data);

      const r = (data.risk_level || '').toUpperCase();
      if (r === 'CRITICAL') soundManager.playEvent('qr.critical_risk');
      else if (r === 'HIGH') soundManager.playEvent('qr.high_risk');
      else if (r === 'SUSPICIOUS' || r === 'MEDIUM') soundManager.playEvent('qr.medium_risk');
      else soundManager.playEvent('qr.low_risk');
    } catch {
      soundManager.playEvent('transaction.failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qr-scanner-page">
      <div className="scanner-header">
        <div>
          <h2>QR Security Scanner & UPI Shield</h2>
          <p>Decodes QR payment payloads, verifies VPA addresses, and checks payee legitimacy before PIN entry.</p>
        </div>
      </div>

      <div className="qr-grid">
        {/* INPUT BOX */}
        <div className="glass-panel qr-input-card">
          <div className="card-title">
            <QrCode className="icon-blue" size={20} />
            <h3>Paste QR Payload / UPI URI</h3>
          </div>

          <textarea
            className="qr-textarea font-mono"
            rows={5}
            placeholder="Paste raw QR string (e.g. upi://pay?pa=merchant@upi&pn=Store&am=1500.00)..."
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
          />

          <div className="qr-actions">
            <button className="btn-primary flex-center gap-2" onClick={() => handleScan()} disabled={loading}>
              {loading ? <RefreshCw size={16} className="spin" /> : <ShieldAlert size={16} />}
              <span>{loading ? 'Analyzing...' : 'Scan Payload'}</span>
            </button>
          </div>

          <div className="samples-container">
            <span className="text-xs text-muted">PRESET TEST SAMPLES:</span>
            <div className="sample-chips mt-2">
              <button className="chip" onClick={() => { setPayload('upi://pay?pa=win_lottery_claim@ybl&pn=Jackpot%20Winner&am=9999.00'); handleScan('upi://pay?pa=win_lottery_claim@ybl&pn=Jackpot%20Winner&am=9999.00'); }}>
                Suspicious High-Val Lottery QR
              </button>
              <button className="chip" onClick={() => { setPayload('upi://pay?pa=starbucks@icici&pn=Starbucks%20India&am=240.00'); handleScan('upi://pay?pa=starbucks@icici&pn=Starbucks%20India&am=240.00'); }}>
                Valid Merchant UPI QR
              </button>
            </div>
          </div>
        </div>

        {/* RESULTS BOX */}
        {result && (
          <div className="glass-panel qr-result-card">
            <div className="res-head flex-between">
              <div className="flex-center gap-2">
                <Smartphone size={18} className="text-blue" />
                <span className="badge badge-blue">{result.qr_type} VECTOR</span>
              </div>
              <span className={`badge ${result.risk_level === 'HIGH' ? 'badge-red' : result.risk_level === 'SUSPICIOUS' ? 'badge-amber' : 'badge-green'}`}>
                {result.risk_level} RISK ({(result.risk_score * 100).toFixed(0)}%)
              </span>
            </div>

            <div className="vpa-details-box mt-3">
              <div className="vpa-row">
                <span className="vpa-lbl">Target Payee VPA:</span>
                <span className="vpa-val font-mono">{result.payee_id || 'Not specified'}</span>
              </div>
              <div className="vpa-row">
                <span className="vpa-lbl">Payee Name:</span>
                <span className="vpa-val font-mono">{result.payee_name || 'N/A'}</span>
              </div>
              {result.amount && (
                <div className="vpa-row">
                  <span className="vpa-lbl">Request Amount:</span>
                  <span className="vpa-val font-mono text-amber">${result.amount.toFixed(2)}</span>
                </div>
              )}
            </div>

            <div className="advisory-box mt-3">
              <strong>RECOMMENDATION:</strong> {result.recommendation}
            </div>

            {result.warnings.length > 0 && (
              <div className="warnings-section mt-3">
                <span className="text-xs text-amber font-mono">WARNING SIGNALS</span>
                <ul className="qr-list">
                  {result.warnings.map((w, i) => (
                    <li key={i}><AlertTriangle size={14} className="text-amber" /> {w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QRScanner;
