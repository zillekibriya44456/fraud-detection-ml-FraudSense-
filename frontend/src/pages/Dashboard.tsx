import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, ShieldAlert, CheckCircle, AlertTriangle,
  DollarSign, Cpu, RefreshCw, Search,
  ChevronLeft, ChevronRight,
  Server, Zap, Clock, Database,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, BarChart, Bar,
} from 'recharts';
import './Dashboard.css';
import { soundManager } from '../audio/soundManager';

// ─── Constants ────────────────────────────────────────────────────────────────

const API_BASE = '/api';

const RISK_COLORS: Record<string, string> = {
  LOW:      '#10b981',
  MEDIUM:   '#f59e0b',
  HIGH:     '#f97316',
  CRITICAL: '#ef4444',
};

const TOOLTIP_STYLE = {
  backgroundColor: 'rgba(10,17,32,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
  color: '#f8fafc',
  fontSize: '0.75rem',
  fontFamily: 'JetBrains Mono, monospace',
};

// ─── Types ─────────────────────────────────────────────────────────────────────

interface DashboardSummary {
  transactions_analyzed: number;
  fraud_detected: number;
  legitimate_transactions: number;
  fraud_rate: number;
  amount_at_risk: number;
  total_amount_analyzed: number;
  confirmed_fraud_cases: number;
  open_cases_count: number;
  risk_distribution: Record<string, number>;
  domain_breakdown: Record<string, number>;
  avg_inference_latency_ms: number;
  timeline: { time: string; total: number; legitimate: number; fraud: number; suspicious: number }[];
  timeline_range: string;
}

interface TxRow {
  id: number;
  timestamp: string | null;
  type: string;
  domain_label: string;
  amount: number | null;
  fraud_probability: number;
  risk_level: string;
  prediction: string;
  recommended_action: string;
  inference_latency_ms: number;
}

interface TxPage {
  page: number;
  page_size: number;
  total: number;
  pages: number;
  results: TxRow[];
}

interface AlertItem {
  id: number;
  timestamp: string | null;
  type: string;
  domain_label: string;
  risk_level: string;
  fraud_probability: number;
  prediction: string;
  recommended_action: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, decimals = 0): string {
  if (n == null) return '—';
  return n.toLocaleString('en-IN', { maximumFractionDigits: decimals });
}

function fmtCurrency(n: number | null | undefined): string {
  if (n == null) return '—';
  if (n >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(2)} Cr`;
  if (n >= 1_00_000)    return `₹${(n / 1_00_000).toFixed(2)} L`;
  return `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

function fmtTime(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });
}

function fmtRelative(iso: string | null): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function probColor(p: number): string {
  if (p >= 0.75) return '#ef4444';
  if (p >= 0.50) return '#f97316';
  if (p >= 0.25) return '#f59e0b';
  return '#10b981';
}

function predClass(pred: string): string {
  const u = pred.toUpperCase();
  if (['FRAUD','SPAM_SCAM','PHISHING','SCAM','SPAM'].includes(u)) return 'fraud';
  if (['LEGITIMATE','LICIT','SAFE','NOT_FRAUD'].includes(u)) return 'legit';
  return 'other';
}

function rowClass(risk: string): string {
  if (risk === 'CRITICAL') return 'row-fraud';
  if (risk === 'HIGH') return 'row-suspicious';
  if (risk === 'MEDIUM') return 'row-medium';
  return 'row-legit';
}

// ─── API ──────────────────────────────────────────────────────────────────────

async function fetchSummary(range: string): Promise<DashboardSummary | null> {
  const res = await fetch(`${API_BASE}/dashboard/summary?range=${range}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchTransactions(
  page: number, search: string, risk: string
): Promise<TxPage | null> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: '15',
    q: search,
    risk,
  });
  const res = await fetch(`${API_BASE}/dashboard/transactions?${params}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchAlerts(): Promise<AlertItem[]> {
  const res = await fetch(`${API_BASE}/dashboard/alerts?limit=20`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.alerts ?? [];
}

async function fetchHealth(): Promise<{ status: string } | null> {
  const t0 = performance.now();
  const res = await fetch(`${API_BASE}/health`);
  const latency = performance.now() - t0;
  if (!res.ok) return null;
  const json = await res.json();
  return { ...json, latency_ms: Math.round(latency) };
}

// ─── Sub-components ────────────────────────────────────────────────────────────

interface KpiCardProps {
  title: string;
  value: string | number;
  sub?: string;
  tooltip?: string;
  icon: React.ElementType;
  iconClass?: string;
  cardClass?: string;
  loading?: boolean;
}

const KpiCard: React.FC<KpiCardProps> = ({
  title, value, sub, icon: Icon, iconClass = 'neutral', cardClass = '', loading,
}) => (
  <div className={`glass-panel metric-card ${cardClass}`} title={sub}>
    <div className="metric-header">
      <span className="metric-title">{title}</span>
      <Icon size={15} className={`metric-icon ${iconClass}`} />
    </div>
    {loading ? (
      <div className="metric-loading">
        <div className="skeleton skeleton-value" />
        <div className="skeleton skeleton-sub" />
      </div>
    ) : (
      <>
        <div className="metric-value data-value">{value}</div>
        {sub && <div className="metric-sub">{sub}</div>}
      </>
    )}
  </div>
);

// ─── Dashboard Page ────────────────────────────────────────────────────────────

const Dashboard: React.FC = () => {
  // ── State ──
  const [summary, setSummary]     = useState<DashboardSummary | null>(null);
  const [sumError, setSumError]   = useState(false);
  const [sumLoading, setSumLoading] = useState(true);
  const [range, setRange]          = useState<string>('24h');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [refreshing, setRefreshing]   = useState(false);

  const [txPage, setTxPage]       = useState<TxPage | null>(null);
  const [txSearch, setTxSearch]   = useState('');
  const [txRisk, setTxRisk]       = useState('');
  const [txPageNum, setTxPageNum] = useState(1);
  const [txLoading, setTxLoading] = useState(true);


  const [alerts, setAlerts]       = useState<AlertItem[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);

  const [apiHealth, setApiHealth]   = useState<{ status: string; latency_ms?: number } | null>(null);
  const [modelReady, setModelReady] = useState<boolean | null>(null);
  const [modelLatency, setModelLatency] = useState<number | null>(null);

  const txSearchRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isInitialRef = useRef(true);

  // ── Load summary ──
  const loadSummary = useCallback(async (r: string, isAuto = false) => {
    if (!isAuto) setSumLoading(true);
    else setRefreshing(true);
    setSumError(false);
    try {
      const data = await fetchSummary(r);
      setSummary(data);
      setLastUpdated(new Date());
      if (!isInitialRef.current) {
        soundManager.playEvent('dashboard.refresh');
      }
      if (data?.risk_distribution?.CRITICAL && data.risk_distribution.CRITICAL > 0) {
        soundManager.playEvent('dashboard.critical_alert');
      }
    } catch {
      setSumError(true);
      if (!isInitialRef.current) soundManager.playEvent('dashboard.error');
    } finally {
      setSumLoading(false);
      setRefreshing(false);
      isInitialRef.current = false;
    }
  }, []);

  // ── Load transactions ──
  const loadTransactions = useCallback(async (page: number, search: string, risk: string) => {
    setTxLoading(true);
    try {
      const data = await fetchTransactions(page, search, risk);
      setTxPage(data);
    } catch {
      setTxPage(null);
    } finally {
      setTxLoading(false);
    }
  }, []);

  // ── Load alerts ──
  const loadAlerts = useCallback(async () => {
    setAlertsLoading(true);
    try {
      const data = await fetchAlerts();
      setAlerts(data);
    } catch {
      setAlerts([]);
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  // ── Load health ──
  const loadHealth = useCallback(async () => {
    const [health, readiness] = await Promise.all([
      fetchHealth(),
      fetch(`${API_BASE}/readiness`).then(async (r) => {
        const t0 = performance.now();
        const json = await r.json();
        return { ...json, latency_ms: Math.round(performance.now() - t0), ok: r.ok };
      }).catch(() => null),
    ]);
    setApiHealth(health as { status: string; latency_ms?: number } | null);
    if (readiness) {
      setModelReady(readiness.model_loaded === true);
      setModelLatency(readiness.latency_ms ?? null);
    }
  }, []);

  // ── Initial load & auto-refresh ──
  useEffect(() => {
    soundManager.playEvent('dashboard.opened');
    loadSummary(range);
    loadTransactions(1, '', '');
    loadAlerts();
    loadHealth();

    const summaryInterval = setInterval(() => loadSummary(range, true), 15_000);
    const alertInterval   = setInterval(loadAlerts, 30_000);
    const healthInterval  = setInterval(loadHealth, 20_000);

    return () => {
      clearInterval(summaryInterval);
      clearInterval(alertInterval);
      clearInterval(healthInterval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Re-fetch summary when range changes ──
  useEffect(() => {
    loadSummary(range);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  // ── Debounced search / risk filter for tx table ──
  useEffect(() => {
    if (txSearchRef.current) clearTimeout(txSearchRef.current);
    txSearchRef.current = setTimeout(() => {
      setTxPageNum(1);
      loadTransactions(1, txSearch, txRisk);
    }, 350);
    return () => { if (txSearchRef.current) clearTimeout(txSearchRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [txSearch, txRisk]);

  useEffect(() => {
    loadTransactions(txPageNum, txSearch, txRisk);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [txPageNum]);

  // ── Derived values ──
  const riskData = Object.entries(summary?.risk_distribution ?? {})
    .map(([name, value]) => ({ name, value }))
    .filter(({ name }) => name in RISK_COLORS)
    .sort((a, b) => {
      const order = ['LOW','MEDIUM','HIGH','CRITICAL'];
      return order.indexOf(a.name) - order.indexOf(b.name);
    });

  const domainData = Object.entries(summary?.domain_breakdown ?? {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const domainTotal = domainData.reduce((acc, d) => acc + d.value, 0);

  // ── API health display ──
  const apiOnline = apiHealth?.status === 'healthy';
  const healthStatus = apiHealth === null ? 'checking' : apiOnline ? 'online' : 'offline';

  // ─────────────────────────────────────────────────────────────────────────────
  return (
    <div className="dashboard">

      {/* ── Header ── */}
      <div className="dashboard-header">
        <div>
          <h2>GLOBAL COMMAND CENTER</h2>
          <p className="subtitle">Real-time financial transaction intelligence &amp; fraud monitoring.</p>
        </div>
        <div className="header-meta">
          <div className="header-badges">
            <span className="badge badge-blue"><Zap size={11} /> DATABASE-BACKED</span>
            <span className={`health-pill ${healthStatus}`}>
              <span className="health-dot" />
              API {healthStatus.toUpperCase()}
            </span>
            {modelReady !== null && (
              <span className={`health-pill ${modelReady ? 'online' : 'offline'}`}>
                <span className="health-dot" />
                MODEL {modelReady ? 'READY' : 'UNAVAILABLE'}
              </span>
            )}
          </div>
          {lastUpdated && (
            <span className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
              {refreshing && <RefreshCw size={10} style={{ marginLeft: 6, animation: 'spin 1s linear infinite', display: 'inline' }} />}
            </span>
          )}
        </div>
      </div>

      {/* ── KPI Row ── */}
      <div className="metrics-grid">
        <KpiCard
          title="TRANSACTIONS ANALYZED"
          value={sumLoading ? '…' : fmt(summary?.transactions_analyzed)}
          sub={`₹${fmt(summary?.total_amount_analyzed, 0)} total volume`}
          icon={Activity}
          iconClass="info"
          cardClass="card-total"
          loading={sumLoading && !summary}
        />
        <KpiCard
          title="FRAUD DETECTED"
          value={sumLoading ? '…' : fmt(summary?.fraud_detected)}
          sub="Model prediction: FRAUD/SPAM_SCAM/PHISHING"
          icon={ShieldAlert}
          iconClass="negative"
          cardClass="card-fraud"
          loading={sumLoading && !summary}
        />
        <KpiCard
          title="LEGITIMATE"
          value={sumLoading ? '…' : fmt(summary?.legitimate_transactions)}
          sub="Prediction: LEGITIMATE/LICIT"
          icon={CheckCircle}
          iconClass="positive"
          cardClass="card-legit"
          loading={sumLoading && !summary}
        />
        <KpiCard
          title="FRAUD RATE"
          value={sumLoading ? '…' : `${summary?.fraud_rate ?? 0}%`}
          sub={`Fraud predictions ÷ total (${fmt(summary?.transactions_analyzed)} records)`}
          icon={AlertTriangle}
          iconClass="amber"
          cardClass="card-rate"
          loading={sumLoading && !summary}
        />
        <KpiCard
          title="AMOUNT AT RISK"
          value={sumLoading ? '…' : fmtCurrency(summary?.amount_at_risk)}
          sub="Sum of amounts flagged as fraud"
          icon={DollarSign}
          iconClass="negative"
          cardClass="card-risk"
          loading={sumLoading && !summary}
        />
        <KpiCard
          title="AVG INFERENCE"
          value={sumLoading ? '…' : `${fmt(summary?.avg_inference_latency_ms, 1)} ms`}
          sub={`API latency: ${apiHealth?.latency_ms ?? '—'} ms · Model ${modelReady ? '✓ READY' : '✗ N/A'}`}
          icon={Cpu}
          iconClass={apiOnline ? 'positive' : 'negative'}
          cardClass="card-health"
          loading={sumLoading && !summary}
        />
      </div>

      {/* ── Charts Row ── */}
      <div className="dashboard-content">

        {/* Transaction Activity */}
        <div className="glass-panel main-chart">
          <div className="panel-header">
            <h3>TRANSACTION ACTIVITY</h3>
            <div className="panel-header-row">
              <div className="chart-controls">
                {(['24h','7d','30d'] as const).map(r => (
                  <button
                    key={r}
                    className={`range-btn ${range === r ? 'active' : ''}`}
                    onClick={() => setRange(r)}
                  >
                    {r.toUpperCase()}
                  </button>
                ))}
              </div>
              <div className="badge badge-blue"><span className="live-dot" />LIVE</div>
            </div>
          </div>
          <div className="panel-body" style={{ height: 280 }}>
            {sumError ? (
              <div className="error-state">
                <span>Failed to load timeline data.</span>
                <button className="retry-btn" onClick={() => loadSummary(range)}>Retry</button>
              </div>
            ) : summary?.timeline?.length === 0 ? (
              <div className="empty-state">
                <Activity size={32} />
                <span>No transactions in the selected range.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary?.timeline ?? []} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="legit" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="fraud" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="susp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#f59e0b" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                  <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Area type="monotone" dataKey="legitimate" stroke="#10b981" strokeWidth={2} fill="url(#legit)" dot={false} name="Legitimate" isAnimationActive={false} />
                  <Area type="monotone" dataKey="suspicious" stroke="#f59e0b" strokeWidth={1.5} fill="url(#susp)" dot={false} name="Suspicious" isAnimationActive={false} />
                  <Area type="monotone" dataKey="fraud"      stroke="#ef4444" strokeWidth={2} fill="url(#fraud)" dot={false} name="Fraud" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="glass-panel side-panel">
          <div className="panel-header">
            <h3>RISK DISTRIBUTION</h3>
          </div>
          <div className="panel-body" style={{ height: 280 }}>
            {riskData.length === 0 ? (
              <div className="empty-state">
                <AlertTriangle size={28} />
                <span>No risk data available.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskData}
                    cx="50%"
                    cy="42%"
                    innerRadius={62}
                    outerRadius={95}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {riskData.map((entry) => (
                      <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? '#64748b'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    formatter={(v) => <span style={{ color: '#94a3b8', fontSize: '0.72rem' }}>{v}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* ── Alert Center + Domain Breakdown ── */}
      <div className="alert-center-section">

        {/* Live Alerts */}
        <div className="glass-panel">
          <div className="panel-header">
            <h3>LIVE FRAUD ALERT CENTER</h3>
            <div className="panel-header-row">
              <span className="badge badge-red"><span className="live-dot" />{alerts.length} ALERTS</span>
            </div>
          </div>
          {alertsLoading ? (
            <div className="alert-list">
              {[1,2,3].map(i => (
                <div key={i} className="alert-item">
                  <div className="skeleton" style={{ width: 56, height: 22, borderRadius: 5 }} />
                  <div style={{ flex:1, display:'flex', flexDirection:'column', gap:6 }}>
                    <div className="skeleton skeleton-label" />
                    <div className="skeleton skeleton-sub" />
                  </div>
                </div>
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="alert-empty">
              <CheckCircle size={24} style={{ opacity: 0.3, marginBottom: 8 }} />
              No high-risk events in the current window.
            </div>
          ) : (
            <div className="alert-list">
              {alerts.map(a => (
                <div key={a.id} className="alert-item">
                  <span className={`alert-risk-badge ${a.risk_level}`}>{a.risk_level}</span>
                  <div className="alert-body">
                    <div className="alert-title">
                      #{a.id} · {a.domain_label} — {a.prediction}
                    </div>
                    <div className="alert-meta">
                      <span>{fmtRelative(a.timestamp)}</span>
                      <span className="alert-prob">⚠ {(a.fraud_probability * 100).toFixed(1)}%</span>
                      <span>{a.recommended_action}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Domain Breakdown */}
        <div className="glass-panel">
          <div className="panel-header">
            <h3>PAYMENT DOMAIN BREAKDOWN</h3>
            <span className="badge badge-blue">ALL TIME</span>
          </div>
          {domainData.length === 0 ? (
            <div className="empty-state">
              <Database size={28} />
              <span>No domain data available.</span>
            </div>
          ) : (
            <>
              <div className="panel-body" style={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={domainData} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 80 }}>
                    <XAxis type="number" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      width={76}
                    />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Bar dataKey="value" name="Transactions" radius={[0, 4, 4, 0]}>
                      {domainData.map((_, i) => (
                        <Cell key={i} fill={`hsl(${200 + i * 22},75%,55%)`} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="domain-row">
                {domainData.map(d => (
                  <div key={d.name} className="domain-card">
                    <div className="domain-label">{d.name}</div>
                    <div className="domain-count">{d.value}</div>
                    <div className="domain-pct">
                      {domainTotal > 0 ? ((d.value / domainTotal) * 100).toFixed(1) : 0}%
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Recent Transactions Table ── */}
      <div className="glass-panel transaction-stream">
        <div className="panel-header">
          <h3>RECENT TRANSACTIONS</h3>
          <span className="badge badge-blue">PERSISTED · SERVER-PAGED</span>
        </div>

        {/* Toolbar */}
        <div className="table-toolbar">
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={13} style={{ position: 'absolute', left: 10, color: '#475569' }} />
            <input
              className="table-search"
              style={{ paddingLeft: 30 }}
              placeholder="Search domain, prediction…"
              value={txSearch}
              onChange={e => setTxSearch(e.target.value)}
            />
          </div>
          <select
            className="filter-select"
            value={txRisk}
            onChange={e => { setTxRisk(e.target.value); setTxPageNum(1); }}
          >
            <option value="">All Risk Levels</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
          {txPage && (
            <span className="table-info">
              {txPage.total} record{txPage.total !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Table */}
        <div className="table-responsive">
          {txLoading ? (
            <table className="stream-table">
              <thead>
                <tr>
                  {['ID','Time','Domain','Amount','Probability','Risk','Prediction','Action'].map(h => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[1,2,3,4,5].map(i => (
                  <tr key={i}>
                    {[1,2,3,4,5,6,7,8].map(j => (
                      <td key={j}><div className="skeleton" style={{ height:12, width:'80%' }} /></td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : !txPage || txPage.results.length === 0 ? (
            <div className="empty-state">
              <Database size={32} />
              <span>No transactions match the current filter.</span>
            </div>
          ) : (
            <table className="stream-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>TIMESTAMP</th>
                  <th>DOMAIN</th>
                  <th>AMOUNT</th>
                  <th>PROBABILITY</th>
                  <th>RISK</th>
                  <th>PREDICTION</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {txPage.results.map(row => (
                  <tr key={row.id} className={rowClass(row.risk_level)}>
                    <td className="mono-sm">#{row.id}</td>
                    <td className="mono-sm" title={row.timestamp ?? ''}>{fmtTime(row.timestamp)}</td>
                    <td>{row.domain_label}</td>
                    <td className="mono-sm">{row.amount != null ? `₹${fmt(row.amount, 0)}` : '—'}</td>
                    <td>
                      <div className="prob-bar-wrap">
                        <span className="mono-sm" style={{ color: probColor(row.fraud_probability), minWidth: 42 }}>
                          {(row.fraud_probability * 100).toFixed(1)}%
                        </span>
                        <div className="prob-bar">
                          <div
                            className="prob-bar-fill"
                            style={{
                              width: `${row.fraud_probability * 100}%`,
                              background: probColor(row.fraud_probability),
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`risk-badge ${row.risk_level}`}>{row.risk_level}</span>
                    </td>
                    <td>
                      <span className={`pred-badge ${predClass(row.prediction)}`}>{row.prediction}</span>
                    </td>
                    <td className="mono-sm" style={{ color: '#94a3b8' }}>{row.recommended_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {txPage && txPage.pages > 1 && (
          <div className="table-pagination">
            <button
              className="page-btn"
              disabled={txPageNum <= 1}
              onClick={() => setTxPageNum(p => p - 1)}
            >
              <ChevronLeft size={13} />
            </button>
            {Array.from({ length: Math.min(txPage.pages, 7) }, (_, i) => {
              const pg = i + 1;
              return (
                <button
                  key={pg}
                  className={`page-btn ${txPageNum === pg ? 'active' : ''}`}
                  onClick={() => setTxPageNum(pg)}
                >
                  {pg}
                </button>
              );
            })}
            <button
              className="page-btn"
              disabled={txPageNum >= txPage.pages}
              onClick={() => setTxPageNum(p => p + 1)}
            >
              <ChevronRight size={13} />
            </button>
            <span className="page-info">Page {txPageNum}/{txPage.pages}</span>
          </div>
        )}
      </div>

      {/* ── Model & API Health Panel ── */}
      <div className="glass-panel">
        <div className="panel-header">
          <h3>MODEL &amp; API HEALTH</h3>
          <span className="badge badge-blue"><Server size={10} /> OPERATIONAL STATUS</span>
        </div>
        <div className="health-grid">
          <div className="health-item">
            <div className="health-item-label">Backend API</div>
            <div className="health-item-value">
              <span className={`health-pill ${healthStatus}`}>
                <span className="health-dot" />
                {healthStatus === 'checking' ? 'CHECKING' : apiOnline ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
            <div className="health-item-sub">
              {apiHealth?.latency_ms != null ? `Latency: ${apiHealth.latency_ms} ms` : 'Checking…'}
            </div>
          </div>
          <div className="health-item">
            <div className="health-item-label">ML Model</div>
            <div className="health-item-value">
              <span className={`health-pill ${modelReady === null ? 'checking' : modelReady ? 'online' : 'offline'}`}>
                <span className="health-dot" />
                {modelReady === null ? 'CHECKING' : modelReady ? 'READY' : 'UNAVAILABLE'}
              </span>
            </div>
            <div className="health-item-sub">
              {modelLatency != null ? `Readiness probe: ${modelLatency} ms` : '—'}
            </div>
          </div>
          <div className="health-item">
            <div className="health-item-label">Avg Inference</div>
            <div className="health-item-value" style={{ color: '#38bdf8' }}>
              {summary ? `${fmt(summary.avg_inference_latency_ms, 1)} ms` : '—'}
            </div>
            <div className="health-item-sub">Mean over all audit records</div>
          </div>
          <div className="health-item">
            <div className="health-item-label">Open Cases</div>
            <div className="health-item-value" style={{ color: '#f59e0b' }}>
              {summary ? fmt(summary.open_cases_count) : '—'}
            </div>
            <div className="health-item-sub">
              {summary ? `${fmt(summary.confirmed_fraud_cases)} confirmed fraud` : 'Loading…'}
            </div>
          </div>
          <div className="health-item">
            <div className="health-item-label">Total Analyzed</div>
            <div className="health-item-value" style={{ color: '#818cf8' }}>
              {summary ? fmt(summary.transactions_analyzed) : '—'}
            </div>
            <div className="health-item-sub">Persisted audit records</div>
          </div>
          <div className="health-item">
            <div className="health-item-label">Refresh Cycle</div>
            <div className="health-item-value" style={{ color: '#10b981' }}>15 s</div>
            <div className="health-item-sub">
              <Clock size={10} style={{ marginRight: 3, verticalAlign: 'middle' }} />
              {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Loading…'}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default Dashboard;
