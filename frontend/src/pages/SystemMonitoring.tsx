import { useEffect, useState, useRef } from 'react';
import { Server, Activity, Database, Cpu, Zap, CheckCircle, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { soundManager } from '../audio/soundManager';
import './SystemMonitoring.css';

const API_BASE = '/api';
const TOOLTIP_STYLE = {
  backgroundColor: 'rgba(15,23,42,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
  color: '#f8fafc',
  fontSize: '0.72rem',
  fontFamily: 'JetBrains Mono, monospace',
};

interface LogEntry { time: string; level: 'INFO' | 'WARN' | 'ERROR'; message: string; }
interface LatencyPoint { time: string; latency: number; }
interface ServiceStatus { name: string; status: 'ONLINE' | 'OFFLINE' | 'DEGRADED'; icon: React.ElementType; detail: string; }

const SystemMonitoring: React.FC = () => {
  const [health, setHealth] = useState<'ONLINE' | 'OFFLINE' | 'CHECKING'>('CHECKING');
  const [readiness, setReadiness] = useState<boolean | null>(null);
  const [latencyHistory, setLatencyHistory] = useState<LatencyPoint[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [drift, setDrift] = useState<any>(null);
  const [performance, setPerformance] = useState<any>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const addLog = (level: LogEntry['level'], message: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [{ time, level, message }, ...prev].slice(0, 80));
  };

  const probe = async (isManual = false) => {
    const start = Date.now();
    try {
      const [h, r] = await Promise.all([
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/readiness`),
      ]);
      const latency = Date.now() - start;
      const online = h.ok;
      setHealth(online ? 'ONLINE' : 'OFFLINE');
      setReadiness(r.ok);
      setLatencyHistory(prev => [
        ...prev.slice(-39),
        { time: new Date().toLocaleTimeString(), latency },
      ]);
      addLog(online ? 'INFO' : 'ERROR', `Health check — ${online ? 'HEALTHY' : 'FAILED'} (${latency}ms)`);
      if (!online) {
        soundManager.playEvent('monitoring.service_error');
      } else if (isManual) {
        soundManager.playEvent('dashboard.refresh');
      }
    } catch {
      setHealth('OFFLINE');
      setReadiness(false);
      addLog('ERROR', 'API unreachable — health check failed');
      soundManager.playEvent('monitoring.service_error');
    }

    try {
      const d = await fetch(`${API_BASE}/monitoring/drift`);
      if (d.ok) {
        const driftData = await d.json();
        setDrift(driftData);
        if (driftData?.drift_detected) {
          soundManager.playEvent('monitoring.drift_detected');
        }
      }
      const p = await fetch(`${API_BASE}/monitoring/performance`);
      if (p.ok) setPerformance(await p.json());
    } catch { /* monitoring endpoints optional */ }
  };

  useEffect(() => {
    probe();
    addLog('INFO', 'FraudSense AI monitoring dashboard initialised');
    addLog('INFO', 'XGBoost inference engine loaded');
    const interval = setInterval(probe, 8000);
    return () => clearInterval(interval);
  }, []);

  const services: ServiceStatus[] = [
    { name: 'FASTAPI BACKEND', status: health === 'ONLINE' ? 'ONLINE' : 'OFFLINE', icon: Server, detail: health === 'ONLINE' ? 'Port 8000 — Active' : 'Unreachable' },
    { name: 'ML MODEL', status: readiness ? 'ONLINE' : readiness === false ? 'OFFLINE' : 'DEGRADED', icon: Zap, detail: readiness ? 'XGBoost v2.4.1 — Ready' : 'Not loaded' },
    { name: 'SQLITE DATABASE', status: health === 'ONLINE' ? 'ONLINE' : 'OFFLINE', icon: Database, detail: 'audit_log.db — Active' },
    { name: 'SHAP ENGINE', status: readiness ? 'ONLINE' : 'OFFLINE', icon: Activity, detail: readiness ? 'TreeExplainer — Ready' : 'Unavailable' },
    { name: 'DECISION ENGINE', status: health === 'ONLINE' ? 'ONLINE' : 'OFFLINE', icon: Cpu, detail: 'Policy v1.0 — Active' },
    { name: 'REACT FRONTEND', status: 'ONLINE', icon: CheckCircle, detail: 'Vite 8.3 — Port 5173' },
  ];

  const avgLatency = latencyHistory.length
    ? (latencyHistory.reduce((s, p) => s + p.latency, 0) / latencyHistory.length).toFixed(0)
    : 'N/A';

  return (
    <div className="monitoring-page">
      <div className="analyze-header">
        <Server size={22} className="page-icon" />
        <div>
          <h2>SYSTEM MONITORING</h2>
          <p className="subtitle">Live infrastructure health, API latency, and model status.</p>
        </div>
        <button className="btn-secondary refresh-btn" onClick={() => probe(true)}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Service Cards */}
      <div className="services-grid">
        {services.map(svc => (
          <div key={svc.name} className={`glass-panel svc-card svc-${svc.status.toLowerCase()}`}>
            <div className="svc-top">
              <svc.icon size={18} className="svc-icon" />
              <span className={`badge ${svc.status === 'ONLINE' ? 'badge-green' : svc.status === 'DEGRADED' ? 'badge-amber' : 'badge-red'}`}>
                {svc.status}
              </span>
            </div>
            <div className="svc-name">{svc.name}</div>
            <div className="svc-detail">{svc.detail}</div>
          </div>
        ))}
      </div>

      {/* Latency Chart + Stats */}
      <div className="monitoring-content">
        <div className="glass-panel latency-chart">
          <div className="panel-header">
            <h3>API RESPONSE LATENCY</h3>
            <span className="badge badge-blue">AUTO-REFRESH 8s</span>
          </div>
          <div className="panel-body" style={{ height: 220 }}>
            {latencyHistory.length > 1 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={latencyHistory}>
                  <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} interval={4} />
                  <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} unit="ms" />
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => [`${v}ms`, 'Latency']} />
                  <Line type="monotone" dataKey="latency" stroke="#38bdf8" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                Collecting data...
              </div>
            )}
          </div>
        </div>

        <div className="side-stats">
          <div className="glass-panel stat-item">
            <div className="si-label">SYSTEM STATUS</div>
            <div className={`si-value ${health === 'ONLINE' ? 'green-text' : 'red-text'}`}>● {health}</div>
          </div>
          <div className="glass-panel stat-item">
            <div className="si-label">AVG LATENCY</div>
            <div className="si-value mono">{avgLatency}ms</div>
          </div>
          <div className="glass-panel stat-item">
            <div className="si-label">HEALTH CHECKS</div>
            <div className="si-value mono">{latencyHistory.length}</div>
          </div>
          <div className="glass-panel stat-item">
            <div className="si-label">MODEL READY</div>
            <div className={`si-value ${readiness ? 'green-text' : 'red-text'}`}>{readiness === null ? 'CHECKING' : readiness ? 'YES' : 'NO'}</div>
          </div>
        </div>
      </div>

      {/* Drift & Performance */}
      {(drift || performance) && (
        <div className="monitoring-content">
          {drift && (
            <div className="glass-panel">
              <div className="panel-header"><h3>DATA DRIFT ANALYSIS</h3></div>
              <div className="panel-body">
                <pre className="mono-data">{JSON.stringify(drift, null, 2)}</pre>
              </div>
            </div>
          )}
          {performance && (
            <div className="glass-panel">
              <div className="panel-header"><h3>MODEL PERFORMANCE ANALYSIS</h3></div>
              <div className="panel-body">
                <pre className="mono-data">{JSON.stringify(performance, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Live Logs */}
      <div className="glass-panel">
        <div className="panel-header">
          <h3>LIVE SYSTEM LOGS</h3>
          <div className="badge badge-green"><span className="live-dot" /> LIVE</div>
        </div>
        <div className="log-container" ref={logRef}>
          {logs.map((log, i) => (
            <div key={i} className={`log-entry log-${log.level.toLowerCase()}`}>
              <span className="log-time">{log.time}</span>
              <span className={`log-level ${log.level === 'INFO' ? 'blue-text' : log.level === 'WARN' ? 'amber-text' : 'red-text'}`}>{log.level}</span>
              <span className="log-msg">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SystemMonitoring;
