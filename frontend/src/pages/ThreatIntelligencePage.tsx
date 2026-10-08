import { useEffect, useState } from 'react';
import { ShieldAlert, RefreshCw } from 'lucide-react';
import './ThreatIntelligencePage.css';

interface ThreatItem {
  id: string;
  category: string;
  threat_actor: string;
  target_ecosystem: string;
  severity: string;
  indicators: string[];
  timestamp: string;
}

const ThreatIntelligencePage = () => {
  const [threats, setThreats] = useState<ThreatItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/threat-intelligence')
      .then((res) => res.json())
      .then((data) => setThreats(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="threat-page">
      <div className="threat-header flex-between">
        <div>
          <h2>Global Threat Intelligence & Domain Security</h2>
          <p>Real-time indicators of compromise (IOCs), phishing wave campaigns, and brand impersonation feeds.</p>
        </div>
        <span className="badge badge-purple font-mono">FEED ACTIVE</span>
      </div>

      <div className="glass-panel threat-feed-card">
        <h3>Live Fraud Indicators (IOC Feed)</h3>

        {loading ? (
          <div className="loading-box flex-center gap-2">
            <RefreshCw size={16} className="spin text-blue" />
            <span>Syncing threat intelligence sources...</span>
          </div>
        ) : (
          <div className="threat-list mt-3">
            {threats.map((t) => (
              <div key={t.id} className="threat-item-card">
                <div className="th-header flex-between">
                  <div className="flex-center gap-2">
                    <ShieldAlert size={16} className="text-red" />
                    <span className="font-mono text-blue">{t.id}</span>
                    <strong>{t.category}</strong>
                  </div>
                  <span className={`badge ${t.severity === 'CRITICAL' ? 'badge-red' : 'badge-amber'}`}>
                    {t.severity}
                  </span>
                </div>

                <div className="th-meta mt-2">
                  <span><strong>Actor:</strong> {t.threat_actor}</span>
                  <span><strong>Target:</strong> {t.target_ecosystem}</span>
                </div>

                <div className="th-indicators mt-2">
                  <span className="text-xs text-muted">INDICATORS:</span>
                  <div className="indicator-tags">
                    {t.indicators.map((ind, i) => (
                      <span key={i} className="ind-tag font-mono">{ind}</span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ThreatIntelligencePage;
