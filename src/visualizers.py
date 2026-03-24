"""
Visualization functions for F1 Rhythm Analysis.

Creates publication-ready charts for:
- Pace progression over race
- Tire degradation analysis
- Driver comparisons
- Statistical distributions
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from matplotlib.patches import Rectangle
import logging

logger = logging.getLogger(__name__)

# Style configuration
sns.set_theme(style="whitegrid")
PALETTE = "husl"
FIGURE_SIZE = (12, 8)
DPI = 300


def plot_pace_progression(df: pd.DataFrame, drivers: List[str] = None, title: str = "Pace Progression") -> plt.Figure:
    """
    Plot lap time progression for drivers across race.

    Args:
        df: DataFrame with columns ['driver_id', 'lap_num', 'lap_time_seconds']
        drivers: List of driver IDs to plot; if None, plots fastest 6
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    if drivers is None:
        # Get fastest drivers by average pace
        fastest = df.groupby("driver_id")["lap_time_seconds"].mean().sort_values().head(6).index.tolist()
        drivers = fastest

    # Filter data
    plot_data = df[df["driver_id"].isin(drivers)]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    # Plot each driver
    for driver in drivers:
        driver_data = plot_data[plot_data["driver_id"] == driver].sort_values("lap_num")
        ax.plot(
            driver_data["lap_num"],
            driver_data["lap_time_seconds"],
            marker="o",
            markersize=4,
            linewidth=2,
            label=driver,
            alpha=0.8,
        )

    ax.set_xlabel("Lap Number", fontsize=12, fontweight="bold")
    ax.set_ylabel("Lap Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="best", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_lap_time_distribution(df: pd.DataFrame, drivers: List[str] = None, title: str = "Lap Time Distribution") -> plt.Figure:
    """
    Box plot comparing lap time distributions across drivers.

    Args:
        df: DataFrame with columns ['driver_id', 'lap_time_seconds']
        drivers: List of driver IDs; if None, plots all
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    if drivers is not None:
        df = df[df["driver_id"].isin(drivers)]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    # Sort by median
    driver_order = df.groupby("driver_id")["lap_time_seconds"].median().sort_values().index.tolist()

    sns.boxplot(
        data=df,
        x="driver_id",
        y="lap_time_seconds",
        order=driver_order,
        palette=PALETTE,
        ax=ax,
    )

    ax.set_xlabel("Driver", fontsize=12, fontweight="bold")
    ax.set_ylabel("Lap Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    return fig


def plot_degradation_heatmap(df: pd.DataFrame, title: str = "Tire Degradation Heatmap") -> plt.Figure:
    """
    Heatmap showing lap-to-lap time change (degradation) for all drivers.

    Rows = drivers, Columns = laps
    Darker = more degradation (positive change)

    Args:
        df: DataFrame with columns ['driver_id', 'lap_num', 'pace_delta']
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    # Pivot to matrix format
    pivot_data = df.pivot_table(
        values="pace_delta",
        index="driver_id",
        columns="lap_num",
        aggfunc="first",
    )

    fig, ax = plt.subplots(figsize=(16, 8))

    sns.heatmap(
        pivot_data,
        cmap="RdYlGn_r",  # Red = slow, Green = fast
        center=0,
        cbar_kws={"label": "Time Change (seconds)"},
        ax=ax,
        vmin=-0.5,
        vmax=0.5,
    )

    ax.set_xlabel("Lap Number", fontsize=12, fontweight="bold")
    ax.set_ylabel("Driver", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    fig.tight_layout()
    return fig


def plot_pace_delta_scatter(df: pd.DataFrame, drivers: List[str] = None, title: str = "Pace Delta Analysis") -> plt.Figure:
    """
    Scatter plot of lap number vs pace delta (change from previous lap).

    Each point = one lap. Clusters show stint patterns.

    Args:
        df: DataFrame with columns ['driver_id', 'lap_num', 'pace_delta']
        drivers: List of driver IDs; if None, plots fastest 4
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    if drivers is None:
        fastest = df.groupby("driver_id")["lap_time_seconds"].mean().sort_values().head(4).index.tolist()
        drivers = fastest

    plot_data = df[df["driver_id"].isin(drivers)]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    for driver in drivers:
        driver_data = plot_data[plot_data["driver_id"] == driver]
        ax.scatter(
            driver_data["lap_num"],
            driver_data["pace_delta"],
            label=driver,
            alpha=0.6,
            s=50,
        )

    # Reference line at 0
    ax.axhline(y=0, color="black", linestyle="--", linewidth=1, alpha=0.5)

    ax.set_xlabel("Lap Number", fontsize=12, fontweight="bold")
    ax.set_ylabel("Pace Delta (seconds)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_driver_comparison(df: pd.DataFrame, title: str = "Driver Pace Comparison") -> plt.Figure:
    """
    Bar plot comparing key metrics across drivers.

    Shows average lap time for each driver.

    Args:
        df: DataFrame with columns ['driver_id', 'lap_time_seconds']
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    # Calculate average times
    avg_times = df.groupby("driver_id")["lap_time_seconds"].mean().sort_values()

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    bars = ax.barh(avg_times.index, avg_times.values, color=sns.color_palette(PALETTE, len(avg_times)))

    ax.set_xlabel("Average Lap Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Driver", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    # Add value labels
    for i, (driver, time) in enumerate(avg_times.items()):
        ax.text(time + 0.1, i, f"{time:.2f}s", va="center", fontsize=9)

    ax.grid(True, alpha=0.3, axis="x")

    fig.tight_layout()
    return fig


def plot_pace_with_trend(df: pd.DataFrame, driver_id: str, window: int = 3, title: str = None) -> plt.Figure:
    """
    Plot driver's pace with smoothed trend line.

    Shows raw lap times + rolling average trend.

    Args:
        df: DataFrame with columns ['lap_num', 'lap_time_seconds']
        driver_id: Driver to plot
        window: Rolling average window size
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    driver_data = df[df["driver_id"] == driver_id].sort_values("lap_num")

    if len(driver_data) == 0:
        logger.warning(f"No data for driver {driver_id}")
        return None

    if title is None:
        title = f"{driver_id} - Pace with Trend"

    # Calculate smooth trend
    smooth = driver_data["lap_time_seconds"].rolling(window=window, center=True, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    # Plot raw
    ax.scatter(
        driver_data["lap_num"],
        driver_data["lap_time_seconds"],
        alpha=0.5,
        s=50,
        label="Actual",
        color="steelblue",
    )

    # Plot trend
    ax.plot(
        driver_data["lap_num"],
        smooth,
        linewidth=2.5,
        label=f"Trend (window={window})",
        color="red",
    )

    ax.set_xlabel("Lap Number", fontsize=12, fontweight="bold")
    ax.set_ylabel("Lap Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_multi_driver_comparison(df: pd.DataFrame, drivers: List[str], title: str = "Multi-Driver Comparison") -> plt.Figure:
    """
    Create 2x2 subplot comparing 4 drivers side-by-side.

    Args:
        df: DataFrame with race data
        drivers: List of up to 4 driver IDs
        title: Overall title

    Returns:
        matplotlib Figure object
    """
    if len(drivers) > 4:
        logger.warning(f"Only plotting first 4 of {len(drivers)} drivers")
        drivers = drivers[:4]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, driver in enumerate(drivers):
        ax = axes[idx]
        driver_data = df[df["driver_id"] == driver].sort_values("lap_num")

        if len(driver_data) > 0:
            ax.plot(
                driver_data["lap_num"],
                driver_data["lap_time_seconds"],
                marker="o",
                markersize=3,
                linewidth=2,
                color=sns.color_palette(PALETTE, len(drivers))[idx],
            )

            ax.set_xlabel("Lap Number", fontsize=10)
            ax.set_ylabel("Lap Time (s)", fontsize=10)
            ax.set_title(f"{driver}", fontsize=11, fontweight="bold")
            ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for idx in range(len(drivers), 4):
        axes[idx].axis("off")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.00)
    fig.tight_layout()

    return fig


def save_figure(fig: plt.Figure, filename: str, output_dir: str = "outputs", dpi: int = DPI) -> str:
    """
    Save figure to file.

    Args:
        fig: matplotlib Figure object
        filename: Output filename (without extension)
        output_dir: Directory to save to
        dpi: Resolution

    Returns:
        Path to saved file
    """
    from pathlib import Path

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{filename}.png"
    fig.savefig(output_file, dpi=dpi, bbox_inches="tight")

    logger.info(f"Saved figure to: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    # Example usage
    from src.data_fetcher import get_fetcher
    from src.etl_pipeline import Pipeline

    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if season_data:
        pipeline = Pipeline()
        race = season_data["races"][0]

        laps_data = fetcher.fetch_race_laps(2024, int(race["round"]))
        race.update(laps_data or {})

        df = pipeline.process_race(2024, int(race["round"]), race)

        if df is not None:
            print("Generating sample visualizations...")

            # Create visualizations
            fig1 = plot_pace_progression(df)
            save_figure(fig1, "01_pace_progression")

            fig2 = plot_lap_time_distribution(df)
            save_figure(fig2, "02_lap_distribution")

            fig3 = plot_driver_comparison(df)
            save_figure(fig3, "03_driver_comparison")

            print("✓ Visualizations saved to outputs/")
