import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Activity, Layers, Zap, FileSearch,
  Box, Server, Settings, Info, Globe, QrCode, MessageSquare,
  Bot, AlertOctagon, ShieldAlert, Database, Code2, Award
} from 'lucide-react';
import './Sidebar.css';

import { soundManager } from '../../audio/soundManager';

const NavItem = ({ to, icon: Icon, label }: { to: string; icon: React.ElementType; label: string }) => (
  <NavLink
    to={to}
    end
    className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
    onClick={() => soundManager.playEvent('navigation.click')}
  >
    <Icon size={16} />
    <span>{label}</span>
  </NavLink>
);

const Sidebar = () => (
  <aside className="sidebar">
    {/* Logo */}
    <div className="sidebar-header">
      <div className="logo-container">
        <Zap className="logo-icon" size={22} />
        <div className="logo-text">
          <h1>FRAUDSENSE AI</h1>
          <span>DETECT. ANALYZE. PROTECT.</span>
        </div>
      </div>
    </div>

    {/* Navigation */}
    <nav className="sidebar-nav">
      <div className="nav-group">
        <div className="nav-title">OVERVIEW</div>
        <NavItem to="/" icon={LayoutDashboard} label="Global Dashboard" />
      </div>

      <div className="nav-group">
        <div className="nav-title">DETECTION & SCANNERS</div>
        <NavItem to="/analyze" icon={FileSearch} label="Analyze Transaction" />
        <NavItem to="/batch" icon={Layers} label="Batch Analysis" />
        <NavItem to="/scan/url" icon={Globe} label="Universal Link Scanner" />
        <NavItem to="/scan/qr" icon={QrCode} label="QR & UPI Shield" />
        <NavItem to="/scam-analyzer" icon={MessageSquare} label="SMS & Scam Analyzer" />
      </div>

      <div className="nav-group">
        <div className="nav-title">AI SECURITY & ASSISTANT</div>
        <NavItem to="/copilot" icon={Bot} label="FraudSense AI Copilot" />
        <NavItem to="/incident-response" icon={AlertOctagon} label="Emergency Response" />
      </div>

      <div className="nav-group">
        <div className="nav-title">INVESTIGATION & CASE</div>
        <NavItem to="/cases" icon={Activity} label="Case Management" />
        <NavItem to="/audit-logs" icon={Database} label="Audit Trail Logs" />
      </div>

      <div className="nav-group">
        <div className="nav-title">INTELLIGENCE & LABS</div>
        <NavItem to="/model" icon={Box} label="Model Intelligence" />
        <NavItem to="/threat-intelligence" icon={ShieldAlert} label="Threat Intelligence" />
        <NavItem to="/research-lab" icon={Award} label="IEEE Research Lab" />
      </div>

      <div className="nav-group">
        <div className="nav-title">MONITORING & ENTERPRISE</div>
        <NavItem to="/monitoring" icon={Server} label="System Monitoring" />
        <NavItem to="/enterprise" icon={Code2} label="Enterprise API & SDK" />
      </div>

      <div className="nav-group">
        <div className="nav-title">SYSTEM</div>
        <NavItem to="/settings" icon={Settings} label="Settings" />
        <NavItem to="/about" icon={Info} label="About FraudSense AI" />
      </div>
    </nav>

    {/* Footer */}
    <div className="sidebar-footer">
      <div className="version-tag">v2.4.1 &nbsp;·&nbsp; XGBoost Engine</div>
    </div>
  </aside>
);

export default Sidebar;
