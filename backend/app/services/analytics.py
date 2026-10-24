"""
WindSight - Data processing and forecast accuracy analytics
Computes error metrics (MAE, RMSE, MAPE, bias) and aligns forecast vs actual data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def process_actuals(raw_data: list[dict]) -> pd.DataFrame:
    """
    Process raw FUELHH wind actuals into a clean DataFrame.
    
    The actuals have 30-min resolution. We aggregate to hourly to match
    the forecast resolution (WINDFOR is hourly).
    
    Returns:
        DataFrame with columns: [timestamp, actual_mw]
    """
    if not raw_data:
        return pd.DataFrame(columns=["timestamp", "actual_mw"])
    
    df = pd.DataFrame(raw_data)
    df["timestamp"] = pd.to_datetime(df["startTime"], utc=True)
    df = df.rename(columns={"generation": "actual_mw"})
    df = df[["timestamp", "actual_mw"]].sort_values("timestamp")
    
    # Aggregate 30-min to hourly (mean of the two half-hours within each hour)
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = df.groupby("hour").agg(actual_mw=("actual_mw", "mean")).reset_index()
    hourly = hourly.rename(columns={"hour": "timestamp"})
    
    return hourly


def process_forecasts(raw_data: list[dict]) -> pd.DataFrame:
    """
    Process raw WINDFOR forecasts into a clean DataFrame.
    
    Multiple forecast vintages exist (published at different times) for the
    same target hour. We keep all vintages for analysis, and also extract
    the "day-ahead" forecast — the most recent forecast published before
    the gate closure (~11:00 UK time, day before delivery).
    
    Returns:
        DataFrame with columns: [timestamp, forecast_mw, publish_time]
    """
    if not raw_data:
        return pd.DataFrame(columns=["timestamp", "forecast_mw", "publish_time"])
    
    df = pd.DataFrame(raw_data)
    df["timestamp"] = pd.to_datetime(df["startTime"], utc=True)
    df["publish_time"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df.rename(columns={"generation": "forecast_mw"})
    df = df[["timestamp", "forecast_mw", "publish_time"]].sort_values(
        ["timestamp", "publish_time"]
    )
    
    return df


def get_day_ahead_forecasts(forecasts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the day-ahead forecast for each target hour.
    
    The UK day-ahead market gate closure is typically around 09:00-11:00 UTC
    the day before delivery. We select the latest forecast published before
    09:00 UTC on the day before the target delivery day.
    
    For each target hour, we find the forecast published closest to (but before)
    the gate closure time.
    
    Returns:
        DataFrame with columns: [timestamp, forecast_mw, publish_time, lead_hours]
    """
    if forecasts_df.empty:
        return pd.DataFrame(
            columns=["timestamp", "forecast_mw", "publish_time", "lead_hours"]
        )
    
    df = forecasts_df.copy()
    
    # The delivery date for a target hour
    df["delivery_date"] = df["timestamp"].dt.date
    
    # Gate closure: 09:00 UTC on the day before delivery
    df["gate_closure"] = pd.to_datetime(
        df["delivery_date"] - pd.Timedelta(days=0)  # same day early morning latest
    ).dt.tz_localize("UTC") + pd.Timedelta(hours=9)
    
    # For day-ahead: use forecasts published before gate closure on D-1
    # i.e., published before 09:00 UTC on the day before delivery
    df["day_before_gate"] = df["timestamp"].dt.normalize() - pd.Timedelta(days=1) + pd.Timedelta(hours=9)
    
    # Filter: publishTime must be before gate closure on D-1
    day_ahead_mask = df["publish_time"] <= df["day_before_gate"]
    
    if day_ahead_mask.sum() == 0:
        # Fallback: use the earliest available forecast for each target hour
        result = df.sort_values("publish_time").groupby("timestamp").first().reset_index()
    else:
        # Take the latest published forecast that's still before gate closure
        filtered = df[day_ahead_mask].copy()
        result = (
            filtered.sort_values("publish_time", ascending=False)
            .groupby("timestamp")
            .first()
            .reset_index()
        )
    
    # Calculate lead time in hours
    result["lead_hours"] = (
        (result["timestamp"] - result["publish_time"]).dt.total_seconds() / 3600
    )
    
    return result[["timestamp", "forecast_mw", "publish_time", "lead_hours"]]


def compute_accuracy_metrics(
    actuals_df: pd.DataFrame, 
    forecasts_df: pd.DataFrame,
    group_by: Optional[str] = None,
) -> dict:
    """
    Compute forecast accuracy metrics by merging actuals and forecasts.
    
    Metrics:
        - MAE: Mean Absolute Error (MW)
        - RMSE: Root Mean Square Error (MW)
        - MAPE: Mean Absolute Percentage Error (%)
        - Bias: Mean Error / systematic over/under-prediction (MW)
        - Max Error: Maximum absolute error (MW)
        - Correlation: Pearson correlation coefficient
    
    Args:
        actuals_df: DataFrame with [timestamp, actual_mw]
        forecasts_df: DataFrame with [timestamp, forecast_mw]
        group_by: Optional grouping ('hour_of_day', 'day', 'week')
    
    Returns:
        Dictionary with computed metrics
    """
    # Merge on timestamp (hourly)
    merged = pd.merge(
        actuals_df[["timestamp", "actual_mw"]],
        forecasts_df[["timestamp", "forecast_mw"]],
        on="timestamp",
        how="inner",
    )
    
    if merged.empty:
        return {
            "mae": 0, "rmse": 0, "mape": 0, "bias": 0,
            "max_error": 0, "correlation": 0, "n_points": 0,
        }
    
    merged["error"] = merged["forecast_mw"] - merged["actual_mw"]
    merged["abs_error"] = merged["error"].abs()
    merged["pct_error"] = (
        merged["abs_error"] / merged["actual_mw"].replace(0, np.nan) * 100
    )
    
    def calc_metrics(df_group):
        return {
            "mae": round(float(df_group["abs_error"].mean()), 2),
            "rmse": round(float(np.sqrt((df_group["error"] ** 2).mean())), 2),
            "mape": round(float(df_group["pct_error"].mean()), 2),
            "bias": round(float(df_group["error"].mean()), 2),
            "max_error": round(float(df_group["abs_error"].max()), 2),
            "correlation": round(
                float(df_group["actual_mw"].corr(df_group["forecast_mw"])), 4
            ),
            "n_points": len(df_group),
        }
    
    if group_by is None:
        return calc_metrics(merged)
    
    # Grouped metrics
    if group_by == "hour_of_day":
        merged["group"] = merged["timestamp"].dt.hour
    elif group_by == "day":
        merged["group"] = merged["timestamp"].dt.strftime("%Y-%m-%d")
    elif group_by == "week":
        merged["group"] = merged["timestamp"].dt.isocalendar().week.astype(int)
    else:
        return calc_metrics(merged)
    
    grouped_metrics = {}
    for group_val, group_df in merged.groupby("group"):
        grouped_metrics[str(group_val)] = calc_metrics(group_df)
    
    return {
        "overall": calc_metrics(merged),
        "grouped": grouped_metrics,
    }


def build_comparison_timeseries(
    actuals_df: pd.DataFrame,
    forecasts_df: pd.DataFrame,
) -> list[dict]:
    """
    Build a merged timeseries of actuals vs forecasts for charting.
    
    Returns:
        List of dicts with {timestamp, actual_mw, forecast_mw, error_mw, error_pct}
    """
    merged = pd.merge(
        actuals_df[["timestamp", "actual_mw"]],
        forecasts_df[["timestamp", "forecast_mw"]],
        on="timestamp",
        how="outer",
    ).sort_values("timestamp")
    
    merged["error_mw"] = merged["forecast_mw"] - merged["actual_mw"]
    merged["error_pct"] = (
        merged["error_mw"].abs() / merged["actual_mw"].replace(0, np.nan) * 100
    )
    
    # Convert timestamps to ISO strings for JSON serialization
    merged["timestamp"] = merged["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Replace NaN with None for JSON
    merged = merged.where(pd.notna(merged), None)
    
    return merged.to_dict(orient="records")


def build_error_distribution(
    actuals_df: pd.DataFrame,
    forecasts_df: pd.DataFrame,
) -> dict:
    """
    Build error distribution data for histogram visualization.
    
    Returns:
        Dictionary with histogram bins, percentiles, and statistics
    """
    merged = pd.merge(
        actuals_df[["timestamp", "actual_mw"]],
        forecasts_df[["timestamp", "forecast_mw"]],
        on="timestamp",
        how="inner",
    )
    
    if merged.empty:
        return {"bins": [], "percentiles": {}, "stats": {}}
    
    errors = merged["forecast_mw"] - merged["actual_mw"]
    pct_errors = errors / merged["actual_mw"].replace(0, np.nan) * 100
    
    # Histogram bins
    hist_counts, bin_edges = np.histogram(errors, bins=30)
    bins = [
        {
            "range_start": round(float(bin_edges[i]), 1),
            "range_end": round(float(bin_edges[i + 1]), 1),
            "count": int(hist_counts[i]),
        }
        for i in range(len(hist_counts))
    ]
    
    # Percentiles
    percentiles = {
        "p5": round(float(errors.quantile(0.05)), 2),
        "p10": round(float(errors.quantile(0.10)), 2),
        "p25": round(float(errors.quantile(0.25)), 2),
        "p50": round(float(errors.quantile(0.50)), 2),
        "p75": round(float(errors.quantile(0.75)), 2),
        "p90": round(float(errors.quantile(0.90)), 2),
        "p95": round(float(errors.quantile(0.95)), 2),
    }
    
    # Basic stats
    stats = {
        "mean": round(float(errors.mean()), 2),
        "std": round(float(errors.std()), 2),
        "skewness": round(float(errors.skew()), 4),
        "kurtosis": round(float(errors.kurtosis()), 4),
        "mean_pct": round(float(pct_errors.mean()), 2),
    }
    
    return {"bins": bins, "percentiles": percentiles, "stats": stats}
