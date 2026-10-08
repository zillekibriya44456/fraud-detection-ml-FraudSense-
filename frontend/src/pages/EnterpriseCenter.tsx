import { useState } from 'react';
import { Code2, Copy, CheckCircle2 } from 'lucide-react';
import './EnterpriseCenter.css';

const EnterpriseCenter = () => {
  const [copiedSdk, setCopiedSdk] = useState(false);

  const sdkCode = `from fraudsense import FraudClient

client = FraudClient(api_key="fs_live_9f83a27e4b109c4d8123ef")

# Analyze real-time payment pre-authorization
decision = client.transactions.analyze(
    amount=1250.00,
    type="TRANSFER",
    oldbalance_org=5000.00,
    newbalance_orig=3750.00,
    oldbalance_dest=0.00
)

print(f"Risk Decision: {decision.recommended_action}")
# Output: APPROVE / VERIFY / BLOCK`;

  const copyCode = () => {
    navigator.clipboard.writeText(sdkCode);
    setCopiedSdk(true);
    setTimeout(() => setCopiedSdk(false), 2000);
  };

  return (
    <div className="enterprise-page">
      <div className="ent-header">
        <h2>Enterprise Platform & API Integration</h2>
        <p>REST endpoints, Webhook dispatchers, and Python / Node.js SDK bindings for banks and fintech systems.</p>
      </div>

      <div className="ent-grid">
        {/* SDK & CODE SNIPPET */}
        <div className="glass-panel sdk-card">
          <div className="res-head flex-between">
            <div className="flex-center gap-2">
              <Code2 size={18} className="icon-blue" />
              <h3>Python Enterprise SDK Example</h3>
            </div>
            <button className="btn-secondary btn-sm flex-center gap-1" onClick={copyCode}>
              {copiedSdk ? <CheckCircle2 size={14} className="text-green" /> : <Copy size={14} />}
              <span>{copiedSdk ? 'Copied!' : 'Copy Code'}</span>
            </button>
          </div>
          <pre className="code-box font-mono mt-3">{sdkCode}</pre>
        </div>

        {/* WEBHOOK & ENDPOINTS */}
        <div className="glass-panel webhook-card">
          <h3>Production API Endpoints</h3>
          <div className="endpoint-list mt-3 font-mono text-xs">
            <div className="endpoint-row">
              <span className="method post">POST</span>
              <span className="ep-path">/api/v1/transactions/analyze</span>
              <span className="text-muted">Pre-auth risk score</span>
            </div>
            <div className="endpoint-row">
              <span className="method post">POST</span>
              <span className="ep-path">/api/v1/scans/url</span>
              <span className="text-muted">Link scanner</span>
            </div>
            <div className="endpoint-row">
              <span className="method post">POST</span>
              <span className="ep-path">/api/v1/scans/qr</span>
              <span className="text-muted">UPI QR shield</span>
            </div>
            <div className="endpoint-row">
              <span className="method get">GET</span>
              <span className="ep-path">/api/v1/threat-intelligence</span>
              <span className="text-muted">IOC threat feed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseCenter;
