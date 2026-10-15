import React, { useState, useEffect } from 'react';
import { Search, Bell, Volume2, VolumeX, Menu } from 'lucide-react';
import { soundManager } from '../../audio/soundManager';
import { useNav } from '../../context/NavContext';
import './Topbar.css';

const Topbar: React.FC = () => {
  const { isMobileOpen, toggleMobileNav } = useNav();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [soundMuted, setSoundMuted] = useState(() => {
    const s = soundManager.getSettings();
    return s.muted || !s.masterEnabled;
  });

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    const unsub = soundManager.subscribe((s) => {
      setSoundMuted(s.muted || !s.masterEnabled);
    });
    return () => {
      clearInterval(timer);
      unsub();
    };
  }, []);

  const toggleSound = () => {
    const s = soundManager.getSettings();
    if (s.muted) {
      soundManager.setMuted(false);
      soundManager.previewSound('ui');
    } else {
      soundManager.setMuted(true);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        {/* Mobile Hamburger Menu Button */}
        <button
          type="button"
          className="mobile-menu-btn"
          onClick={toggleMobileNav}
          aria-label={isMobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={isMobileOpen}
        >
          <Menu size={20} />
        </button>

        {/* Global Search */}
        <div className="search-container">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search transactions, cases... (⌘K)"
            className="global-search"
            aria-label="Global transaction and case search"
          />
          <div className="search-shortcut">⌘K</div>
        </div>
      </div>

      {/* System Status Indicators */}
      <div className="status-indicators">
        <div className="status-item" title="AI Engine is active and running XGBoost & Neural Risk Models">
          <span className="status-dot green" />
          <span className="status-label">AI ENGINE ONLINE</span>
        </div>
        <div className="status-item" title="Connected to FraudSense Real-Time Intelligence API">
          <span className="status-dot blue" />
          <span className="status-label">API CONNECTED</span>
        </div>
      </div>

      {/* Topbar Actions */}
      <div className="topbar-actions">
        <div className="sys-time data-value" title="System Time">
          {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </div>
        <button
          type="button"
          className="action-btn"
          onClick={toggleSound}
          title={soundMuted ? 'Audio is Muted (Click to Unmute)' : 'Audio is Active (Click to Mute)'}
          aria-label={soundMuted ? 'Unmute sounds' : 'Mute sounds'}
        >
          {soundMuted ? (
            <VolumeX size={18} style={{ color: '#ef4444' }} />
          ) : (
            <Volume2 size={18} style={{ color: '#06b6d4' }} />
          )}
        </button>
        <button
          type="button"
          className="action-btn"
          title="Security Notifications"
          aria-label="Security notifications (3 unread)"
        >
          <Bell size={18} />
          <span className="notification-badge">3</span>
        </button>
      </div>
    </header>
  );
};

export default Topbar;
