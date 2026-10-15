import { useEffect, useState } from 'react';
import { Box, AlertTriangle, Loader } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './ModelIntelligence.css';

import { API_BASE } from '../lib/apiClient';

const TOOLTIP_STYLE = {
  backgroundColor: 'rgba(15,23,42,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
  color: '#f8fafc',
  fontSize: '0.75rem',
  fontFamily: 'JetBrains Mono, monospace',
};

interface ModelInfo {
  model_version: string;
  inference_latency_ms: number;
  feature_schema_version: string;
}

const ModelIntelligence: React.FC = () => {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [sample, setSample] = useState<ModelInfo | null>(null);
  const [shapData, setShapData] = useState<any[]>([]);

  useEffect(() => {
    const init = async () => {
      try {
        const h = await fetch(`${API_BASE}/health`);
        setApiOnline(h.ok);
      } catch { setApiOnline(false); }

      // Run a probe transaction to get model metadata
      try {
        const res = await fetch(`${API_BASE}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transaction_id: 'PROBE-001',
            step: 1, type: 'TRANSFER', amount: 10000,
            oldbalanceOrg: 50000, oldbalanceDest: 1000,
            newbalanceOrig: 40000, newbalanceDest: 11000,
            nameOrig: 'PROBE_C', nameDest: 'PROBE_M', channel: 'PROBE',
          }),
        });
        if (res.ok) {
          const d = await res.json();
          setSample({ model_version: d.model_version, inference_latency_ms: d.inference_latency_ms, feature_schema_version: d.feature_schema_version });
        }
      } catch {}

      // Get SHAP from explain endpoint
      try {
        const res = await fetch(`${API_BASE}/explain`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transaction_id: 'PROBE-001',
            step: 1, type: 'TRANSFER', amount: 100000,
            oldbalanceOrg: 150000, oldbalanceDest: 0,
            newbalanceOrig: 50000, newbalanceDest: 100000,
            nameOrig: 'PROBE_C', nameDest: 'PROBE_M', channel: 'PROBE',
          }),
        });
        if (res.ok) {
          const d = await res.json();
          setShapData(
            d.top_factors
              ?.sort((a: any, b: any) => Math.abs(b.impact) - Math.abs(a.impact))
              .slice(0, 10) || []
          );
        }
      } catch {}

      setLoading(false);
    };
    init();
  }, []);

  const NA = <span className="na-text">DATA UNAVAILABLE</span>;

  return (
    <div className="model-page">
      <div className="analyze-header">
        <Box size={22} className="page-icon" />
        <div>
          <h2>MODEL INTELLIGENCE</h2>
          <p className="subtitle">Live XGBoost model metadata, SHAP feature importance, and system readiness.</p>
        </div>
      </div>

      {loading ? (
        <div className="glass-panel loading-panel">
          <Loader size={24} className="spin" style={{ color: 'var(--accent-blue)' }} />
          <span>Probing backend for model metadata...</span>
        </div>
      ) : (
        <>
          {/* Model Status Cards */}
          <div className="model-status-grid">
            <div className="glass-panel model-status-card">
              <div className="msc-label">MODEL STATUS</div>
              {apiOnline
                ? <div className="msc-value green-text">● ONLINE</div>
                : <div className="msc-value red-text">● OFFLINE</div>}
            </div>
            <div className="glass-panel model-status-card">
              <div className="msc-label">ALGORITHM</div>
              <div className="msc-value">XGBoost</div>
            </div>
            <div className="glass-panel model-status-card">
              <div className="msc-label">MODEL VERSION</div>
              <div className="msc-value mono">{sample?.model_version || NA}</div>
            </div>
            <div className="glass-panel model-status-card">
              <div className="msc-label">FEATURE SCHEMA</div>
              <div className="msc-value mono">{sample?.feature_schema_version || NA}</div>
            </div>
            <div className="glass-panel model-status-card">
              <div className="msc-label">AVG INFERENCE LATENCY</div>
              <div className="msc-value mono green-text">{sample ? `${sample.inference_latency_ms.toFixed(1)}ms` : NA}</div>
            </div>
          </div>

          {/* Performance Note */}
          <div className="glass-panel info-banner">
            <AlertTriangle size={16} style={{ color: 'var(--accent-amber)', flexShrink: 0 }} />
            <p>
              Offline model performance metrics (Precision, Recall, ROC-AUC, F1, PR-AUC) are available in the training artifacts.
              Run the evaluation script (<code>evaluate_decision_engine.py</code>) and expose results via the API to display them here.
              Fabricated metrics are never shown.
            </p>
          </div>

          {/* SHAP Feature Importance */}
          <div className="glass-panel">
            <div className="panel-header">
              <h3>SHAP FEATURE IMPORTANCE</h3>
              <span className="badge badge-purple">LIVE — from /explain</span>
            </div>
            <div className="panel-body">
              {shapData.length > 0 ? (
                <>
                  <div className="shap-legend">
                    <span className="legend-pos">■ Increases fraud risk</span>
                    <span className="legend-neg">■ Reduces fraud risk</span>
                  </div>
                  <div style={{ marginTop: 16 }}>
                    {shapData.map((f, i) => (
                      <div key={i} className="fi-row">
                        <span className="fi-feature">{f.feature}</span>
                        <div className="fi-bar-track">
                          <div
                            className={`fi-bar ${f.impact >= 0 ? 'fi-pos' : 'fi-neg'}`}
                            style={{ width: `${Math.min(Math.abs(f.impact) * 200, 100)}%` }}
                          />
                        </div>
                        <span className={`fi-value ${f.impact >= 0 ? 'red-text' : 'green-text'}`}>
                          {f.impact >= 0 ? '+' : ''}{f.impact.toFixed(3)}
                        </span>
                      </div>
                    ))}
                  </div>
                  {/* Bar chart view */}
                  <div style={{ height: 280, marginTop: 24 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart layout="vertical" data={shapData} margin={{ left: 60, right: 20 }}>
                        <XAxis type="number" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <YAxis type="category" dataKey="feature" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} width={130} />
                        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => [Number(v ?? 0).toFixed(4), 'SHAP Impact']} />
                        <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                          {shapData.map((f, i) => (
                            <Cell key={i} fill={f.impact >= 0 ? '#ef4444' : '#10b981'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </>
              ) : (
                <div className="unavailable-state">
                  <AlertTriangle size={20} style={{ color: 'var(--accent-amber)' }} />
                  <p>SHAP data unavailable. The explain endpoint returned no factors.</p>
                </div>
              )}
            </div>
          </div>

          {/* Decision Policy */}
          <div className="glass-panel">
            <div className="panel-header"><h3>DECISION POLICY CONFIGURATION</h3></div>
            <div className="panel-body">
              <div className="policy-grid">
                <div className="policy-item">
                  <div className="policy-label">LOW RISK THRESHOLD</div>
                  <div className="policy-value green-text">≤ 30%</div>
                </div>
                <div className="policy-item">
                  <div className="policy-label">MEDIUM RISK THRESHOLD</div>
                  <div className="policy-value amber-text">31% – 60%</div>
                </div>
                <div className="policy-item">
                  <div className="policy-label">HIGH RISK THRESHOLD</div>
                  <div className="policy-value red-text">≥ 61%</div>
                </div>
                <div className="policy-item">
                  <div className="policy-label">APPROVE ACTION</div>
                  <div className="policy-value green-text">FRAUD_PROB &lt; 0.30</div>
                </div>
                <div className="policy-item">
                  <div className="policy-label">VERIFY ACTION</div>
                  <div className="policy-value amber-text">0.30 ≤ FRAUD_PROB ≤ 0.60</div>
                </div>
                <div className="policy-item">
                  <div className="policy-label">BLOCK ACTION</div>
                  <div className="policy-value red-text">FRAUD_PROB &gt; 0.60</div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelIntelligence;
