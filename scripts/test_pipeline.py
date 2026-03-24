#!/usr/bin/env python3
"""
Test script for F1 Rhythm Analysis pipeline.

Demonstrates:
1. Data fetching from mock data
2. ETL processing through all 3 layers
3. Basic analysis on the results
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import get_fetcher
from src.etl_pipeline import Pipeline, PipelineConfig
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run pipeline test."""
    print("\n" + "=" * 70)
    print("F1 RHYTHM ANALYSIS - PIPELINE TEST".center(70))
    print("=" * 70)

    # Step 1: Fetch data
    print("\n[Step 1] Fetching season data...")
    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if not season_data:
        logger.error("Failed to fetch season data")
        return False

    print(f"✓ Fetched 2024 season data")
    print(f"  - Drivers: {len(season_data.get('drivers', []))}")
    print(f"  - Races: {len(season_data.get('races', []))}")

    # Step 2: Initialize pipeline
    print("\n[Step 2] Initializing ETL pipeline...")
    pipeline = Pipeline()
    print("✓ Pipeline initialized")

    # Step 3: Process races
    print("\n[Step 3] Processing races through pipeline...")
    races = season_data.get("races", [])

    if not races:
        logger.error("No races found")
        return False

    # Process first 2 races as test
    test_races = races[:2]
    results = {}

    for race in test_races:
        round_num = int(race.get("round", 0))
        race_name = race.get("raceName", f"Race {round_num}")

        print(f"\n  Processing R{round_num}: {race_name}...")

        # Fetch lap data
        laps_data = fetcher.fetch_race_laps(2024, round_num)
        if laps_data:
            race = {**race, **laps_data}

        # Process through pipeline
        result_df = pipeline.process_race(2024, round_num, race)

        if result_df is not None:
            results[round_num] = result_df
            print(f"    ✓ Processed {len(result_df)} lap records")
        else:
            print(f"    ✗ Failed to process race")

    # Step 4: Analyze results
    print("\n[Step 4] Analyzing results...")

    all_results = pd.concat(results.values(), ignore_index=True)

    print(f"\n✓ Total races processed: {len(results)}")
    print(f"✓ Total lap records: {len(all_results)}")
    print(f"✓ Unique drivers: {all_results['driver_id'].nunique()}")

    # Sample statistics
    print("\n[Results Summary]")
    print(f"\nPace Delta Statistics (seconds/lap):")
    pace_stats = all_results["pace_delta"].describe()
    print(f"  Mean: {pace_stats['mean']:.4f}")
    print(f"  Std:  {pace_stats['std']:.4f}")
    print(f"  Min:  {pace_stats['min']:.4f}")
    print(f"  Max:  {pace_stats['max']:.4f}")

    print(f"\nLap Time Statistics (seconds):")
    time_stats = all_results["lap_time_seconds"].describe()
    print(f"  Mean: {time_stats['mean']:.2f}")
    print(f"  Std:  {time_stats['std']:.2f}")
    print(f"  Min:  {time_stats['min']:.2f}")
    print(f"  Max:  {time_stats['max']:.2f}")

    # Top drivers by average pace
    print(f"\nTop 5 Drivers by Average Pace:")
    top_drivers = (
        all_results.groupby("driver_id")["lap_time_seconds"]
        .mean()
        .sort_values()
        .head(5)
    )
    for idx, (driver_id, avg_time) in enumerate(top_drivers.items(), 1):
        print(f"  {idx}. {driver_id}: {avg_time:.2f}s")

    # Degradation rates
    print(f"\nDegradation Rates (seconds/lap):")
    deg_stats = all_results["degradation_rate"].dropna().describe()
    print(f"  Mean: {deg_stats['mean']:.4f}")
    print(f"  Drivers with measurable degradation: {all_results['degradation_rate'].notna().sum()}")

    print("\n" + "=" * 70)
    print("✓ PIPELINE TEST PASSED".center(70))
    print("=" * 70 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
