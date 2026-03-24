#!/usr/bin/env python3
"""
Generate visualization examples from mock data.

Creates a suite of charts demonstrating the analysis capabilities.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_fetcher
from src.etl_pipeline import Pipeline
from src.visualizers import (
    plot_pace_progression,
    plot_lap_time_distribution,
    plot_driver_comparison,
    plot_degradation_heatmap,
    plot_pace_delta_scatter,
    plot_pace_with_trend,
    plot_multi_driver_comparison,
    save_figure,
)
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    """Generate visualizations."""
    print("\n" + "=" * 70)
    print("F1 RHYTHM ANALYSIS - VISUALIZATION SUITE".center(70))
    print("=" * 70)

    # Fetch and process data
    print("\n[Preparing Data]")
    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if not season_data:
        logger.error("Failed to fetch season data")
        return False

    pipeline = Pipeline()
    races = season_data.get("races", [])

    # Process first 3 races
    print(f"Processing {min(3, len(races))} races...")
    all_race_data = []

    for race in races[:3]:
        round_num = int(race.get("round", 0))
        laps_data = fetcher.fetch_race_laps(2024, round_num)

        if laps_data:
            race.update(laps_data)

        df = pipeline.process_race(2024, round_num, race)
        if df is not None:
            all_race_data.append(df)

    if not all_race_data:
        logger.error("No race data processed")
        return False

    import pandas as pd
    combined_df = pd.concat(all_race_data, ignore_index=True)

    print(f"✓ Processed {len(all_race_data)} races with {len(combined_df)} lap records")

    # Get single race for detailed analysis
    single_race_df = all_race_data[0]
    race_round = int(single_race_df["round"].iloc[0])

    print(f"\nGenerating visualizations for {len(all_race_data)} races...")

    # Output directory
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    # Create visualizations
    figs = []
    names = []

    # 1. Pace progression (all races combined)
    print("\n  1. Pace Progression Chart...")
    try:
        fig = plot_pace_progression(combined_df, title="Pace Progression - Multiple Races")
        save_figure(fig, "01_pace_progression", str(output_dir))
        figs.append(fig)
        names.append("Pace Progression")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # 2. Lap time distribution
    print("  2. Lap Time Distribution...")
    try:
        fig = plot_lap_time_distribution(combined_df, title="Lap Time Distribution")
        save_figure(fig, "02_lap_distribution", str(output_dir))
        figs.append(fig)
        names.append("Lap Time Distribution")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # 3. Driver comparison
    print("  3. Driver Comparison...")
    try:
        fig = plot_driver_comparison(combined_df, title="Average Pace by Driver")
        save_figure(fig, "03_driver_comparison", str(output_dir))
        figs.append(fig)
        names.append("Driver Comparison")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # 4. Pace delta scatter
    print("  4. Pace Delta (Lap-to-Lap Change)...")
    try:
        fig = plot_pace_delta_scatter(single_race_df, title=f"Pace Delta - Race Round {race_round}")
        save_figure(fig, "04_pace_delta", str(output_dir))
        figs.append(fig)
        names.append("Pace Delta")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # 5. Degradation heatmap (limited to prevent huge charts)
    print("  5. Degradation Heatmap...")
    try:
        # Limit to first race for readability
        heatmap_df = all_race_data[0].copy()
        fig = plot_degradation_heatmap(heatmap_df, title=f"Tire Degradation - Race {race_round}")
        save_figure(fig, "05_degradation_heatmap", str(output_dir))
        figs.append(fig)
        names.append("Degradation Heatmap")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # 6. Individual driver trend
    print("  6. Individual Driver Trend...")
    try:
        top_driver = combined_df.groupby("driver_id")["lap_time_seconds"].mean().idxmin()
        fig = plot_pace_with_trend(combined_df, top_driver, window=3, title=f"{top_driver} - Pace with Trend")
        save_figure(fig, "06_driver_trend", str(output_dir))
        figs.append(fig)
        names.append(f"Driver Trend ({top_driver})")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # 7. Multi-driver comparison
    print("  7. Multi-Driver Comparison (4-panel)...")
    try:
        top_4 = (
            combined_df.groupby("driver_id")["lap_time_seconds"]
            .mean()
            .sort_values()
            .head(4)
            .index.tolist()
        )
        fig = plot_multi_driver_comparison(combined_df, top_4, title="Top 4 Drivers - Individual Pace")
        save_figure(fig, "07_multi_driver_comparison", str(output_dir))
        figs.append(fig)
        names.append("Multi-Driver Comparison")
        print("     ✓ Created")
    except Exception as e:
        print(f"     ✗ Error: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("VISUALIZATION SUMMARY".center(70))
    print("=" * 70)

    print(f"\n✓ Generated {len(figs)} visualizations:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")

    print(f"\n✓ All charts saved to: {output_dir}")
    print("\nYou can now:")
    print("  - View PNG files in outputs/ directory")
    print("  - Use these as references for Jupyter notebooks")
    print("  - Incorporate into reports and presentations")

    print("\n" + "=" * 70 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
