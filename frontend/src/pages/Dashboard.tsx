import { useState, useEffect } from 'react';
import { Activity, ShieldAlert, CheckCircle, Clock, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import './Dashboard.css';

// ─── Types ───────────────────────────────────────────────────────────────────
interface Metric {
  title: string;
  value: string | number;
  change: string;
  trend: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
}

interface ApiHealth {
  status: string;
}

interface DashboardSummary {
  transactions_analyzed: number;
  fraud_detected: number;
  legitimate_transactions: number;
  fraud_rate: number;
  risk_distribution: Record<string, number>;
  timeline: { time: string; legitimate: number; fraud: number; suspicious: number }[];
}

// ─── API Layer ───────────────────────────────────────────────────────────────
const API_BASE = '/api';

async function fetchHealth(): Promise<ApiHealth | null> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

// ─── Subcomponents ────────────────────────────────────────────────────────────
const MetricCard: React.FC<Metric> = ({ title, value, change, trend, icon: Icon }) => (
  <div className="glass-panel metric-card">
    <div className="metric-header">
      <h3 className="metric-title">{title}</h3>
      <Icon size={16} className={`metric-icon ${trend}`} />
    </div>
    <div className="metric-body">
      <div className="metric-value data-value">{value}</div>
      <div className={`metric-change ${trend}`}>
        {trend === 'positive' ? <TrendingDown size={12} /> : trend === 'negative' ? <TrendingUp size={12} /> : null}
        {change} <span className="metric-vs">vs previous period</span>
      </div>
    </div>
  </div>
);

const RISK_COLORS = {
  LOW: '#10b981',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
};

const CUSTOM_TOOLTIP_STYLE = {
  backgroundColor: 'rgba(15,23,42,0.9)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
  color: '#f8fafc',
  fontSize: '0.75rem',
  fontFamily: 'JetBrains Mono, monospace',
};

// ─── Dashboard Page ───────────────────────────────────────────────────────────
const Dashboard: React.FC = () => {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    const refresh = async () => {
      const health = await fetchHealth();
      setApiOnline(health?.status === 'healthy');
      try {
        const response = await fetch(`${API_BASE}/dashboard/summary`);
        if (response.ok) setSummary(await response.json());
      } catch { /* API state is represented by apiOnline */ }
    };
    refresh();
    const interval = setInterval(refresh, 15_000);
    return () => clearInterval(interval);
  }, []);

  const riskData = Object.entries(summary?.risk_distribution ?? {})
    .map(([name, value]) => ({ name, value }))
    .filter(({ name }) => name in RISK_COLORS);

  const metrics: Metric[] = [
    {
      title: 'TRANSACTIONS ANALYZED',
      value: summary?.transactions_analyzed ?? 0,
      change: 'Recorded audits',
      trend: 'neutral',
      icon: Activity,
    },
    {
      title: 'FRAUD DETECTED',
      value: summary?.fraud_detected ?? 0,
      change: 'Model decisions',
      trend: 'negative',
      icon: ShieldAlert,
    },
    {
      title: 'LEGITIMATE TRANSACTIONS',
      value: summary?.legitimate_transactions ?? 0,
      change: 'Model decisions',
      trend: 'positive',
      icon: CheckCircle,
    },
    {
      title: 'FRAUD RATE',
      value: `${summary?.fraud_rate ?? 0}%`,
      change: 'Across recorded audits',
      trend: 'positive',
      icon: Clock,
    },
  ];

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <div className="dashboard-header">
        <div>
          <h2>GLOBAL COMMAND CENTER</h2>
          <p className="subtitle">Real-time financial transaction intelligence and fraud monitoring.</p>
        </div>
        <div className="model-info">
          <div className="badge badge-blue"><Zap size={11} /> DATABASE-BACKED METRICS</div>
          <div className="latency-info">
            API: <span className={apiOnline === null ? '' : apiOnline ? 'data-value green-text' : 'data-value red-text'}>
              {apiOnline === null ? 'Checking...' : apiOnline ? '● ONLINE' : '● OFFLINE'}
            </span>
          </div>
        </div>
      </div>

      {/* ── KPI Metrics ── */}
      <div className="metrics-grid">
        {metrics.map(m => <MetricCard key={m.title} {...m} />)}
      </div>

      {/* ── Charts Row ── */}
      <div className="dashboard-content">
        {/* Threat Landscape */}
        <div className="glass-panel main-chart">
          <div className="panel-header">
            <h3>TRANSACTION ACTIVITY (LAST 24 HOURS)</h3>
            <div className="badge badge-blue">15s REFRESH</div>
          </div>
          <div className="panel-body" style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary?.timeline ?? []} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="legit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="fraud" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="susp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} interval={4} />
                <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="legitimate" stroke="#10b981" strokeWidth={2} fill="url(#legit)" dot={false} name="Legitimate" isAnimationActive={false} />
                <Area type="monotone" dataKey="suspicious" stroke="#f59e0b" strokeWidth={1.5} fill="url(#susp)" dot={false} name="Suspicious" isAnimationActive={false} />
                <Area type="monotone" dataKey="fraud" stroke="#ef4444" strokeWidth={2} fill="url(#fraud)" dot={false} name="Fraud" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="glass-panel side-panel">
          <div className="panel-header">
            <h3>FRAUD RISK DISTRIBUTION</h3>
          </div>
          <div className="panel-body" style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="45%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {riskData.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name as keyof typeof RISK_COLORS]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={CUSTOM_TOOLTIP_STYLE} />
                <Legend
                  iconType="circle"
                  formatter={(value) => <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── Audit disclosure ── */}
      <div className="glass-panel transaction-stream">
        <div className="panel-header">
          <h3>AUDIT DATA</h3>
          <div className="badge badge-blue">PERSISTED</div>
        </div>
        <div className="panel-body" style={{ padding: '20px', color: 'var(--text-secondary)' }}>
          {summary?.transactions_analyzed
            ? 'Dashboard figures are calculated from persisted transaction audit records. Open Audit Logs for record-level review.'
            : 'No transaction audits have been recorded yet. Submit a transaction after a trained model has been configured.'}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
