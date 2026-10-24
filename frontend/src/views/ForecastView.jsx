import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, AreaChart, Area,
} from 'recharts';
import { fetchForecastEvolution } from '../api';
import { format, parseISO } from 'date-fns';

// Distinct colors for forecast vintages
const VINTAGE_COLORS = [
  '#ff6b6b', '#ffa94d', '#ffd43b', '#a9e34b',
  '#51cf66', '#22b8cf', '#4cc9f0', '#748ffc',
  '#9775fa', '#f06595',
];

const ForecastTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  
  let formattedLabel = label;
  try {
    formattedLabel = format(parseISO(label), 'HH:mm');
  } catch (e) {}

  return (
    <div className="custom-tooltip">
      <p className="label">{formattedLabel}</p>
      {payload.map((entry, index) => (
        <p key={index} className="value" style={{ color: entry.color }}>
          {entry.name}: {entry.value != null ? `${Math.round(entry.value).toLocaleString()} MW` : 'N/A'}
        </p>
      ))}
    </div>
  );
};

export default function ForecastView({ dateRange }) {
  const [targetDate, setTargetDate] = useState('2026-01-15');
  const [evolutionData, setEvolutionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [targetDate]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchForecastEvolution(targetDate);
      setEvolutionData(data);
    } catch (err) {
      setError(err.message || 'Failed to load forecast evolution');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Loading forecast evolution for {targetDate}...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">⚠️</div>
        <div className="error-message">{error}</div>
        <button className="error-retry" onClick={loadData}>Retry</button>
      </div>
    );
  }

  const evolution = evolutionData?.evolution || [];
  const actuals = evolutionData?.actuals || [];

  // Build merged chart data: each target hour is a row, each vintage is a column
  const hours = new Set();
  evolution.forEach((vintage) => {
    vintage.forecasts.forEach((f) => hours.add(f.timestamp));
  });
  actuals.forEach((a) => hours.add(a.timestamp));

  const sortedHours = [...hours].sort();
  
  const chartData = sortedHours.map((hour) => {
    const row = { timestamp: hour };
    
    // Add actual
    const actual = actuals.find((a) => a.timestamp === hour);
    if (actual) row.actual = actual.actual_mw;
    
    // Add each vintage
    evolution.forEach((vintage, i) => {
      const forecast = vintage.forecasts.find((f) => f.timestamp === hour);
      if (forecast) {
        const publishLabel = format(parseISO(vintage.publish_time), 'dd/MM HH:mm');
        row[`v_${i}`] = forecast.forecast_mw;
        row[`label_${i}`] = publishLabel;
      }
    });
    
    return row;
  });

  // Generate available dates (Jan 2026 only)
  const availableDates = [];
  for (let d = 1; d <= 31; d++) {
    const dateStr = `2026-01-${String(d).padStart(2, '0')}`;
    availableDates.push(dateStr);
  }

  return (
    <div className="fade-in">
      {/* Date Selector */}
      <div className="filter-bar" style={{ marginBottom: '1.5rem' }}>
        <label>Target Delivery Date:</label>
        <input
          type="date"
          value={targetDate}
          min="2026-01-01"
          max="2026-01-31"
          onChange={(e) => setTargetDate(e.target.value)}
        />
        <button className="filter-btn" onClick={loadData}>
          Load Forecasts
        </button>
        <div style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {evolution.length} forecast vintages · {actuals.length} actual data points
        </div>
      </div>

      {/* Info KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card fade-in">
          <div className="kpi-label">📅 Target Date</div>
          <div className="kpi-value neutral" style={{ fontSize: '1.4rem' }}>
            {format(parseISO(targetDate), 'dd MMM yyyy')}
          </div>
          <div className="kpi-sub">Delivery day being analyzed</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">🔄 Forecast Vintages</div>
          <div className="kpi-value positive">
            {evolution.length}
          </div>
          <div className="kpi-sub">Published forecast updates</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">📊 Actual Data Points</div>
          <div className="kpi-value neutral">
            {actuals.length}
          </div>
          <div className="kpi-sub">Hourly generation readings</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">⏱️ Earliest Forecast</div>
          <div className="kpi-value neutral" style={{ fontSize: '1.1rem' }}>
            {evolution.length > 0 ? format(parseISO(evolution[0].publish_time), 'dd/MM HH:mm') : '—'}
          </div>
          <div className="kpi-sub">First available forecast vintage</div>
        </div>
      </div>

      {/* Forecast Evolution Chart */}
      <div className="chart-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">
              <span className="chart-title-icon cyan">🔮</span>
              Forecast Evolution for {format(parseISO(targetDate), 'dd MMMM yyyy')}
            </div>
            <div className="chart-subtitle">
              Each line represents a forecast vintage (published at different times).
              The green area shows actual generation. Observe how forecasts converge toward actuals closer to delivery.
            </div>
          </div>
        </div>
        <div className="chart-container large">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="actualEvolutionGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06d6a0" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#06d6a0" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(val) => {
                  try { return format(parseISO(val), 'HH:mm'); } catch { return val; }
                }}
                interval="preserveStartEnd"
                minTickGap={50}
              />
              <YAxis
                tickFormatter={(val) => `${(val / 1000).toFixed(1)}k`}
                label={{ value: 'MW', angle: -90, position: 'insideLeft', style: { fill: '#64748b' } }}
              />
              <Tooltip content={<ForecastTooltip />} />
              <Legend />
              
              {/* Actual as filled area */}
              <Area
                type="monotone"
                dataKey="actual"
                name="Actual Generation"
                stroke="#06d6a0"
                fill="url(#actualEvolutionGrad)"
                strokeWidth={3}
                dot={false}
                connectNulls
              />
              
              {/* Forecast vintages as lines */}
              {evolution.map((vintage, i) => {
                const publishLabel = format(parseISO(vintage.publish_time), 'dd/MM HH:mm');
                return (
                  <Line
                    key={i}
                    type="monotone"
                    dataKey={`v_${i}`}
                    name={`Forecast ${publishLabel}`}
                    stroke={VINTAGE_COLORS[i % VINTAGE_COLORS.length]}
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray={i < evolution.length - 1 ? '4 3' : '0'}
                    opacity={0.3 + (i / evolution.length) * 0.7}
                    connectNulls
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Vintage Details Table */}
      <div className="chart-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">
              <span className="chart-title-icon blue">📋</span>
              Forecast Vintage Details
            </div>
            <div className="chart-subtitle">
              Publication times and summary for each forecast update
            </div>
          </div>
        </div>
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Published At (UTC)</th>
                <th>Lead Time</th>
                <th>Data Points</th>
                <th>Mean Forecast (MW)</th>
              </tr>
            </thead>
            <tbody>
              {evolution.map((vintage, i) => {
                const publishTime = parseISO(vintage.publish_time);
                const targetStart = parseISO(`${targetDate}T12:00:00Z`);
                const leadHours = (targetStart - publishTime) / (1000 * 60 * 60);
                const meanForecast = vintage.forecasts.length > 0
                  ? Math.round(vintage.forecasts.reduce((sum, f) => sum + f.forecast_mw, 0) / vintage.forecasts.length)
                  : 0;
                
                return (
                  <tr key={i}>
                    <td>
                      <span style={{
                        display: 'inline-block',
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background: VINTAGE_COLORS[i % VINTAGE_COLORS.length],
                        marginRight: 8,
                      }}></span>
                      {i + 1}
                    </td>
                    <td>{format(publishTime, 'dd MMM yyyy HH:mm')}</td>
                    <td>{leadHours > 0 ? `${Math.round(leadHours)}h ahead` : 'After delivery'}</td>
                    <td>{vintage.forecasts.length}</td>
                    <td>{meanForecast.toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
