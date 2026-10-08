import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import './AuditLogs.css';

interface AuditRecord {
  id: number;
  timestamp: string;
  step: number;
  type: string;
  amount: number;
  prediction: string;
  fraud_probability: number;
  risk_level: string;
  recommended_action: string;
  decision_policy: string;
  model_version: string;
  inference_latency_ms: number;
}

const AuditLogs = () => {
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = () => {
    setLoading(true);
    fetch('/api/v1/audit/logs')
      .then((res) => res.json())
      .then((data) => setLogs(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="audit-page">
      <div className="audit-header flex-between">
        <div>
          <h2>Immutable Application Audit Trail</h2>
          <p>Read-only SQLite WAL transaction logs recording every decision, model version, and inference latency.</p>
        </div>
        <button className="btn-secondary flex-center gap-2" onClick={fetchLogs}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Logs
        </button>
      </div>

      <div className="glass-panel audit-panel">
        <table className="audit-table font-mono text-xs">
          <thead>
            <tr>
              <th>LOG ID</th>
              <th>TIMESTAMP</th>
              <th>TYPE</th>
              <th>AMOUNT</th>
              <th>PREDICTION</th>
              <th>FRAUD PROB</th>
              <th>ACTION</th>
              <th>MODEL</th>
              <th>LATENCY</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="text-blue">#{log.id}</td>
                <td className="text-muted">{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.type}</td>
                <td>${log.amount.toFixed(2)}</td>
                <td>
                  <span className={`badge ${log.prediction === 'Fraud' ? 'badge-red' : 'badge-green'}`}>
                    {log.prediction}
                  </span>
                </td>
                <td>{(log.fraud_probability * 100).toFixed(1)}%</td>
                <td>{log.recommended_action}</td>
                <td>{log.model_version}</td>
                <td className="text-amber">{log.inference_latency_ms.toFixed(1)}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditLogs;
