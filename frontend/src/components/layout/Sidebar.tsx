import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Activity, Layers, Zap, FileSearch,
  Box, Server, Settings, Info, Globe, QrCode, MessageSquare,
  Bot, AlertOctagon, ShieldAlert, Database, Code2, Award, X
} from 'lucide-react';
import './Sidebar.css';
import { soundManager } from '../../audio/soundManager';
import { useNav } from '../../context/NavContext';

interface NavItemProps {
  to: string;
  icon: React.ElementType;
  label: string;
  onClick?: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon: Icon, label, onClick }) => (
  <NavLink
    to={to}
    end
    className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
    onClick={() => {
      soundManager.playEvent('navigation.click');
      if (onClick) onClick();
    }}
  >
    <Icon size={16} className="nav-item-icon" />
    <span>{label}</span>
  </NavLink>
);

const Sidebar: React.FC = () => {
  const { isMobileOpen, closeMobileNav } = useNav();

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      <div
        className={`sidebar-backdrop ${isMobileOpen ? 'visible' : ''}`}
        onClick={closeMobileNav}
        aria-hidden="true"
      />

      <aside className={`sidebar ${isMobileOpen ? 'mobile-open' : ''}`} aria-label="Main Navigation">
        {/* Logo & Header */}
        <div className="sidebar-header">
          <div className="logo-container">
            <Zap className="logo-icon" size={22} />
            <div className="logo-text">
              <h1>FRAUDSENSE AI</h1>
              <span>DETECT. ANALYZE. PROTECT.</span>
            </div>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={closeMobileNav}
            aria-label="Close navigation menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Independently Scrollable Navigation List */}
        <nav className="sidebar-nav" id="sidebar-navigation">
          <div className="nav-group">
            <div className="nav-title">OVERVIEW</div>
            <NavItem to="/" icon={LayoutDashboard} label="Global Dashboard" onClick={closeMobileNav} />
          </div>

          <div className="nav-group">
            <div className="nav-title">DETECTION & SCANNERS</div>
            <NavItem to="/analyze" icon={FileSearch} label="Analyze Transaction" onClick={closeMobileNav} />
            <NavItem to="/batch" icon={Layers} label="Batch Analysis" onClick={closeMobileNav} />
            <NavItem to="/scan/url" icon={Globe} label="Universal Link Scanner" onClick={closeMobileNav} />
            <NavItem to="/scan/qr" icon={QrCode} label="QR & UPI Shield" onClick={closeMobileNav} />
            <NavItem to="/scam-analyzer" icon={MessageSquare} label="SMS & Scam Analyzer" onClick={closeMobileNav} />
          </div>

          <div className="nav-group">
            <div className="nav-title">AI SECURITY & ASSISTANT</div>
            <NavItem to="/copilot" icon={Bot} label="FraudSense AI Copilot" onClick={closeMobileNav} />
            <NavItem to="/incident-response" icon={AlertOctagon} label="Emergency Response" onClick={closeMobileNav} />
          </div>

          <div className="nav-group">
            <div className="nav-title">INVESTIGATION & CASE</div>
            <NavItem to="/cases" icon={Activity} label="Case Management" onClick={closeMobileNav} />
            <NavItem to="/audit-logs" icon={Database} label="Audit Trail Logs" onClick={closeMobileNav} />
          </div>

          <div className="nav-group">
            <div className="nav-title">INTELLIGENCE & LABS</div>
            <NavItem to="/model" icon={Box} label="Model Intelligence" onClick={closeMobileNav} />
            <NavItem to="/threat-intelligence" icon={ShieldAlert} label="Threat Intelligence" onClick={closeMobileNav} />
            <NavItem to="/research-lab" icon={Award} label="IEEE Research Lab" onClick={closeMobileNav} />
          </div>

          <div className="nav-group">
            <div className="nav-title">MONITORING & ENTERPRISE</div>
            <NavItem to="/monitoring" icon={Server} label="System Monitoring" onClick={closeMobileNav} />
            <NavItem to="/enterprise" icon={Code2} label="Enterprise API & SDK" onClick={closeMobileNav} />
          </div>

          <div className="nav-group">
            <div className="nav-title">SYSTEM</div>
            <NavItem to="/settings" icon={Settings} label="Settings" onClick={closeMobileNav} />
            <NavItem to="/about" icon={Info} label="About FraudSense AI" onClick={closeMobileNav} />
          </div>
        </nav>

        {/* Footer (Fixed at bottom, never covering nav items) */}
        <div className="sidebar-footer">
          <div className="version-tag">v2.4.1 &nbsp;·&nbsp; XGBoost Engine</div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
