import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import Dashboard from './pages/Dashboard';
import AnalyzeTransaction from './pages/AnalyzeTransaction';
import BatchAnalysis from './pages/BatchAnalysis';
import CaseManagement from './pages/CaseManagement';
import ModelIntelligence from './pages/ModelIntelligence';
import SystemMonitoring from './pages/SystemMonitoring';
import Settings from './pages/Settings';
import About from './pages/About';
import LinkScanner from './pages/LinkScanner';
import QRScanner from './pages/QRScanner';
import ScamAnalyzer from './pages/ScamAnalyzer';
import Copilot from './pages/Copilot';
import IncidentResponse from './pages/IncidentResponse';
import ThreatIntelligencePage from './pages/ThreatIntelligencePage';
import AuditLogs from './pages/AuditLogs';
import EnterpriseCenter from './pages/EnterpriseCenter';
import ResearchLab from './pages/ResearchLab';
import './index.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Topbar />
          <main className="content-scroll">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/analyze" element={<AnalyzeTransaction />} />
              <Route path="/batch" element={<BatchAnalysis />} />
              <Route path="/cases" element={<CaseManagement />} />
              <Route path="/model" element={<ModelIntelligence />} />
              <Route path="/monitoring" element={<SystemMonitoring />} />
              <Route path="/scan/url" element={<LinkScanner />} />
              <Route path="/scan/qr" element={<QRScanner />} />
              <Route path="/scam-analyzer" element={<ScamAnalyzer />} />
              <Route path="/copilot" element={<Copilot />} />
              <Route path="/incident-response" element={<IncidentResponse />} />
              <Route path="/threat-intelligence" element={<ThreatIntelligencePage />} />
              <Route path="/audit-logs" element={<AuditLogs />} />
              <Route path="/enterprise" element={<EnterpriseCenter />} />
              <Route path="/research-lab" element={<ResearchLab />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/about" element={<About />} />
              <Route path="*" element={
                <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  This module is under active development.
                </div>
              } />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
