import { useState, useEffect } from 'react';
import { Search, Bell, Volume2, VolumeX } from 'lucide-react';
import { soundManager } from '../../audio/soundManager';
import './Topbar.css';

const Topbar = () => {
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
      <div className="search-container">
        <Search size={16} className="search-icon" />
        <input 
          type="text" 
          placeholder="Search transactions, cases, alerts... (Ctrl+K)" 
          className="global-search"
        />
        <div className="search-shortcut">⌘K</div>
      </div>
      
      <div className="status-indicators">
        <div className="status-item">
          <span className="status-dot green"></span>
          <span className="status-label">AI ENGINE ONLINE</span>
        </div>
        <div className="status-item">
          <span className="status-dot blue"></span>
          <span className="status-label">API CONNECTED</span>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="sys-time data-value">
          {currentTime.toLocaleTimeString()}
        </div>
        <button 
          type="button"
          className="action-btn"
          onClick={toggleSound}
          title={soundMuted ? "Audio is Muted (Click to Unmute)" : "Audio is Active (Click to Mute)"}
        >
          {soundMuted ? <VolumeX size={18} style={{ color: '#ef4444' }} /> : <Volume2 size={18} style={{ color: '#06b6d4' }} />}
        </button>
        <button className="action-btn">
          <Bell size={18} />
          <span className="notification-badge">3</span>
        </button>
      </div>
    </header>
  );
};

export default Topbar;
