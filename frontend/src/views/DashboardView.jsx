import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Area, AreaChart, ComposedChart, Bar,
} from 'recharts';
import { fetchComparison, fetchAccuracy } from '../api';
import { format, parseISO } from 'date-fns';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  
  let formattedLabel = label;
  try {
    formattedLabel = format(parseISO(label), 'dd MMM HH:mm');
  } catch (e) {
    // keep original
  }

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

const ErrorTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  
  let formattedLabel = label;
  try {
    formattedLabel = format(parseISO(label), 'dd MMM HH:mm');
  } catch (e) {}

  return (
    <div className="custom-tooltip">
      <p className="label">{formattedLabel}</p>
      {payload.map((entry, index) => (
        <p key={index} className="value" style={{ color: entry.color }}>
          {entry.name}: {entry.value != null ? `${Math.round(entry.value)} ${entry.name.includes('%') ? '%' : 'MW'}` : 'N/A'}
        </p>
      ))}
    </div>
  );
};

export default function DashboardView({ dateRange }) {
  const [comparisonData, setComparisonData] = useState(null);
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [dateRange]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [comparison, accuracy] = await Promise.all([
        fetchComparison(dateRange.from, dateRange.to),
        fetchAccuracy(dateRange.from, dateRange.to),
      ]);
      setComparisonData(comparison);
      setAccuracyData(accuracy);
    } catch (err) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Loading wind generation data from Elexon BMRS...</div>
        <div className="loading-subtext">Fetching actuals and forecasts for {dateRange.from} to {dateRange.to}</div>
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

  const metrics = accuracyData?.metrics || {};
  const timeseries = comparisonData?.timeseries || [];

  // Downsample for chart performance (show every N-th point)
  const sampleRate = Math.max(1, Math.floor(timeseries.length / 500));
  const chartData = timeseries.filter((_, i) => i % sampleRate === 0);

  // Calculate summary stats
  const actualValues = timeseries.filter(d => d.actual_mw != null).map(d => d.actual_mw);
  const avgActual = actualValues.length > 0 ? actualValues.reduce((a, b) => a + b, 0) / actualValues.length : 0;
  const maxActual = actualValues.length > 0 ? Math.max(...actualValues) : 0;
  const minActual = actualValues.length > 0 ? Math.min(...actualValues) : 0;

  return (
    <div className="fade-in">
      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card fade-in">
          <div className="kpi-label">📈 Mean Actual Generation</div>
          <div className="kpi-value neutral">
            {Math.round(avgActual).toLocaleString()}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">
            Range: {Math.round(minActual).toLocaleString()} – {Math.round(maxActual).toLocaleString()} MW
          </div>
        </div>

        <div className="kpi-card fade-in">
          <div className="kpi-label">🎯 Mean Absolute Error</div>
          <div className="kpi-value positive">
            {metrics.mae?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">
            MAPE: {metrics.mape || '—'}%
          </div>
        </div>

        <div className="kpi-card fade-in">
          <div className="kpi-label">📐 RMSE</div>
          <div className="kpi-value neutral">
            {metrics.rmse?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">
            Root Mean Square Error
          </div>
        </div>

        <div className="kpi-card fade-in">
          <div className="kpi-label">⚖️ Forecast Bias</div>
          <div className={`kpi-value ${metrics.bias > 0 ? 'negative' : 'positive'}`}>
            {metrics.bias > 0 ? '+' : ''}{metrics.bias?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">
            {metrics.bias > 0 ? 'Over-prediction' : 'Under-prediction'} tendency
          </div>
        </div>

        <div className="kpi-card fade-in">
          <div className="kpi-label">🔗 Correlation</div>
          <div className="kpi-value positive">
            {metrics.correlation || '—'}
          </div>
          <div className="kpi-sub">
            Pearson r coefficient
          </div>
        </div>

        <div className="kpi-card fade-in">
          <div className="kpi-label">📊 Data Points</div>
          <div className="kpi-value neutral">
            {metrics.n_points?.toLocaleString() || '—'}
          </div>
          <div className="kpi-sub">
            Matched forecast-actual pairs
          </div>
        </div>
      </div>

      {/* Main Comparison Chart */}
      <div className="chart-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">
              <span className="chart-title-icon cyan">⚡</span>
              Actual vs Forecast Wind Generation
            </div>
            <div className="chart-subtitle">
              Day-ahead forecast comparison · Half-hourly resolution · January 2026
            </div>
          </div>
        </div>
        <div className="chart-container large">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06d6a0" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#06d6a0" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4cc9f0" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#4cc9f0" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(val) => {
                  try { return format(parseISO(val), 'dd/MM'); } catch { return val; }
                }}
                interval="preserveStartEnd"
                minTickGap={60}
              />
              <YAxis
                tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                label={{ value: 'MW', angle: -90, position: 'insideLeft', style: { fill: '#64748b' } }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="actual_mw"
                name="Actual"
                stroke="#06d6a0"
                fill="url(#actualGrad)"
                strokeWidth={2}
                dot={false}
                connectNulls
              />
              <Area
                type="monotone"
                dataKey="forecast_mw"
                name="Forecast (Day-Ahead)"
                stroke="#4cc9f0"
                fill="url(#forecastGrad)"
                strokeWidth={2}
                dot={false}
                strokeDasharray="4 2"
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Error Chart */}
      <div className="chart-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">
              <span className="chart-title-icon orange">📉</span>
              Forecast Error Over Time
            </div>
            <div className="chart-subtitle">
              Error = Forecast − Actual (positive = over-prediction)
            </div>
          </div>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(val) => {
                  try { return format(parseISO(val), 'dd/MM'); } catch { return val; }
                }}
                interval="preserveStartEnd"
                minTickGap={60}
              />
              <YAxis
                tickFormatter={(val) => `${val > 0 ? '+' : ''}${(val / 1000).toFixed(1)}k`}
              />
              <Tooltip content={<ErrorTooltip />} />
              <Legend />
              <Bar
                dataKey="error_mw"
                name="Error (MW)"
                fill={(entry) => entry?.error_mw > 0 ? '#f97316' : '#4cc9f0'}
                opacity={0.6}
              />
              <Line
                type="monotone"
                dataKey="error_pct"
                name="Error %"
                stroke="#fbbf24"
                strokeWidth={1.5}
                dot={false}
                yAxisId="right"
                connectNulls
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={(val) => `${Math.round(val)}%`}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
