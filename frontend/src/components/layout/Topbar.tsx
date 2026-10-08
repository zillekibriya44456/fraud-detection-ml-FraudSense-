import { useState, useEffect } from 'react';
import { Search, Bell } from 'lucide-react';
import './Topbar.css';

const Topbar = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

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
        <button className="action-btn">
          <Bell size={18} />
          <span className="notification-badge">3</span>
        </button>
      </div>
    </header>
  );
};

export default Topbar;
