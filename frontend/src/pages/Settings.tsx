import { useState } from 'react';
import { 
  Sliders, Bell, Key, Cpu, Save, RefreshCw, 
  CheckCircle2, Copy, Eye, EyeOff
} from 'lucide-react';
import { SoundSettings } from '../components/settings/SoundSettings';
import { soundManager } from '../audio/soundManager';
import './Settings.css';

const Settings = () => {
  // Threshold Settings
  const [highRiskThreshold, setHighRiskThreshold] = useState<number>(0.75);
  const [suspiciousThreshold, setSuspiciousThreshold] = useState<number>(0.40);
  const [autoBlockHighRisk, setAutoBlockHighRisk] = useState<boolean>(true);
  const [velocityCheckDuration, setVelocityCheckDuration] = useState<number>(300); // seconds

  // Alert Settings
  const [emailAlerts, setEmailAlerts] = useState<boolean>(true);
  const [webhookAlerts, setWebhookAlerts] = useState<boolean>(true);
  const [slackAlerts, setSlackAlerts] = useState<boolean>(false);
  const [criticalOnly, setCriticalOnly] = useState<boolean>(false);
  const [webhookUrl, setWebhookUrl] = useState<string>('https://api.internal-sec.org/hooks/fraud-alerts');

  // Security & API Settings
  const [apiKey, setApiKey] = useState<string>('fs_live_9f83a27e4b109c4d8123ef');
  const [showKey, setShowKey] = useState<boolean>(false);
  const [copiedKey, setCopiedKey] = useState<boolean>(false);
  const [enforceMfa, setEnforceMfa] = useState<boolean>(true);
  const [sessionTimeout, setSessionTimeout] = useState<number>(30); // minutes
  const [ipWhitelist, setIpWhitelist] = useState<string>('192.168.1.0/24, 10.0.4.0/16');

  // Model Retraining Settings
  const [autoRetrain, setAutoRetrain] = useState<boolean>(true);
  const [retrainSchedule, setRetrainSchedule] = useState<string>('weekly');
  const [driftTolerance, setDriftTolerance] = useState<number>(0.05);

  // Status feedback
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(true);
    soundManager.playEvent('navigation.click');
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleGenerateNewKey = () => {
    const randomHex = Array.from({ length: 24 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
    setApiKey(`fs_live_${randomHex}`);
    soundManager.playEvent('navigation.click');
  };

  const handleSave = () => {
    setSaveSuccess(true);
    soundManager.playEvent('settings.saved');
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const handleReset = () => {
    soundManager.playEvent('settings.reset');
    window.location.reload();
  };

  return (
    <div className="settings-page">
      {/* Header */}
      <div className="settings-header">
        <div>
          <h2>System Settings & Preferences</h2>
          <p>Configure risk decision boundaries, alerting pipelines, API security, and AI model policies.</p>
        </div>
        <div className="settings-actions">
          {saveSuccess && (
            <div className="save-toast">
              <CheckCircle2 size={16} />
              <span>Settings saved successfully</span>
            </div>
          )}
          <button className="btn-secondary flex-center gap-2" onClick={handleReset}>
            <RefreshCw size={14} /> Reset
          </button>
          <button className="btn-primary flex-center gap-2" onClick={handleSave}>
            <Save size={14} /> Save Configuration
          </button>
        </div>
      </div>

      {/* DEDICATED SOUND & ALERT SETTINGS SECTION */}
      <SoundSettings />

      <div className="settings-grid">
        {/* SECTION 1: DECISION ENGINE THRESHOLDS */}
        <div className="glass-panel settings-section">
          <div className="section-header">
            <div className="section-title">
              <Sliders className="icon-blue" size={20} />
              <div>
                <h3>Risk Engine Thresholds</h3>
                <span>Calibrate real-time score classification boundaries</span>
              </div>
            </div>
          </div>

          <div className="section-body">
            <div className="setting-group">
              <div className="setting-label flex-between">
                <div>
                  <label>High Risk Threshold (Block Target)</label>
                  <p>Transactions scoring above this limit trigger automatic block recommendations.</p>
                </div>
                <span className="badge badge-red font-mono">{(highRiskThreshold * 100).toFixed(0)}%</span>
              </div>
              <div className="range-container">
                <input 
                  type="range" 
                  min="0.50" 
                  max="0.95" 
                  step="0.01" 
                  value={highRiskThreshold}
                  onChange={(e) => setHighRiskThreshold(parseFloat(e.target.value))}
                  className="range-slider range-red"
                />
              </div>
            </div>

            <div className="setting-group">
              <div className="setting-label flex-between">
                <div>
                  <label>Suspicious Risk Threshold (Review Target)</label>
                  <p>Scores between suspicious and high risk require manual analyst verification.</p>
                </div>
                <span className="badge badge-amber font-mono">{(suspiciousThreshold * 100).toFixed(0)}%</span>
              </div>
              <div className="range-container">
                <input 
                  type="range" 
                  min="0.15" 
                  max="0.60" 
                  step="0.01" 
                  value={suspiciousThreshold}
                  onChange={(e) => setSuspiciousThreshold(parseFloat(e.target.value))}
                  className="range-slider range-amber"
                />
              </div>
            </div>

            <div className="setting-group flex-between toggle-group">
              <div>
                <label>Autonomous Execution Mode</label>
                <p>Automatically block transactions exceeding high-risk threshold without manual hold.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={autoBlockHighRisk}
                  onChange={(e) => setAutoBlockHighRisk(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-group">
              <div className="setting-label flex-between">
                <div>
                  <label>Velocity Check Window (Seconds)</label>
                  <p>Time window for tracking aggregate transaction frequency per user entity.</p>
                </div>
                <span className="badge badge-blue font-mono">{velocityCheckDuration}s</span>
              </div>
              <select 
                className="select-input" 
                value={velocityCheckDuration} 
                onChange={(e) => setVelocityCheckDuration(parseInt(e.target.value))}
              >
                <option value={60}>60 Seconds (1 Minute)</option>
                <option value={300}>300 Seconds (5 Minutes)</option>
                <option value={900}>900 Seconds (15 Minutes)</option>
                <option value={3600}>3600 Seconds (1 Hour)</option>
              </select>
            </div>
          </div>
        </div>

        {/* SECTION 2: NOTIFICATION & ALERTING PIPELINES */}
        <div className="glass-panel settings-section">
          <div className="section-header">
            <div className="section-title">
              <Bell className="icon-purple" size={20} />
              <div>
                <h3>Real-Time Alert Channels</h3>
                <span>Configure real-time webhooks, emails, and SOC integration</span>
              </div>
            </div>
          </div>

          <div className="section-body">
            <div className="setting-group flex-between toggle-group">
              <div>
                <label>Email Incident Notifications</label>
                <p>Send instant digests for flagged high-risk anomalies to security ops.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-group flex-between toggle-group">
              <div>
                <label>SOC Webhook Dispatcher</label>
                <p>Stream JSON payloads directly to your SIEM/SOAR platform endpoint.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={webhookAlerts}
                  onChange={(e) => setWebhookAlerts(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            {webhookAlerts && (
              <div className="setting-group">
                <label>Webhook Target Endpoint</label>
                <input 
                  type="text" 
                  className="text-input font-mono" 
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  placeholder="https://your-domain.com/api/webhooks/fraud"
                />
              </div>
            )}

            <div className="setting-group flex-between toggle-group">
              <div>
                <label>Slack/Discord Incident Channel</label>
                <p>Broadcast high-severity risk events into dedicated response channel.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={slackAlerts}
                  onChange={(e) => setSlackAlerts(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-group flex-between toggle-group">
              <div>
                <label>Critical Severity Filter Only</label>
                <p>Suppress low and medium risk logs from dispatching external alerts.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={criticalOnly}
                  onChange={(e) => setCriticalOnly(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        {/* SECTION 3: API KEYS & SECURITY CONTROLS */}
        <div className="glass-panel settings-section">
          <div className="section-header">
            <div className="section-title">
              <Key className="icon-amber" size={20} />
              <div>
                <h3>API Authentication & Security</h3>
                <span>Manage bearer tokens and API gateway access controls</span>
              </div>
            </div>
          </div>

          <div className="section-body">
            <div className="setting-group">
              <label>Live Production API Secret Key</label>
              <div className="api-key-box">
                <input 
                  type={showKey ? "text" : "password"} 
                  className="text-input font-mono readonly-input" 
                  value={apiKey} 
                  readOnly 
                />
                <button className="icon-btn" onClick={() => setShowKey(!showKey)} title={showKey ? "Hide key" : "Show key"}>
                  {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
                <button className="icon-btn" onClick={handleCopyKey} title="Copy key">
                  {copiedKey ? <CheckCircle2 size={16} className="text-green" /> : <Copy size={16} />}
                </button>
                <button className="btn-secondary btn-sm" onClick={handleGenerateNewKey}>
                  Rotate
                </button>
              </div>
            </div>

            <div className="setting-group flex-between toggle-group">
              <div>
                <label>Enforce Multi-Factor Authentication (MFA)</label>
                <p>Require TOTP token verification for all administrative actions.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={enforceMfa}
                  onChange={(e) => setEnforceMfa(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-group">
              <label>Session Inactivity Timeout (Minutes)</label>
              <select 
                className="select-input" 
                value={sessionTimeout}
                onChange={(e) => setSessionTimeout(parseInt(e.target.value))}
              >
                <option value={15}>15 Minutes</option>
                <option value={30}>30 Minutes (Standard)</option>
                <option value={60}>60 Minutes</option>
                <option value={120}>120 Minutes</option>
              </select>
            </div>

            <div className="setting-group">
              <label>Authorized Subnet Whitelist (CIDR notation)</label>
              <p className="text-xs text-muted mb-2">Restricts API access to defined corporate IP ranges.</p>
              <input 
                type="text" 
                className="text-input font-mono" 
                value={ipWhitelist}
                onChange={(e) => setIpWhitelist(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* SECTION 4: MODEL RETRAINING & DRIFT POLICIES */}
        <div className="glass-panel settings-section">
          <div className="section-header">
            <div className="section-title">
              <Cpu className="icon-green" size={20} />
              <div>
                <h3>Model Retraining & Governance</h3>
                <span>Autonomous MLOps retraining pipelines and drift constraints</span>
              </div>
            </div>
          </div>

          <div className="section-body">
            <div className="setting-group flex-between toggle-group">
              <div>
                <label>Automated Continuous Retraining</label>
                <p>Trigger background retraining pipeline when feedback queue exceeds 1,000 cases.</p>
              </div>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={autoRetrain}
                  onChange={(e) => setAutoRetrain(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-group">
              <label>Retraining Recurrence Schedule</label>
              <select 
                className="select-input" 
                value={retrainSchedule}
                onChange={(e) => setRetrainSchedule(e.target.value)}
              >
                <option value="daily">Daily Cron (00:00 UTC)</option>
                <option value="weekly">Weekly (Sunday 02:00 UTC)</option>
                <option value="biweekly">Bi-weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            <div className="setting-group">
              <div className="setting-label flex-between">
                <div>
                  <label>Data Drift Alerting Threshold (PSI Metric)</label>
                  <p>Population Stability Index shift tolerance before triggering alert.</p>
                </div>
                <span className="badge badge-amber font-mono">{driftTolerance} PSI</span>
              </div>
              <input 
                type="range" 
                min="0.01" 
                max="0.20" 
                step="0.01" 
                value={driftTolerance}
                onChange={(e) => setDriftTolerance(parseFloat(e.target.value))}
                className="range-slider range-amber"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
