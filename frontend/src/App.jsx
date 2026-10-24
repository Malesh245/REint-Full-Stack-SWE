import { useState, useEffect, useCallback } from 'react';
import './index.css';
import DashboardView from './views/DashboardView';
import AccuracyView from './views/AccuracyView';
import ForecastView from './views/ForecastView';

const VIEWS = {
  dashboard: { label: 'Dashboard', icon: '📊' },
  accuracy: { label: 'Accuracy Analysis', icon: '🎯' },
  forecast: { label: 'Forecast Explorer', icon: '🔮' },
};

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [dateRange, setDateRange] = useState({
    from: '2026-01-01',
    to: '2026-01-31',
  });
  const [tempDateRange, setTempDateRange] = useState({ ...dateRange });

  const handleApplyFilter = useCallback(() => {
    setDateRange({ ...tempDateRange });
  }, [tempDateRange]);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">⚡</div>
          <div>
            <div className="header-title">WindSight</div>
            <div className="header-subtitle">Wind Power Forecast Analytics</div>
          </div>
        </div>

        <nav className="header-nav">
          {Object.entries(VIEWS).map(([key, { label, icon }]) => (
            <button
              key={key}
              className={`nav-btn ${activeView === key ? 'active' : ''}`}
              onClick={() => setActiveView(key)}
            >
              <span>{icon}</span>
              {label}
            </button>
          ))}
        </nav>

        <div className="header-meta">
          <div className="data-badge">
            <span className="dot"></span>
            Elexon BMRS · Jan 2026
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Date Filter Bar */}
        <div className="filter-bar">
          <label>From:</label>
          <input
            type="date"
            value={tempDateRange.from}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) =>
              setTempDateRange((prev) => ({ ...prev, from: e.target.value }))
            }
          />
          <label>To:</label>
          <input
            type="date"
            value={tempDateRange.to}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) =>
              setTempDateRange((prev) => ({ ...prev, to: e.target.value }))
            }
          />
          <button className="filter-btn" onClick={handleApplyFilter}>
            Apply
          </button>
        </div>

        {/* Views */}
        {activeView === 'dashboard' && <DashboardView dateRange={dateRange} />}
        {activeView === 'accuracy' && <AccuracyView dateRange={dateRange} />}
        {activeView === 'forecast' && <ForecastView dateRange={dateRange} />}
      </main>
    </div>
  );
}

export default App;
