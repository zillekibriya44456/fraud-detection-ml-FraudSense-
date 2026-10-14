import React, { useState } from 'react';
import {
  Volume2,
  VolumeX,
  Volume1,
  ShieldAlert,
  Play,
  RotateCcw,
  Sparkles,
  Clock,
  Sliders,
  Filter,
  CheckCircle2,
  ListMusic
} from 'lucide-react';
import { useSoundSettings } from '../../audio/useSoundSettings';
import type { SoundCategory, SoundTheme } from '../../audio/soundTypes';
import './SoundSettings.css';

const SOUND_CATEGORIES_PREVIEW: Array<{
  category: SoundCategory;
  name: string;
  description: string;
  badgeClass: string;
  priority: string;
}> = [
  { category: 'ui', name: 'UI Click / Navigation', description: 'Subtle high-frequency click on buttons or menu links', badgeClass: 'badge-blue', priority: 'LOW' },
  { category: 'processing', name: 'Pipeline Processing', description: 'Dual-pulse frequency when transaction or URL scan begins', badgeClass: 'badge-blue', priority: 'INFO' },
  { category: 'complete', name: 'Analysis Complete', description: 'Gentle ascending chime upon inference resolution', badgeClass: 'badge-green', priority: 'LOW' },
  { category: 'approve', name: 'Approved / Low Risk', description: 'Harmonic confirmation chord for safe transactions', badgeClass: 'badge-green', priority: 'LOW' },
  { category: 'verify', name: 'Verify / Caution', description: 'Two-tone attention chord for suspicious/review signals', badgeClass: 'badge-amber', priority: 'MEDIUM' },
  { category: 'high_risk', name: 'High Risk Warning', description: 'Urgent sawtooth pulse indicating high fraud probability', badgeClass: 'badge-amber', priority: 'HIGH' },
  { category: 'block', name: 'Block Decision', description: 'Unmistakable low descending tone for blocked events', badgeClass: 'badge-red', priority: 'HIGH' },
  { category: 'critical', name: 'Critical Attack Alarm', description: 'Triple high-urgency burst for confirmed attacks or zero-days', badgeClass: 'badge-red', priority: 'CRITICAL' },
  { category: 'error', name: 'System / API Error', description: 'Downward descending error tone for network or pipeline faults', badgeClass: 'badge-amber', priority: 'NORMAL' },
  { category: 'drift', name: 'Model Drift Warning', description: 'Modulated tone for PSI shift or statistical concept drift', badgeClass: 'badge-purple', priority: 'HIGH' },
  { category: 'case', name: 'Case Incident Notification', description: 'Ascending dual chime when a new investigation case is opened', badgeClass: 'badge-blue', priority: 'HIGH' },
];

export const SoundSettings: React.FC = () => {
  const {
    settings,
    isTesting,
    testProgress,
    setMasterEnabled,
    setFraudAlertsEnabled,
    setMasterVolume,
    setAlertVolume,
    setMuted,
    setQuietMode,
    setQuietHours,
    setSoundTheme,
    setDefaultCooldown,
    setEventConfig,
    previewSound,
    resetSoundSettings,
    testAllSounds,
  } = useSoundSettings();

  const [activeTab, setActiveTab] = useState<'overview' | 'events'>('overview');
  const [eventFilter, setEventFilter] = useState<string>('');
  const [sectionFilter, setSectionFilter] = useState<string>('all');
  const [feedbackToast, setFeedbackToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setFeedbackToast(msg);
    setTimeout(() => setFeedbackToast(null), 2500);
  };

  const handleReset = () => {
    resetSoundSettings();
    showToast('Sound preferences reset to default');
  };

  const allEvents = Object.values(settings.events || {});
  const sections = Array.from(new Set(allEvents.map((e) => e.section)));

  const filteredEvents = allEvents.filter((e) => {
    const matchesSection = sectionFilter === 'all' || e.section === sectionFilter;
    const matchesQuery =
      eventFilter === '' ||
      e.name.toLowerCase().includes(eventFilter.toLowerCase()) ||
      e.id.toLowerCase().includes(eventFilter.toLowerCase()) ||
      e.subsection.toLowerCase().includes(eventFilter.toLowerCase());
    return matchesSection && matchesQuery;
  });

  return (
    <div className="glass-panel sound-settings-panel">
      {/* Header */}
      <div className="sound-settings-header">
        <div className="sound-title-area">
          <div className="sound-header-icon-wrap">
            {settings.muted || !settings.masterEnabled ? (
              <VolumeX className="sound-icon-red" size={24} />
            ) : settings.masterVolume > 0.5 ? (
              <Volume2 className="sound-icon-cyan" size={24} />
            ) : (
              <Volume1 className="sound-icon-cyan" size={24} />
            )}
          </div>
          <div>
            <div className="sound-header-title-row">
              <h3>Intelligent Audio & Fraud Alarm System</h3>
              <span className={`badge ${settings.masterEnabled && !settings.muted ? 'badge-green' : 'badge-red'}`}>
                {settings.muted ? 'MUTED' : settings.masterEnabled ? 'ACTIVE' : 'DISABLED'}
              </span>
              {settings.quietMode && <span className="badge badge-amber">QUIET MODE</span>}
            </div>
            <p className="sound-header-subtitle">
              Context-aware audio telemetry, priority-ranked fraud alarms, and synthesized sound effects
            </p>
          </div>
        </div>

        <div className="sound-header-actions">
          {feedbackToast && (
            <div className="sound-toast">
              <CheckCircle2 size={15} />
              <span>{feedbackToast}</span>
            </div>
          )}
          <button
            type="button"
            className="sound-btn sound-btn-secondary"
            onClick={testAllSounds}
            disabled={isTesting || settings.muted || !settings.masterEnabled}
            title="Preview all synthesized sound cues in sequence"
          >
            <Sparkles size={14} className={isTesting ? 'spin-icon' : ''} />
            <span>{isTesting ? `Testing (${testProgress?.index}/${testProgress?.total})...` : 'Test All Sounds'}</span>
          </button>
          <button
            type="button"
            className="sound-btn sound-btn-outline"
            onClick={handleReset}
            title="Restore default audio configuration"
          >
            <RotateCcw size={14} />
            <span>Reset Defaults</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="sound-tabs">
        <button
          type="button"
          className={`sound-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Sliders size={15} />
          <span>Master Controls & Themes</span>
        </button>
        <button
          type="button"
          className={`sound-tab ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          <ListMusic size={15} />
          <span>Granular Event Matrix ({allEvents.length})</span>
        </button>
      </div>

      {activeTab === 'overview' ? (
        <div className="sound-overview-content">
          {/* PRIMARY SWITCHES GRID */}
          <div className="sound-switches-grid">
            {/* Master Switch */}
            <div className="sound-switch-card">
              <div className="switch-card-info">
                <div className="switch-icon-box cyan">
                  <Volume2 size={18} />
                </div>
                <div>
                  <h4>Master Audio</h4>
                  <p>Global enable or disable switch for all interface sounds</p>
                </div>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.masterEnabled}
                  onChange={(e) => setMasterEnabled(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            {/* Fraud Alerts Switch */}
            <div className="sound-switch-card">
              <div className="switch-card-info">
                <div className="switch-icon-box red">
                  <ShieldAlert size={18} />
                </div>
                <div>
                  <h4>Fraud Alarms & Alerts</h4>
                  <p>Audible alerts for suspicious, high-risk, and block decisions</p>
                </div>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.fraudAlertsEnabled}
                  onChange={(e) => setFraudAlertsEnabled(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            {/* Global Mute */}
            <div className="sound-switch-card">
              <div className="switch-card-info">
                <div className="switch-icon-box amber">
                  <VolumeX size={18} />
                </div>
                <div>
                  <h4>Quick Mute</h4>
                  <p>Temporarily silence all playback without losing preferences</p>
                </div>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.muted}
                  onChange={(e) => setMuted(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            {/* Quiet Mode */}
            <div className="sound-switch-card">
              <div className="switch-card-info">
                <div className="switch-icon-box purple">
                  <Clock size={18} />
                </div>
                <div>
                  <h4>Quiet Mode (Critical Only)</h4>
                  <p>Mute routine clicks and approvals; only play CRITICAL attacks</p>
                </div>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.quietMode}
                  onChange={(e) => setQuietMode(e.target.checked)}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>

          {/* VOLUMES & THEME CONTROLS */}
          <div className="sound-controls-grid">
            {/* Master Volume */}
            <div className="sound-card">
              <div className="sound-card-header">
                <div>
                  <h4>Master Volume</h4>
                  <span className="text-muted">Scales all synthesized sound effects</span>
                </div>
                <span className="volume-badge">{Math.round(settings.masterVolume * 100)}%</span>
              </div>
              <div className="sound-range-wrap">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={settings.masterVolume}
                  onChange={(e) => setMasterVolume(parseFloat(e.target.value))}
                  className="range-slider range-cyan"
                  disabled={!settings.masterEnabled || settings.muted}
                />
                <button
                  type="button"
                  className="sound-mini-preview-btn"
                  onClick={() => previewSound('complete')}
                  title="Test Master Volume"
                >
                  <Play size={12} /> Test
                </button>
              </div>
            </div>

            {/* Alert Volume */}
            <div className="sound-card">
              <div className="sound-card-header">
                <div>
                  <h4>Fraud Alarm Volume</h4>
                  <span className="text-muted">Volume multiplier for High & Critical alarms</span>
                </div>
                <span className="volume-badge alert">{Math.round(settings.alertVolume * 100)}%</span>
              </div>
              <div className="sound-range-wrap">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={settings.alertVolume}
                  onChange={(e) => setAlertVolume(parseFloat(e.target.value))}
                  className="range-slider range-red"
                  disabled={!settings.masterEnabled || settings.muted}
                />
                <button
                  type="button"
                  className="sound-mini-preview-btn red"
                  onClick={() => previewSound('critical')}
                  title="Test Critical Alarm Volume"
                >
                  <Play size={12} /> Test
                </button>
              </div>
            </div>

            {/* Audio Profile / Theme */}
            <div className="sound-card">
              <div className="sound-card-header">
                <div>
                  <h4>Synthesis Audio Theme</h4>
                  <span className="text-muted">Acoustic profile and harmonic waveform style</span>
                </div>
              </div>
              <div className="theme-select-row">
                <select
                  className="select-input font-mono"
                  value={settings.soundTheme}
                  onChange={(e) => {
                    const t = e.target.value as SoundTheme;
                    setSoundTheme(t);
                    setTimeout(() => previewSound('approve'), 50);
                  }}
                >
                  <option value="CYBER_FINTECH">Cyber Fintech (Modern Harmonic Sine)</option>
                  <option value="MINIMAL_DIGITAL">Minimal Digital (Soft Triangle Cues)</option>
                  <option value="TACTICAL_ALARM">Tactical Security (High-Def Sawtooth)</option>
                </select>
                <button
                  type="button"
                  className="sound-mini-preview-btn"
                  onClick={() => previewSound('high_risk')}
                  title="Sample Theme"
                >
                  <Play size={12} /> Sample
                </button>
              </div>
            </div>

            {/* Cooldown & Quiet Hours */}
            <div className="sound-card">
              <div className="sound-card-header">
                <div>
                  <h4>Deduplication & Quiet Hours</h4>
                  <span className="text-muted">Throttle repetitive triggers and schedule quiet times</span>
                </div>
              </div>
              <div className="cooldown-and-hours-row">
                <div className="cooldown-input-group">
                  <label className="text-xs text-muted">Alert Cooldown (ms):</label>
                  <input
                    type="number"
                    min={100}
                    max={5000}
                    step={100}
                    value={settings.defaultCooldownMs || 1000}
                    onChange={(e) => setDefaultCooldown(parseInt(e.target.value) || 1000)}
                    className="text-input font-mono compact"
                  />
                </div>
                <div className="quiet-hours-group">
                  <label className="text-xs text-muted flex-between">
                    <span>Quiet Hours:</span>
                    <input
                      type="checkbox"
                      checked={settings.quietHoursEnabled}
                      onChange={(e) => setQuietHours(e.target.checked)}
                    />
                  </label>
                  <div className="time-range-row">
                    <input
                      type="time"
                      value={settings.quietHoursStart || '22:00'}
                      onChange={(e) => setQuietHours(settings.quietHoursEnabled, e.target.value, settings.quietHoursEnd)}
                      disabled={!settings.quietHoursEnabled}
                      className="text-input font-mono compact"
                    />
                    <span className="text-muted">to</span>
                    <input
                      type="time"
                      value={settings.quietHoursEnd || '07:00'}
                      onChange={(e) => setQuietHours(settings.quietHoursEnabled, settings.quietHoursStart, e.target.value)}
                      disabled={!settings.quietHoursEnabled}
                      className="text-input font-mono compact"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* PALETTE EXPLORER */}
          <div className="sound-palette-section">
            <div className="palette-header">
              <h4>Audio Palette & Tone Library</h4>
              <span className="text-muted text-xs">
                Zero external dependencies — synthesized directly via Web Audio API oscillators and gain envelopes
              </span>
            </div>
            <div className="palette-grid">
              {SOUND_CATEGORIES_PREVIEW.map((item) => (
                <div key={item.category} className="palette-item">
                  <div className="palette-info">
                    <div className="palette-name-row">
                      <span className="palette-name">{item.name}</span>
                      <span className={`badge ${item.badgeClass} compact`}>{item.priority}</span>
                    </div>
                    <span className="palette-desc">{item.description}</span>
                  </div>
                  <button
                    type="button"
                    className="palette-play-btn"
                    onClick={() => previewSound(item.category)}
                    title={`Play ${item.name}`}
                  >
                    <Play size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* GRANULAR EVENTS MATRIX */
        <div className="sound-events-content">
          <div className="events-filter-bar">
            <div className="events-search-wrap">
              <input
                type="text"
                placeholder="Filter events (e.g., upi, credit_card, link, block)..."
                value={eventFilter}
                onChange={(e) => setEventFilter(e.target.value)}
                className="text-input"
              />
            </div>
            <div className="events-section-select">
              <Filter size={14} className="text-muted" />
              <select
                className="select-input"
                value={sectionFilter}
                onChange={(e) => setSectionFilter(e.target.value)}
              >
                <option value="all">All Modules ({allEvents.length})</option>
                {sections.map((sec) => (
                  <option key={sec} value={sec}>
                    {sec}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="events-table-wrap">
            <table className="events-table">
              <thead>
                <tr>
                  <th style={{ width: '60px' }}>Active</th>
                  <th>Event Name & Module</th>
                  <th style={{ width: '130px' }}>Priority</th>
                  <th style={{ width: '140px' }}>Tone Category</th>
                  <th style={{ width: '140px' }}>Volume</th>
                  <th style={{ width: '80px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((evt) => (
                  <tr key={evt.id} className={evt.enabled ? '' : 'event-row-disabled'}>
                    <td className="text-center">
                      <input
                        type="checkbox"
                        checked={evt.enabled}
                        onChange={(e) => setEventConfig(evt.id, { enabled: e.target.checked })}
                      />
                    </td>
                    <td>
                      <div className="event-meta">
                        <span className="event-name">{evt.name}</span>
                        <div className="event-path font-mono text-muted">
                          <span>{evt.section}</span> &rsaquo; <span>{evt.subsection}</span> &bull; <code>{evt.id}</code>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          evt.priority === 'CRITICAL'
                            ? 'badge-red'
                            : evt.priority === 'HIGH'
                            ? 'badge-amber'
                            : 'badge-blue'
                        }`}
                      >
                        {evt.priority}
                      </span>
                    </td>
                    <td>
                      <span className="font-mono text-xs text-muted">{evt.soundCategory}</span>
                    </td>
                    <td>
                      <div className="event-vol-row">
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={evt.volume}
                          onChange={(e) => setEventConfig(evt.id, { volume: parseFloat(e.target.value) })}
                          className="range-slider range-cyan compact"
                          disabled={!evt.enabled}
                        />
                        <span className="font-mono text-xs">{Math.round(evt.volume * 100)}%</span>
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="sound-play-row-btn"
                        onClick={() => previewSound(evt.soundCategory)}
                        title="Preview tone"
                      >
                        <Play size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
