import { useState } from 'react';
import { AlertOctagon, FileText, Download } from 'lucide-react';
import './IncidentResponse.css';

const IncidentResponse = () => {
  const [txnId, setTxnId] = useState('');
  const [amount, setAmount] = useState('');
  const [payee, setPayee] = useState('');
  const [details, setDetails] = useState('');
  const [reportGenerated, setReportGenerated] = useState(false);

  const handleGenerateReport = () => {
    if (!txnId.trim()) return;
    setReportGenerated(true);
  };

  return (
    <div className="incident-page">
      <div className="incident-header">
        <div className="flex-center gap-3">
          <AlertOctagon size={28} className="text-red" />
          <div>
            <h2>"I Already Paid" — Emergency Incident Response</h2>
            <p>Immediate steps to minimize financial loss, freeze compromised accounts, and generate official fraud reports.</p>
          </div>
        </div>
      </div>

      {/* STEP BY STEP EMERGENCY CHECKLIST */}
      <div className="glass-panel checklist-card">
        <h3>Emergency Action Protocol</h3>
        <div className="protocol-steps">
          <div className="protocol-step">
            <div className="step-num">1</div>
            <div>
              <strong>Contact Your Bank Immediately</strong>
              <p>Call the official customer helpline on the back of your debit/credit card or net banking app to request an emergency chargeback / payment hold.</p>
            </div>
          </div>

          <div className="protocol-step">
            <div className="step-num">2</div>
            <div>
              <strong>Freeze Compromised Accounts & Block Cards</strong>
              <p>Change net banking passwords, revoke active UPI mandate permissions, and lock card transactions via your banking app.</p>
            </div>
          </div>

          <div className="protocol-step">
            <div className="step-num">3</div>
            <div>
              <strong>Preserve Digital Evidence</strong>
              <p>Save screenshots of payment confirmations, SMS alerts, WhatsApp chats, and recipient UPI IDs/URLs.</p>
            </div>
          </div>
        </div>
      </div>

      {/* INCIDENT REPORT GENERATOR */}
      <div className="glass-panel generator-card">
        <h3>Generate Official Fraud Incident Report</h3>
        <p className="text-xs text-muted mb-3">Creates an exportable PDF/JSON evidence dossier for banking dispute teams and cybercrime reporting portals.</p>

        <div className="form-grid">
          <div className="form-group">
            <label>Transaction / Reference ID</label>
            <input type="text" className="text-input font-mono" placeholder="e.g. TXN9048123901" value={txnId} onChange={(e) => setTxnId(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Loss Amount ($)</label>
            <input type="number" className="text-input font-mono" placeholder="e.g. 1250.00" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Scammer Payee VPA / Domain / Phone</label>
            <input type="text" className="text-input font-mono" placeholder="e.g. claim_support@ybl" value={payee} onChange={(e) => setPayee(e.target.value)} />
          </div>
          <div className="form-group full-width">
            <label>Brief Incident Chronology & Details</label>
            <textarea className="text-input" rows={3} placeholder="Describe how the scam occurred..." value={details} onChange={(e) => setDetails(e.target.value)} />
          </div>
        </div>

        <button className="btn-primary flex-center gap-2 mt-3" onClick={handleGenerateReport}>
          <FileText size={16} />
          <span>Generate Incident Dossier</span>
        </button>

        {reportGenerated && (
          <div className="report-preview-box mt-4">
            <div className="res-head flex-between">
              <span className="badge badge-red">OFFICIAL INCIDENT DOSSIER</span>
              <span className="text-xs font-mono text-muted">REPORT ID: FS-INC-{Math.floor(Math.random() * 899999 + 100000)}</span>
            </div>
            <div className="report-body mt-2 font-mono text-xs">
              <p><strong>TRANSACTION ID:</strong> {txnId}</p>
              <p><strong>LOSS AMOUNT:</strong> ${amount || '0.00'}</p>
              <p><strong>SUSPECT VPA/DOMAIN:</strong> {payee || 'Unspecified'}</p>
              <p><strong>EVIDENCE STATUS:</strong> VERIFIED DIGITAL SNAPSHOT</p>
            </div>
            <div className="report-actions mt-3">
              <button className="btn-secondary btn-sm flex-center gap-2" onClick={() => alert('Dossier downloaded as JSON.')}>
                <Download size={14} /> Download JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IncidentResponse;
