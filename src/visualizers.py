"""
Visualization and charting functions for F1 Rhythm Analysis.

Generates publication-quality charts including:
- Pace progression and deltas
- Tire degradation heatmaps
- Driver comparison plots
- Race strategy analysis
- Prediction visualizations
- Driver clustering analysis
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from matplotlib.patches import Rectangle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Style configuration
sns.set_theme(style="whitegrid")
sns.set_palette("husl")
PALETTE = "husl"
FIGURE_SIZE = (12, 8)
DPI = 300

# Enhanced defaults
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.size"] = 10
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["axes.titlesize"] = 13


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


def plot_degradation_comparison(
    degradation_dict: Dict[str, Dict],
    top_n: int = 10,
    title: str = "Tire Degradation Rate Comparison"
) -> plt.Figure:
    """
    Compare tire degradation rates between drivers (ADVANCED).

    Args:
        degradation_dict: Output from identify_tyre_degradation()
        top_n: Number of drivers to show
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    # Convert to DataFrame
    deg_df = pd.DataFrame(degradation_dict).T.reset_index()
    deg_df.columns = ["driver_id", "degradation_rate", "r_squared", "total_loss", "laps", "avg_lap"]

    # Sort and take top N
    deg_df = deg_df.sort_values("degradation_rate").head(top_n)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Plot 1: Degradation rate
    colors_deg = ["green" if x < 0.2 else "orange" if x < 0.3 else "red" for x in deg_df["degradation_rate"]]
    ax1.barh(deg_df["driver_id"], deg_df["degradation_rate"], color=colors_deg, alpha=0.8)
    ax1.set_xlabel("Degradation Rate (sec/lap)", fontsize=11, fontweight="bold")
    ax1.set_title("Tire Degradation Rate", fontsize=13, fontweight="bold")
    ax1.grid(True, alpha=0.3, axis="x")

    # Plot 2: Total loss
    colors_loss = ["green" if x < 5 else "orange" if x < 10 else "red" for x in deg_df["total_loss"]]
    ax2.barh(deg_df["driver_id"], deg_df["total_loss"], color=colors_loss, alpha=0.8)
    ax2.set_xlabel("Total Time Loss (seconds)", fontsize=11, fontweight="bold")
    ax2.set_title("Total Lap Time Loss", fontsize=13, fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="x")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.00)
    fig.tight_layout()
    return fig


def plot_consistency_analysis(
    consistency_dict: Dict[str, Dict],
    title: str = "Driver Consistency Analysis"
) -> plt.Figure:
    """
    Analyze and visualize driver consistency (ADVANCED).

    Args:
        consistency_dict: Output from calculate_consistency()
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    cons_df = pd.DataFrame(consistency_dict).T.reset_index()
    cons_df.columns = ["driver_id", "cv", "avg_delta", "improvement", "best_lap"]

    # Sort by CV (lower = more consistent)
    cons_df = cons_df.sort_values("cv")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Plot 1: Coefficient of Variation
    ax = axes[0, 0]
    colors_cv = ["green" if x < 0.02 else "orange" if x < 0.03 else "red" for x in cons_df["cv"]]
    ax.barh(cons_df["driver_id"], cons_df["cv"], color=colors_cv, alpha=0.8)
    ax.set_xlabel("Coefficient of Variation", fontsize=11)
    ax.set_title("Consistency (Lower = Better)", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")

    # Plot 2: Avg Lap-to-Lap Delta
    ax = axes[0, 1]
    ax.barh(cons_df["driver_id"], cons_df["avg_delta"], color="steelblue", alpha=0.8)
    ax.set_xlabel("Avg Lap-to-Lap Change (seconds)", fontsize=11)
    ax.set_title("Pace Variation Between Laps", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")

    # Plot 3: Improvement from Best Lap
    ax = axes[1, 0]
    ax.barh(cons_df["driver_id"], cons_df["improvement"], color="coral", alpha=0.8)
    ax.set_xlabel("Improvement from Best Lap (%)", fontsize=11)
    ax.set_title("Average vs Best Lap", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")

    # Plot 4: Best Lap Times
    ax = axes[1, 1]
    ax.barh(cons_df["driver_id"], cons_df["best_lap"], color="mediumseagreen", alpha=0.8)
    ax.set_xlabel("Best Lap Time (seconds)", fontsize=11)
    ax.set_title("Best Lap Achieved", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.00)
    fig.tight_layout()
    return fig


def plot_prediction_vs_actual(
    actual: np.ndarray,
    predicted: np.ndarray,
    driver_id: str = "Driver",
    title: str = None
) -> plt.Figure:
    """
    Compare predicted vs actual lap times (ADVANCED).

    Args:
        actual: Array of actual lap times
        predicted: Array of predicted lap times
        driver_id: Driver identifier for plots
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    if title is None:
        title = f"{driver_id} - Prediction Performance"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    laps = np.arange(len(actual))

    # Plot 1: Actual vs Predicted
    ax1.plot(laps, actual, "o-", label="Actual", linewidth=2, markersize=5, alpha=0.8)
    ax1.plot(laps, predicted, "s--", label="Predicted", linewidth=2, markersize=4, alpha=0.8)
    ax1.fill_between(laps, actual, predicted, alpha=0.2, color="red")
    ax1.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Lap Time (seconds)", fontsize=11, fontweight="bold")
    ax1.set_title("Actual vs Predicted Lap Times", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Prediction Error
    errors = actual - predicted
    colors_err = ["green" if e > 0 else "red" for e in errors]
    ax2.bar(laps, errors, color=colors_err, alpha=0.7)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=1)
    ax2.set_xlabel("Lap Number", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Error (seconds)", fontsize=11, fontweight="bold")
    ax2.set_title("Prediction Errors (Green=Underpredicted)", fontsize=13, fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="y")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.00)
    fig.tight_layout()
    return fig


def plot_cluster_analysis(
    df: pd.DataFrame,
    clusters: pd.DataFrame,
    title: str = "Driver Clustering Analysis"
) -> plt.Figure:
    """
    Visualize driver clusters by performance (ADVANCED).

    Args:
        df: Race DataFrame
        clusters: Output from DriverClusterer.fit_predict()
        title: Chart title

    Returns:
        matplotlib Figure object
    """
    # Merge cluster assignments
    df_clustered = df.merge(clusters, on="driver_id", how="left")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Get unique clusters
    unique_clusters = sorted(df_clustered["cluster"].unique())
    colors = sns.color_palette("husl", len(unique_clusters))

    # Plot 1: Clusters by pace
    ax = axes[0, 0]
    for cluster in unique_clusters:
        cluster_data = df_clustered[df_clustered["cluster"] == cluster]
        avg_pace = cluster_data.groupby("driver_id")["lap_time_seconds"].mean()
        ax.scatter(
            range(len(avg_pace)),
            avg_pace.values,
            label=f"Cluster {cluster}",
            s=150,
            alpha=0.7,
            color=colors[cluster % len(colors)]
        )
    ax.set_ylabel("Avg Lap Time (seconds)", fontsize=11, fontweight="bold")
    ax.set_title("Drivers by Cluster - Pace", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Plot 2: Cluster sizes
    ax = axes[0, 1]
    cluster_sizes = clusters.groupby("cluster").size()
    ax.bar(cluster_sizes.index, cluster_sizes.values, color=colors, alpha=0.8)
    ax.set_xlabel("Cluster", fontsize=11, fontweight="bold")
    ax.set_ylabel("Number of Drivers", fontsize=11, fontweight="bold")
    ax.set_title("Drivers per Cluster", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    # Plot 3: Consistency by cluster
    ax = axes[1, 0]
    consistency_by_cluster = []
    for cluster in unique_clusters:
        cluster_data = df_clustered[df_clustered["cluster"] == cluster]
        consistency = (
            cluster_data.groupby("driver_id")["lap_time_seconds"].std() /
            cluster_data.groupby("driver_id")["lap_time_seconds"].mean()
        ).mean()
        consistency_by_cluster.append(consistency)

    ax.bar(unique_clusters, consistency_by_cluster, color=colors, alpha=0.8)
    ax.set_xlabel("Cluster", fontsize=11, fontweight="bold")
    ax.set_ylabel("Avg Consistency (CV)", fontsize=11, fontweight="bold")
    ax.set_title("Consistency by Cluster", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    # Plot 4: Degradation by cluster
    ax = axes[1, 1]
    degradation_by_cluster = []
    for cluster in unique_clusters:
        cluster_data = df_clustered[df_clustered["cluster"] == cluster]
        if "degradation_rate" in cluster_data.columns:
            degradation = cluster_data["degradation_rate"].mean()
        else:
            degradation = 0
        degradation_by_cluster.append(degradation)

    ax.bar(unique_clusters, degradation_by_cluster, color=colors, alpha=0.8)
    ax.set_xlabel("Cluster", fontsize=11, fontweight="bold")
    ax.set_ylabel("Avg Degradation (sec/lap)", fontsize=11, fontweight="bold")
    ax.set_title("Tire Degradation by Cluster", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

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
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{filename}.png"
    fig.savefig(output_file, dpi=dpi, bbox_inches="tight")

    logger.info(f"Saved figure to: {output_file}")
    return str(output_file)


def generate_all_visualizations(
    df: pd.DataFrame,
    degradation_dict: Dict = None,
    consistency_dict: Dict = None,
    comparison_df: pd.DataFrame = None,
    clusters: pd.DataFrame = None,
    output_dir: str = "outputs"
) -> Dict[str, str]:
    """
    Generate all available visualizations (CONVENIENCE FUNCTION).

    Args:
        df: Race DataFrame
        degradation_dict: Output from identify_tyre_degradation()
        consistency_dict: Output from calculate_consistency()
        comparison_df: Output from compare_pilots()
        clusters: Output from DriverClusterer.fit_predict()
        output_dir: Directory to save figures

    Returns:
        Dict mapping viz name to filename
    """
    generated = {}

    try:
        logger.info("Generating pace progression...")
        fig = plot_pace_progression(df)
        save_figure(fig, "01_pace_progression", output_dir)
        generated["pace_progression"] = "01_pace_progression.png"
        plt.close(fig)
    except Exception as e:
        logger.error(f"Failed pace progression: {e}")

    try:
        logger.info("Generating pace delta heatmap...")
        fig = plot_degradation_heatmap(df)
        save_figure(fig, "02_pace_delta_heatmap", output_dir)
        generated["pace_delta"] = "02_pace_delta_heatmap.png"
        plt.close(fig)
    except Exception as e:
        logger.error(f"Failed pace delta: {e}")

    try:
        logger.info("Generating lap distribution...")
        fig = plot_lap_time_distribution(df)
        save_figure(fig, "03_lap_distribution", output_dir)
        generated["distribution"] = "03_lap_distribution.png"
        plt.close(fig)
    except Exception as e:
        logger.error(f"Failed distribution: {e}")

    if degradation_dict:
        try:
            logger.info("Generating degradation comparison...")
            fig = plot_degradation_comparison(degradation_dict)
            save_figure(fig, "04_degradation_comparison", output_dir)
            generated["degradation"] = "04_degradation_comparison.png"
            plt.close(fig)
        except Exception as e:
            logger.error(f"Failed degradation: {e}")

    if comparison_df is not None:
        try:
            logger.info("Generating driver comparison...")
            fig = plot_driver_comparison(df)
            save_figure(fig, "05_driver_comparison", output_dir)
            generated["comparison"] = "05_driver_comparison.png"
            plt.close(fig)
        except Exception as e:
            logger.error(f"Failed comparison: {e}")

    if consistency_dict:
        try:
            logger.info("Generating consistency analysis...")
            fig = plot_consistency_analysis(consistency_dict)
            save_figure(fig, "06_consistency_analysis", output_dir)
            generated["consistency"] = "06_consistency_analysis.png"
            plt.close(fig)
        except Exception as e:
            logger.error(f"Failed consistency: {e}")

    try:
        logger.info("Generating pace delta scatter...")
        fig = plot_pace_delta_scatter(df)
        save_figure(fig, "07_pace_delta_scatter", output_dir)
        generated["scatter"] = "07_pace_delta_scatter.png"
        plt.close(fig)
    except Exception as e:
        logger.error(f"Failed scatter: {e}")

    if clusters is not None:
        try:
            logger.info("Generating cluster analysis...")
            fig = plot_cluster_analysis(df, clusters)
            save_figure(fig, "08_cluster_analysis", output_dir)
            generated["clusters"] = "08_cluster_analysis.png"
            plt.close(fig)
        except Exception as e:
            logger.error(f"Failed clusters: {e}")

    logger.info(f"✓ Generated {len(generated)} visualizations")
    return generated


if __name__ == "__main__":
    # Example usage
    from src.data_fetcher import get_fetcher
    from src.etl_pipeline import Pipeline
    from src.analysis import (
        identify_tyre_degradation,
        calculate_consistency,
        compare_pilots,
    )

    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if season_data:
        pipeline = Pipeline()
        race = season_data["races"][0]

        laps_data = fetcher.fetch_race_laps(2024, int(race["round"]))
        race.update(laps_data or {})

        df = pipeline.process_race(2024, int(race["round"]), race)

        if df is not None:
            print("\n" + "=" * 60)
            print("GENERATING VISUALIZATIONS".center(60))
            print("=" * 60)

            # Calculate analysis data
            degradation = identify_tyre_degradation(df)
            consistency = calculate_consistency(df)
            comparison = compare_pilots(df)

            # Generate all visualizations
            generated = generate_all_visualizations(
                df,
                degradation_dict=degradation,
                consistency_dict=consistency,
                comparison_df=comparison
            )

            print(f"\n✓ Generated {len(generated)} visualizations:")
            for name, filename in generated.items():
                print(f"  • {name:20s} → {filename}")
            print("\nAll saved to outputs/")
