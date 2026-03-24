"""
Analysis functions for F1 Rhythm Analysis.

Core analysis functions for:
- Pace progression and deltas
- Tire degradation estimation
- Driver comparisons
- Trend analysis and smoothing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)


def calculate_pace_delta(lap_times: pd.Series) -> pd.Series:
    """
    Calculate pace delta (lap-to-lap time change).

    Args:
        lap_times: Series of lap times in seconds, indexed by lap number

    Returns:
        Series of pace deltas (positive = slower, negative = faster)
    """
    return lap_times.diff()


def identify_tyre_degradation(df: pd.DataFrame, driver_id: str = None) -> Dict[str, float]:
    """
    Estimate tire degradation based on lap time progression.

    For each driver (or specific driver), calculates:
    - Linear degradation rate (seconds/lap)
    - R-squared coefficient of fit quality
    - Overall time loss from first to last lap

    Args:
        df: DataFrame with columns ['driver_id', 'lap_num', 'lap_time_seconds']
        driver_id: Optional specific driver; if None, analyzes all drivers

    Returns:
        Dict mapping driver_id -> {rate, r_squared, total_loss}
    """
    results = {}

    drivers = [driver_id] if driver_id else df["driver_id"].unique()

    for d_id in drivers:
        driver_data = df[df["driver_id"] == d_id].sort_values("lap_num")

        if len(driver_data) < 2:
            continue

        # Prepare data for regression
        X = driver_data["lap_num"].values.reshape(-1, 1)
        y = driver_data["lap_time_seconds"].values

        # Fit linear model
        model = LinearRegression()
        model.fit(X, y)

        degradation_rate = model.coef_[0]  # seconds per lap
        r_squared = model.score(X, y)
        total_loss = degradation_rate * (driver_data["lap_num"].max() - driver_data["lap_num"].min())

        results[d_id] = {
            "degradation_rate": degradation_rate,
            "r_squared": r_squared,
            "total_loss": total_loss,
            "laps_analyzed": len(driver_data),
            "avg_lap_time": y.mean(),
        }

    return results


def compare_pilots(df: pd.DataFrame, metric: str = "lap_time_seconds") -> pd.DataFrame:
    """
    Create comparison matrix of drivers by specified metric.

    Args:
        df: DataFrame with columns ['driver_id', metric]
        metric: Column to compare (default: lap_time_seconds)

    Returns:
        DataFrame with drivers as rows, sorted by average metric value
    """
    comparison = (
        df.groupby("driver_id")[metric]
        .agg(["mean", "std", "min", "max", "count"])
        .sort_values("mean")
        .round(3)
    )

    comparison.columns = ["avg_" + metric, "std_" + metric, "min_" + metric, "max_" + metric, "samples"]

    return comparison


def smooth_pace_trajectory(df: pd.DataFrame, driver_id: str = None, window: int = 3) -> pd.DataFrame:
    """
    Smooth lap time trajectory using rolling average.

    Useful for identifying overall pace trends vs race noise.

    Args:
        df: DataFrame with columns ['driver_id', 'lap_num', 'lap_time_seconds']
        driver_id: Optional specific driver; if None, applies to all
        window: Rolling window size (laps)

    Returns:
        Copy of DataFrame with additional 'pace_smooth' column
    """
    df_out = df.copy()

    drivers = [driver_id] if driver_id else df["driver_id"].unique()

    for d_id in drivers:
        mask = df_out["driver_id"] == d_id
        smooth_vals = df_out.loc[mask, "lap_time_seconds"].rolling(window=window, center=True, min_periods=1).mean()
        df_out.loc[mask, "pace_smooth"] = smooth_vals

    return df_out


def extract_stint_data(df: pd.DataFrame, stint_length: int = 15) -> Dict[str, pd.DataFrame]:
    """
    Segment races into stints (tire compound changes).

    Without explicit tire compound data, estimates stints as
    continuous performance segments.

    Args:
        df: DataFrame with columns ['driver_id', 'lap_num', 'lap_time_seconds']
        stint_length: Approximate laps per stint (default: 15 for F1)

    Returns:
        Dict mapping driver_id -> DataFrame of stint-level statistics
    """
    stint_stats = {}

    for driver_id in df["driver_id"].unique():
        driver_data = df[df["driver_id"] == driver_id].sort_values("lap_num").reset_index(drop=True)

        if len(driver_data) == 0:
            continue

        # Create stint groups
        driver_data["stint"] = (driver_data.index // stint_length).astype(int)

        # Aggregate by stint
        stint_agg = driver_data.groupby("stint").agg({
            "lap_time_seconds": ["mean", "std", "min", "max", "count"],
            "lap_num": ["min", "max"],
        }).round(2)

        stint_stats[driver_id] = stint_agg

    return stint_stats


def identify_outliers(df: pd.DataFrame, driver_id: str = None, method: str = "iqr", threshold: float = 1.5) -> pd.DataFrame:
    """
    Identify outlier lap times for each driver.

    Methods:
    - 'iqr': Interquartile range (IQR * threshold)
    - 'zscore': Standard deviations from mean

    Args:
        df: DataFrame with columns ['driver_id', 'lap_time_seconds']
        driver_id: Optional specific driver; if None, analyzes all
        method: 'iqr' or 'zscore'
        threshold: Multiplier for outlier detection (1.5 for IQR, 2-3 for zscore)

    Returns:
        DataFrame of only outlier records
    """
    outliers = []

    drivers = [driver_id] if driver_id else df["driver_id"].unique()

    for d_id in drivers:
        driver_data = df[df["driver_id"] == d_id]

        if method == "iqr":
            Q1 = driver_data["lap_time_seconds"].quantile(0.25)
            Q3 = driver_data["lap_time_seconds"].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - threshold * IQR
            upper = Q3 + threshold * IQR

            mask = (driver_data["lap_time_seconds"] < lower) | (driver_data["lap_time_seconds"] > upper)
            outliers.append(driver_data[mask])

        elif method == "zscore":
            z_scores = np.abs(stats.zscore(driver_data["lap_time_seconds"]))
            mask = z_scores > threshold
            outliers.append(driver_data[mask])

    return pd.concat(outliers, ignore_index=True) if outliers else pd.DataFrame()


def calculate_consistency(df: pd.DataFrame, driver_id: str = None) -> Dict[str, Dict[str, float]]:
    """
    Calculate consistency metrics for each driver.

    Metrics:
    - coefficient_of_variation: std/mean (lower = more consistent)
    - lap_to_lap_std: Average lap-to-lap time variation
    - best_lap_improvement: % slower than best lap

    Args:
        df: DataFrame with columns ['driver_id', 'lap_time_seconds']
        driver_id: Optional specific driver; if None, analyzes all

    Returns:
        Dict mapping driver_id -> consistency metrics
    """
    results = {}

    drivers = [driver_id] if driver_id else df["driver_id"].unique()

    for d_id in drivers:
        driver_data = df[df["driver_id"] == d_id]

        if len(driver_data) < 2:
            continue

        times = driver_data["lap_time_seconds"].values
        mean_time = times.mean()
        std_time = times.std()
        best_time = times.min()

        # Coefficient of variation
        cv = std_time / mean_time if mean_time > 0 else 0

        # Average lap-to-lap change
        deltas = np.abs(np.diff(times))
        avg_delta = deltas.mean()

        # Improvement from best lap (%)
        avg_improvement = ((mean_time - best_time) / best_time) * 100 if best_time > 0 else 0

        results[d_id] = {
            "coefficient_of_variation": round(cv, 4),
            "avg_lap_delta": round(avg_delta, 3),
            "avg_improvement_from_best": round(avg_improvement, 2),
            "best_lap": round(best_time, 2),
        }

    return results


def rate_drivers(df: pd.DataFrame, metrics: List[str] = None) -> pd.DataFrame:
    """
    Create overall driver ranking based on multiple metrics.

    Normalizes metrics and creates weighted score.

    Args:
        df: Analysis DataFrame with columns for multiple metrics
        metrics: List of metric columns to include; defaults to essential metrics

    Returns:
        DataFrame sorted by overall score (descending)
    """
    if metrics is None:
        metrics = ["pace_delta", "degradation_rate", "lap_position"]

    # Ensure metrics exist
    available_metrics = [m for m in metrics if m in df.columns]

    if not available_metrics:
        raise ValueError(f"No valid metrics found. Available: {df.columns.tolist()}")

    # Group by driver
    driver_stats = df.groupby("driver_id")[available_metrics].mean()

    # Normalize (0-1 scale)
    normalized = (driver_stats - driver_stats.min()) / (driver_stats.max() - driver_stats.min())

    # Simple average as overall score
    normalized["overall_score"] = normalized[available_metrics].mean(axis=1)

    return normalized.sort_values("overall_score", ascending=False)


# Convenience aggregation function
def get_race_summary(df: pd.DataFrame) -> Dict[str, List]:
    """
    Get quick summary statistics for a race.

    Args:
        df: Analysis DataFrame for a single race

    Returns:
        Dict with key race statistics
    """
    return {
        "total_drivers": df["driver_id"].nunique(),
        "total_laps": df["lap_num"].max(),
        "total_records": len(df),
        "avg_lap_time": round(df["lap_time_seconds"].mean(), 2),
        "fastest_lap": round(df["lap_time_seconds"].min(), 2),
        "slowest_lap": round(df["lap_time_seconds"].max(), 2),
        "avg_degradation_rate": round(df["degradation_rate"].mean(), 4),
        "drivers_by_pace": compare_pilots(df)["avg_lap_time_seconds"].to_dict(),
    }


if __name__ == "__main__":
    # Example usage
    from src.data_fetcher import get_fetcher
    from src.etl_pipeline import Pipeline

    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if season_data:
        pipeline = Pipeline()
        race = season_data["races"][0]

        # Fetch laps
        laps_data = fetcher.fetch_race_laps(2024, int(race["round"]))
        race.update(laps_data or {})

        # Process
        df = pipeline.process_race(2024, int(race["round"]), race)

        if df is not None:
            print("\n" + "=" * 60)
            print("ANALYSIS EXAMPLES".center(60))
            print("=" * 60)

            # Summary
            summary = get_race_summary(df)
            print(f"\nRace Summary:")
            for key, val in summary.items():
                if key != "drivers_by_pace":
                    print(f"  {key}: {val}")

            # Degradation
            print(f"\nTire Degradation (Fastest 5 Drivers):")
            deg = identify_tyre_degradation(df)
            sorted_deg = sorted(deg.items(), key=lambda x: x[1]["degradation_rate"])[:5]
            for driver, metrics in sorted_deg:
                print(f"  {driver}: {metrics['degradation_rate']:.4f} sec/lap")

            # Consistency
            print(f"\nConsistency (Most Consistent Drivers):")
            cons = calculate_consistency(df)
            sorted_cons = sorted(cons.items(), key=lambda x: x[1]["coefficient_of_variation"])[:5]
            for driver, metrics in sorted_cons:
                print(f"  {driver}: CV={metrics['coefficient_of_variation']:.4f}")
