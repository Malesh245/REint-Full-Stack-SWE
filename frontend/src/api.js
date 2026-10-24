import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minute timeout for large data fetches
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Fetch actual wind generation data
 */
export const fetchActuals = async (dateFrom, dateTo) => {
  const params = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  const { data } = await api.get('/api/actuals', { params });
  return data;
};

/**
 * Fetch wind forecast data (all vintages + day-ahead)
 */
export const fetchForecasts = async (dateFrom, dateTo) => {
  const params = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  const { data } = await api.get('/api/forecasts', { params });
  return data;
};

/**
 * Fetch comparison timeseries (actuals vs day-ahead forecast)
 */
export const fetchComparison = async (dateFrom, dateTo) => {
  const params = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  const { data } = await api.get('/api/comparison', { params });
  return data;
};

/**
 * Fetch forecast accuracy metrics
 */
export const fetchAccuracy = async (dateFrom, dateTo, groupBy) => {
  const params = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  if (groupBy) params.group_by = groupBy;
  const { data } = await api.get('/api/accuracy', { params });
  return data;
};

/**
 * Fetch forecast evolution for a specific target date
 */
export const fetchForecastEvolution = async (targetDate) => {
  const { data } = await api.get('/api/forecast-evolution', {
    params: { target_date: targetDate },
  });
  return data;
};

export default api;
