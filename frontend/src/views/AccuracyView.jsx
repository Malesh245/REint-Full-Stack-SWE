import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, LineChart, Line, Cell,
  ScatterChart, Scatter, ZAxis,
} from 'recharts';
import { fetchAccuracy } from '../api';
import { format, parseISO } from 'date-fns';

const MetricTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="custom-tooltip">
      <p className="label">{label}</p>
      {payload.map((entry, index) => (
        <p key={index} className="value" style={{ color: entry.color }}>
          {entry.name}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
          {entry.name.includes('MAPE') ? '%' : entry.name.includes('Correlation') ? '' : ' MW'}
        </p>
      ))}
    </div>
  );
};

export default function AccuracyView({ dateRange }) {
  const [groupBy, setGroupBy] = useState('day');
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [dateRange, groupBy]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAccuracy(dateRange.from, dateRange.to, groupBy);
      setAccuracyData(data);
    } catch (err) {
      setError(err.message || 'Failed to load accuracy data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <div className="loading-text">Computing forecast accuracy metrics...</div>
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

  const overall = accuracyData?.metrics?.overall || accuracyData?.metrics || {};
  const grouped = accuracyData?.metrics?.grouped || {};
  const distribution = accuracyData?.error_distribution || {};

  // Build grouped chart data
  const groupedChartData = Object.entries(grouped).map(([key, val]) => ({
    group: groupBy === 'hour_of_day' ? `${key}:00` : key,
    MAE: val.mae,
    RMSE: val.rmse,
    MAPE: val.mape,
    Bias: val.bias,
    Correlation: val.correlation,
    n_points: val.n_points,
  }));

  // Error distribution histogram
  const histogramData = (distribution.bins || []).map((bin) => ({
    range: `${Math.round(bin.range_start)} to ${Math.round(bin.range_end)}`,
    range_mid: (bin.range_start + bin.range_end) / 2,
    count: bin.count,
    isPositive: (bin.range_start + bin.range_end) / 2 > 0,
  }));

  const stats = distribution.stats || {};
  const percentiles = distribution.percentiles || {};

  return (
    <div className="fade-in">
      {/* Overall KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card fade-in">
          <div className="kpi-label">🎯 MAE</div>
          <div className="kpi-value positive">
            {overall.mae?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">Mean Absolute Error</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">📐 RMSE</div>
          <div className="kpi-value neutral">
            {overall.rmse?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">Root Mean Square Error</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">📊 MAPE</div>
          <div className="kpi-value neutral">
            {overall.mape || '—'}
            <span className="kpi-unit">%</span>
          </div>
          <div className="kpi-sub">Mean Absolute Percentage Error</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">⚖️ Bias</div>
          <div className={`kpi-value ${overall.bias > 0 ? 'negative' : 'positive'}`}>
            {overall.bias > 0 ? '+' : ''}{overall.bias?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">{overall.bias > 0 ? 'Over-predicting' : 'Under-predicting'}</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">📏 Max Error</div>
          <div className="kpi-value negative">
            {overall.max_error?.toLocaleString() || '—'}
            <span className="kpi-unit">MW</span>
          </div>
          <div className="kpi-sub">Worst-case single error</div>
        </div>
        <div className="kpi-card fade-in">
          <div className="kpi-label">🔗 Correlation</div>
          <div className="kpi-value positive">
            {overall.correlation || '—'}
          </div>
          <div className="kpi-sub">Pearson r</div>
        </div>
      </div>

      {/* Group By Selector */}
      <div className="filter-bar" style={{ marginBottom: '1.5rem' }}>
        <label>Group metrics by:</label>
        <select
          className="custom-select"
          value={groupBy}
          onChange={(e) => setGroupBy(e.target.value)}
        >
          <option value="day">Day</option>
          <option value="hour_of_day">Hour of Day</option>
          <option value="week">Week</option>
        </select>
      </div>

      {/* Grouped MAE / RMSE Chart */}
      <div className="chart-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">
              <span className="chart-title-icon cyan">📊</span>
              MAE & RMSE by {groupBy === 'hour_of_day' ? 'Hour of Day' : groupBy === 'day' ? 'Day' : 'Week'}
            </div>
            <div className="chart-subtitle">
              Error magnitude trends across {groupBy === 'hour_of_day' ? 'hours' : groupBy === 'day' ? 'days' : 'weeks'}
            </div>
          </div>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={groupedChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="group"
                tickFormatter={(val) => {
                  if (groupBy === 'day') {
                    try { return format(parseISO(val), 'dd/MM'); } catch { return val; }
                  }
                  return val;
                }}
                interval={groupBy === 'day' ? 2 : 0}
                angle={groupBy === 'day' ? -45 : 0}
                textAnchor={groupBy === 'day' ? 'end' : 'middle'}
                height={groupBy === 'day' ? 60 : 30}
              />
              <YAxis tickFormatter={(val) => `${val}`} label={{ value: 'MW', angle: -90, position: 'insideLeft', style: { fill: '#64748b' } }} />
              <Tooltip content={<MetricTooltip />} />
              <Legend />
              <Bar dataKey="MAE" fill="#06d6a0" radius={[4, 4, 0, 0]} opacity={0.8} />
              <Bar dataKey="RMSE" fill="#4cc9f0" radius={[4, 4, 0, 0]} opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        {/* Bias by Group */}
        <div className="chart-card">
          <div className="chart-header">
            <div>
              <div className="chart-title">
                <span className="chart-title-icon purple">⚖️</span>
                Forecast Bias
              </div>
              <div className="chart-subtitle">
                Systematic over/under prediction
              </div>
            </div>
          </div>
          <div className="chart-container small">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={groupedChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="group"
                  tickFormatter={(val) => {
                    if (groupBy === 'day') {
                      try { return format(parseISO(val), 'dd'); } catch { return val; }
                    }
                    return val;
                  }}
                  interval={groupBy === 'day' ? 3 : 0}
                />
                <YAxis />
                <Tooltip content={<MetricTooltip />} />
                <Bar dataKey="Bias" radius={[4, 4, 0, 0]}>
                  {groupedChartData.map((entry, index) => (
                    <Cell key={index} fill={entry.Bias > 0 ? '#f97316' : '#4cc9f0'} opacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Error Distribution Histogram */}
        <div className="chart-card">
          <div className="chart-header">
            <div>
              <div className="chart-title">
                <span className="chart-title-icon orange">📉</span>
                Error Distribution
              </div>
              <div className="chart-subtitle">
                Histogram of forecast errors (Forecast − Actual)
              </div>
            </div>
          </div>
          <div className="chart-container small">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histogramData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="range_mid"
                  tickFormatter={(val) => `${Math.round(val)}`}
                  label={{ value: 'Error (MW)', position: 'insideBottom', offset: -5, style: { fill: '#64748b' } }}
                />
                <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft', style: { fill: '#64748b' } }} />
                <Tooltip
                  formatter={(value, name) => [value, 'Count']}
                  labelFormatter={(val) => `Error: ~${Math.round(val)} MW`}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {histogramData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.isPositive ? '#f97316' : '#4cc9f0'}
                      opacity={0.8}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Percentiles Table */}
      {Object.keys(percentiles).length > 0 && (
        <div className="chart-card">
          <div className="chart-header">
            <div>
              <div className="chart-title">
                <span className="chart-title-icon blue">📊</span>
                Error Percentiles & Statistics
              </div>
              <div className="chart-subtitle">
                Quantile analysis of forecast errors for risk assessment
              </div>
            </div>
          </div>
          <div className="grid-2" style={{ gap: '2rem' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Percentile</th>
                  <th>Error (MW)</th>
                  <th>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>P5</td>
                  <td style={{ color: '#4cc9f0' }}>{percentiles.p5?.toLocaleString()}</td>
                  <td>5% of errors below this</td>
                </tr>
                <tr>
                  <td>P10</td>
                  <td style={{ color: '#4cc9f0' }}>{percentiles.p10?.toLocaleString()}</td>
                  <td>10% of errors below this</td>
                </tr>
                <tr>
                  <td>P25 (Q1)</td>
                  <td>{percentiles.p25?.toLocaleString()}</td>
                  <td>Lower quartile</td>
                </tr>
                <tr>
                  <td><strong>P50 (Median)</strong></td>
                  <td><strong>{percentiles.p50?.toLocaleString()}</strong></td>
                  <td>Median error</td>
                </tr>
                <tr>
                  <td>P75 (Q3)</td>
                  <td>{percentiles.p75?.toLocaleString()}</td>
                  <td>Upper quartile</td>
                </tr>
                <tr>
                  <td>P90</td>
                  <td style={{ color: '#f97316' }}>{percentiles.p90?.toLocaleString()}</td>
                  <td>90% of errors below this</td>
                </tr>
                <tr>
                  <td>P95</td>
                  <td style={{ color: '#ef4444' }}>{percentiles.p95?.toLocaleString()}</td>
                  <td>95% of errors below this</td>
                </tr>
              </tbody>
            </table>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Statistic</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Mean Error</td>
                  <td>{stats.mean?.toLocaleString()} MW</td>
                </tr>
                <tr>
                  <td>Standard Deviation</td>
                  <td>{stats.std?.toLocaleString()} MW</td>
                </tr>
                <tr>
                  <td>Skewness</td>
                  <td>{stats.skewness}</td>
                </tr>
                <tr>
                  <td>Kurtosis</td>
                  <td>{stats.kurtosis}</td>
                </tr>
                <tr>
                  <td>Mean % Error</td>
                  <td>{stats.mean_pct}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MAPE by Group */}
      <div className="chart-card">
        <div className="chart-header">
          <div>
            <div className="chart-title">
              <span className="chart-title-icon cyan">📈</span>
              MAPE by {groupBy === 'hour_of_day' ? 'Hour' : groupBy === 'day' ? 'Day' : 'Week'}
            </div>
            <div className="chart-subtitle">
              Percentage error variation — useful for identifying worst-performing periods
            </div>
          </div>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={groupedChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="group"
                tickFormatter={(val) => {
                  if (groupBy === 'day') {
                    try { return format(parseISO(val), 'dd/MM'); } catch { return val; }
                  }
                  return val;
                }}
                interval={groupBy === 'day' ? 2 : 0}
              />
              <YAxis tickFormatter={(val) => `${val}%`} />
              <Tooltip content={<MetricTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="MAPE"
                name="MAPE (%)"
                stroke="#fbbf24"
                strokeWidth={2.5}
                dot={{ fill: '#fbbf24', r: 3 }}
                activeDot={{ r: 6, stroke: '#fbbf24', strokeWidth: 2, fill: '#1a2236' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
