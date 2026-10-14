import { useState, useEffect } from 'react';
import { ShieldAlert } from 'lucide-react';
import { soundManager } from '../audio/soundManager';
import './CaseManagement.css';

const API_BASE = '/api';

interface CaseHistory {
  id: number;
  timestamp: string;
  action: string;
  previous_status: string;
  new_status: string;
  analyst_id: string;
  notes: string;
}

interface Case {
  id: string;
  transaction_id: string;
  severity: string;
  status: string;
  resolution: string | null;
  fraud_probability: number;
  created_at: string;
  updated_at: string;
  analyst_notes: string | null;
}

const CaseManagement: React.FC = () => {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [caseHistory, setCaseHistory] = useState<CaseHistory[]>([]);
  const [noteInput, setNoteInput] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchCases();
  }, [filter]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const url = filter === 'ALL' ? `${API_BASE}/cases` : `${API_BASE}/cases?status=${filter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setCases(data);
        if (selectedCase) {
          const updated = data.find((c: Case) => c.id === selectedCase.id);
          if (updated) setSelectedCase(updated);
        }
      }
    } catch (e) {
      console.error("Failed to fetch cases", e);
    } finally {
      setLoading(false);
    }
  };

  const loadCaseDetails = async (caseId: string) => {
    try {
      const res = await fetch(`${API_BASE}/cases/${caseId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedCase(data);
        setCaseHistory(data.history || []);
      }
    } catch (e) {
      console.error("Failed to fetch case details", e);
    }
  };

  const updateStatus = async (newStatus: string, resolution?: string) => {
    if (!selectedCase) return;
    setUpdating(true);
    try {
      const res = await fetch(`${API_BASE}/cases/${selectedCase.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          resolution,
          notes: noteInput || undefined,
          analyst_id: 'analyst_1', // mocked user
        }),
      });
      if (res.ok) {
        soundManager.playEvent('case.status_updated');
        setNoteInput('');
        await fetchCases();
        await loadCaseDetails(selectedCase.id);
      } else {
        soundManager.playEvent('case.update_failed');
      }
    } catch (e) {
      console.error("Failed to update status", e);
      soundManager.playEvent('case.update_failed');
    } finally {
      setUpdating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN': return <span className="badge badge-red">OPEN</span>;
      case 'UNDER_REVIEW': return <span className="badge badge-amber">UNDER REVIEW</span>;
      case 'RESOLVED': return <span className="badge badge-green">RESOLVED</span>;
      default: return <span className="badge">{status}</span>;
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL': return <span className="badge badge-red">{sev}</span>;
      case 'HIGH': return <span className="badge badge-amber">{sev}</span>;
      case 'MEDIUM': return <span className="badge badge-blue">{sev}</span>;
      case 'LOW': return <span className="badge badge-green">{sev}</span>;
      default: return <span className="badge">{sev}</span>;
    }
  };

  return (
    <div className="cases-page">
      <div className="analyze-header">
        <ShieldAlert size={22} className="page-icon" />
        <div>
          <h2>CASE MANAGEMENT</h2>
          <p className="subtitle">Investigate, track, and resolve suspected fraud incidents.</p>
        </div>
      </div>

      <div className="cases-layout">
        {/* Left Column: Case List */}
        <div className="glass-panel cases-list-panel">
          <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h3>ACTIVE CASES</h3>
            <div className="filter-group">
              <select value={filter} onChange={e => setFilter(e.target.value)} className="form-input" style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
                <option value="ALL">All Status</option>
                <option value="OPEN">Open</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="RESOLVED">Resolved</option>
              </select>
            </div>
          </div>
          
          <div className="cases-list">
            {loading ? (
              <div className="p-4 text-center text-muted">Loading cases...</div>
            ) : cases.length === 0 ? (
              <div className="p-4 text-center text-muted">No cases found.</div>
            ) : (
              cases.map(c => (
                <div 
                  key={c.id} 
                  className={`case-item ${selectedCase?.id === c.id ? 'active' : ''}`}
                  onClick={() => loadCaseDetails(c.id)}
                >
                  <div className="case-item-header">
                    <span className="case-id mono">{c.id}</span>
                    <span className="case-time mono">{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                  <div className="case-item-meta">
                    <span className="case-tx mono">TX: {c.transaction_id}</span>
                    <span className={`case-prob mono ${c.fraud_probability > 0.5 ? 'red-text' : 'green-text'}`}>
                      {(c.fraud_probability * 100).toFixed(1)}% RISK
                    </span>
                  </div>
                  <div className="case-item-badges">
                    {getStatusBadge(c.status)}
                    {getSeverityBadge(c.severity)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Case Details */}
        <div className="case-details-panel">
          {!selectedCase ? (
            <div className="glass-panel" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              Select a case to view details
            </div>
          ) : (
            <div className="glass-panel detail-content">
              <div className="panel-header">
                <h3>CASE DETAILS: {selectedCase.id}</h3>
                {getStatusBadge(selectedCase.status)}
              </div>
              
              <div className="panel-body">
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="dl">TRANSACTION ID</div>
                    <div className="dv mono">{selectedCase.transaction_id}</div>
                  </div>
                  <div className="detail-item">
                    <div className="dl">SEVERITY</div>
                    <div className="dv">{getSeverityBadge(selectedCase.severity)}</div>
                  </div>
                  <div className="detail-item">
                    <div className="dl">FRAUD PROBABILITY</div>
                    <div className="dv mono red-text">{(selectedCase.fraud_probability * 100).toFixed(2)}%</div>
                  </div>
                  <div className="detail-item">
                    <div className="dl">CREATED AT</div>
                    <div className="dv mono">{new Date(selectedCase.created_at).toLocaleString()}</div>
                  </div>
                </div>

                {/* Actions */}
                <div className="case-actions">
                  <h4>UPDATE STATUS</h4>
                  <div className="action-buttons">
                    {selectedCase.status === 'OPEN' && (
                      <button className="btn-action amber" onClick={() => updateStatus('UNDER_REVIEW')} disabled={updating}>
                        Start Review
                      </button>
                    )}
                    {(selectedCase.status === 'OPEN' || selectedCase.status === 'UNDER_REVIEW') && (
                      <>
                        <button className="btn-action green" onClick={() => updateStatus('RESOLVED', 'FALSE_POSITIVE')} disabled={updating}>
                          Resolve: False Positive
                        </button>
                        <button className="btn-action red" onClick={() => updateStatus('RESOLVED', 'CONFIRMED_FRAUD')} disabled={updating}>
                          Resolve: Confirmed Fraud
                        </button>
                      </>
                    )}
                    {selectedCase.status === 'RESOLVED' && (
                      <button className="btn-action amber" onClick={() => updateStatus('UNDER_REVIEW')} disabled={updating}>
                        Re-open Case
                      </button>
                    )}
                  </div>
                  
                  <textarea 
                    className="form-input case-notes-input" 
                    placeholder="Add notes for this status change..." 
                    value={noteInput}
                    onChange={(e) => setNoteInput(e.target.value)}
                  />
                </div>

                {/* Notes History */}
                <div className="case-history">
                  <h4>CASE HISTORY & NOTES</h4>
                  <div className="history-timeline">
                    {caseHistory.map((h, i) => (
                      <div key={i} className="history-item">
                        <div className="history-time mono">{new Date(h.timestamp).toLocaleString()}</div>
                        <div className="history-action">
                          <strong>{h.analyst_id}</strong> {h.action === 'STATUS_CHANGED' ? `changed status from ${h.previous_status} to ${h.new_status}` : 'added a note'}
                        </div>
                        {h.notes && <div className="history-notes">{h.notes}</div>}
                      </div>
                    ))}
                    {caseHistory.length === 0 && <div className="text-muted">No history found.</div>}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CaseManagement;
