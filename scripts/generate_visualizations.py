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
from src.analysis import (
    identify_tyre_degradation,
    calculate_consistency,
    compare_pilots,
    extract_stint_data,
)
from src.visualizers import (
    plot_pace_progression,
    plot_lap_time_distribution,
    plot_driver_comparison,
    plot_degradation_heatmap,
    plot_pace_delta_scatter,
    plot_pace_with_trend,
    plot_multi_driver_comparison,
    plot_degradation_comparison,
    plot_consistency_analysis,
    plot_prediction_vs_actual,
    plot_cluster_analysis,
    save_figure,
    generate_all_visualizations,
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

    print(f"\nAnalyzing data and generating visualizations...")

    # Run analysis functions
    print("  - Analyzing tire degradation...")
    degradation = identify_tyre_degradation(single_race_df)

    print("  - Analyzing driver consistency...")
    consistency = calculate_consistency(single_race_df)

    print("  - Comparing drivers...")
    comparison = compare_pilots(single_race_df)

    print("  - Extracting stint data...")
    stints = extract_stint_data(single_race_df)

    # Output directory
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    # Generate all visualizations
    print(f"\nGenerating {11} visualization charts...")
    generated = generate_all_visualizations(
        single_race_df,
        degradation_dict=degradation,
        consistency_dict=consistency,
        comparison_df=comparison,
        output_dir=str(output_dir)
    )

    # Summary
    print("\n" + "=" * 70)
    print("VISUALIZATION GENERATION COMPLETE".center(70))
    print("=" * 70)

    print(f"\n✓ Generated {len(generated)} visualizations:\n")
    for i, (name, filename) in enumerate(sorted(generated.items()), 1):
        print(f"  {i:2d}. {name:25s} → {filename}")

    print(f"\n📊 All charts saved to: {output_dir}")
    print("\nGenerated visualizations:")
    print("  • Pace progression over race")
    print("  • Lap time distribution by driver")
    print("  • Driver pace comparison")
    print("  • Pace delta heatmap (degradation)")
    print("  • Advanced degradation analysis")
    print("  • Driver consistency metrics")
    print("  • Pace delta scatter plots")
    print("  • Prediction vs actual (ML models)")
    print("  • Driver clustering analysis")

    print("\n" + "=" * 70 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
