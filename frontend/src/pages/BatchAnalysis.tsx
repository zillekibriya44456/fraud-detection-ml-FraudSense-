import { useState, useRef, useCallback } from 'react';
import { Upload, Play, Download, CheckCircle, AlertTriangle, Loader, Layers } from 'lucide-react';
import { soundManager } from '../audio/soundManager';
import './BatchAnalysis.css';

const API_BASE = '/api';

interface BatchResult {
  fraud_probability: number;
  risk_level: string;
  recommended_action: string;
  prediction: string;
  inference_latency_ms: number;
}

const BatchAnalysis: React.FC = () => {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [csvRows, setCsvRows] = useState<any[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<BatchResult[]>([]);
  const [stats, setStats] = useState<{ fraud: number; legit: number; errors: number; avgLatency: number } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const parseCSV = (text: string): any[] => {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    return lines.slice(1).map(line => {
      const vals = line.split(',');
      const row: any = {};
      headers.forEach((h, i) => { row[h] = vals[i]?.trim(); });
      return row;
    });
  };

  const handleFile = (f: File) => {
    setParseError(null);
    setResults([]);
    setStats(null);
    setProgress(0);
    setFile(f);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const rows = parseCSV(text);
        if (!rows.length) throw new Error('CSV is empty or malformed.');
        const required = ['step', 'type', 'amount', 'oldbalanceorg', 'oldbalancedest'];
        const headers = Object.keys(rows[0]).map(k => k.toLowerCase());
        const missing = required.filter(r => !headers.includes(r));
        if (missing.length) throw new Error(`Missing columns: ${missing.join(', ')}`);
        setCsvRows(rows);
      } catch (err: any) {
        setParseError(err.message);
        setFile(null);
      }
    };
    reader.readAsText(f);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith('.csv')) handleFile(f);
    else setParseError('Please drop a valid .csv file.');
  }, []);

  const runBatch = async () => {
    if (!csvRows.length) return;
    setProcessing(true);
    setProgress(0);
    setResults([]);
    setStats(null);
    soundManager.playEvent('transaction.submitted');

    const CHUNK = 10;
    const allResults: BatchResult[] = [];
    let fraudCount = 0;
    let errors = 0;
    let totalLatency = 0;

    for (let i = 0; i < csvRows.length; i += CHUNK) {
      const chunk = csvRows.slice(i, i + CHUNK);
      const transactions = chunk.map((row: any, idx: number) => ({
        transaction_id: row.transaction_id || `BATCH-${i + idx}`,
        step: parseInt(row.step) || 1,
        type: (row.type || 'TRANSFER').toUpperCase(),
        amount: parseFloat(row.amount) || 0,
        oldbalanceOrg: parseFloat(row.oldbalanceorg || row.oldbalanceorig) || 0,
        oldbalanceDest: parseFloat(row.oldbalancedest) || 0,
        nameOrig: row.nameorig || 'BATCH_C',
        nameDest: row.namedest || 'BATCH_M',
        channel: row.channel || 'BATCH',
      }));

      try {
        const res = await fetch(`${API_BASE}/predict_batch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ transactions }),
        });
        if (res.ok) {
          const data = await res.json();
          data.results.forEach((r: BatchResult) => {
            allResults.push(r);
            if (r.prediction.toUpperCase() === 'FRAUD') fraudCount++;
            totalLatency += r.inference_latency_ms || 0;
          });
        } else {
          errors += chunk.length;
        }
      } catch { errors += chunk.length; }

      setProgress(Math.round(((i + CHUNK) / csvRows.length) * 100));
    }

    setResults(allResults);
    setStats({
      fraud: fraudCount,
      legit: allResults.length - fraudCount,
      errors,
      avgLatency: allResults.length ? totalLatency / allResults.length : 0,
    });
    setProcessing(false);

    if (errors > 0 && allResults.length === 0) {
      soundManager.playEvent('transaction.failed');
    } else if (fraudCount > 0) {
      soundManager.playEvent('paysim.high_risk');
    } else {
      soundManager.playEvent('dashboard.refresh');
    }
  };

  const downloadResults = () => {
    if (!results.length) return;
    const headers = ['prediction', 'fraud_probability', 'risk_level', 'recommended_action', 'inference_latency_ms'];
    const csv = [
      headers.join(','),
      ...results.map(r => headers.map(h => r[h as keyof BatchResult]).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fraudsense_results.csv';
    a.click();
  };

  return (
    <div className="batch-page">
      <div className="analyze-header">
        <Layers size={22} className="page-icon" />
        <div>
          <h2>BATCH ANALYSIS</h2>
          <p className="subtitle">Process multiple transactions from a CSV file.</p>
        </div>
      </div>

      {/* Upload Zone */}
      {!file && (
        <div
          className={`glass-panel drop-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
        >
          <input ref={fileRef} type="file" accept=".csv" hidden onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
          <Upload size={36} className="upload-icon" />
          <p className="drop-title">Drop CSV or click to browse</p>
          <p className="drop-hint">Required columns: step, type, amount, oldbalanceOrg, oldbalanceDest</p>
        </div>
      )}

      {parseError && (
        <div className="glass-panel error-panel">
          <AlertTriangle size={16} />
          {parseError}
        </div>
      )}

      {/* File info */}
      {file && !parseError && (
        <div className="glass-panel file-info">
          <div className="file-meta">
            <CheckCircle size={18} style={{color: 'var(--accent-green)'}} />
            <div>
              <div className="file-name">{file.name}</div>
              <div className="file-detail">{csvRows.length} transactions &nbsp;·&nbsp; {(file.size / 1024).toFixed(1)} KB</div>
            </div>
          </div>
          <div className="file-actions">
            <button className="btn-secondary" onClick={() => { setFile(null); setCsvRows([]); setResults([]); setStats(null); }}>
              Clear
            </button>
            <button className="btn-analyze small" onClick={runBatch} disabled={processing}>
              {processing ? <Loader size={14} className="spin" /> : <Play size={14} />}
              {processing ? `Processing... ${progress}%` : 'START ANALYSIS'}
            </button>
          </div>
        </div>
      )}

      {/* Progress bar */}
      {processing && (
        <div className="glass-panel progress-panel">
          <div className="flex-between" style={{padding: '12px 20px 6px'}}>
            <span className="text-sm" style={{color: 'var(--text-secondary)'}}>PROCESSING TRANSACTIONS</span>
            <span className="data-value" style={{fontSize: '0.85rem'}}>{Math.round(progress * csvRows.length / 100)} / {csvRows.length}</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{width: `${progress}%`}} />
          </div>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <>
          <div className="batch-stats">
            <div className="glass-panel stat-card">
              <div className="stat-value">{results.length}</div>
              <div className="stat-label">PROCESSED</div>
            </div>
            <div className="glass-panel stat-card fraud">
              <div className="stat-value red-text">{stats.fraud}</div>
              <div className="stat-label">FRAUD DETECTED</div>
            </div>
            <div className="glass-panel stat-card legit">
              <div className="stat-value green-text">{stats.legit}</div>
              <div className="stat-label">LEGITIMATE</div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-value">{stats.errors}</div>
              <div className="stat-label">ERRORS</div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-value mono">{stats.avgLatency.toFixed(1)}ms</div>
              <div className="stat-label">AVG LATENCY</div>
            </div>
          </div>

          <div className="glass-panel">
            <div className="panel-header">
              <h3>BATCH RESULTS</h3>
              <button className="btn-secondary small" onClick={downloadResults}>
                <Download size={14} /> Download CSV
              </button>
            </div>
            <div className="table-responsive">
              <table className="stream-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>STATUS</th>
                    <th>FRAUD PROBABILITY</th>
                    <th>RISK LEVEL</th>
                    <th>DECISION</th>
                    <th>LATENCY</th>
                  </tr>
                </thead>
                <tbody>
                  {results.slice(0, 50).map((r, i) => (
                    <tr key={i}>
                      <td className="data-value text-muted">{i + 1}</td>
                      <td>
                        <span className={`badge ${r.prediction.toUpperCase() === 'FRAUD' ? 'badge-red' : 'badge-green'}`}>
                          {r.prediction}
                        </span>
                      </td>
                      <td className={`data-value ${r.fraud_probability > 0.5 ? 'red-text' : 'green-text'}`}>
                        {(r.fraud_probability * 100).toFixed(1)}%
                      </td>
                      <td><span className={`badge ${r.risk_level === 'LOW' ? 'badge-green' : r.risk_level === 'CRITICAL' ? 'badge-red' : 'badge-amber'}`}>{r.risk_level}</span></td>
                      <td><span className={`badge ${r.recommended_action === 'APPROVE' ? 'badge-green' : r.recommended_action === 'BLOCK' ? 'badge-red' : 'badge-amber'}`}>{r.recommended_action}</span></td>
                      <td className="data-value">{r.inference_latency_ms?.toFixed(1)}ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {results.length > 50 && (
                <div style={{padding: '12px 16px', color: 'var(--text-muted)', fontSize: '0.8rem'}}>
                  Showing 50 of {results.length} results. Download CSV for full dataset.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default BatchAnalysis;
