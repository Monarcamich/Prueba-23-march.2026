"""
ETL Pipeline for F1 Rhythm Analysis.

3-layer architecture:
1. Bronze: Raw data from API/files
2. Silver: Cleaned, validated, normalized data
3. Gold: Enriched data with derived metrics (pace deltas, degradation estimates, etc.)
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for ETL pipeline."""
    base_dir: Path = None
    bronze_dir: Path = None
    silver_dir: Path = None
    gold_dir: Path = None

    def __post_init__(self):
        if self.base_dir is None:
            self.base_dir = Path(__file__).parent.parent / "data"

        self.bronze_dir = self.bronze_dir or self.base_dir / "bronze"
        self.silver_dir = self.silver_dir or self.base_dir / "silver"
        self.gold_dir = self.gold_dir or self.base_dir / "gold"

        # Create directories
        for d in [self.bronze_dir, self.silver_dir, self.gold_dir]:
            d.mkdir(parents=True, exist_ok=True)


class BronzeLayer:
    """Bronze layer: Store raw data as-is from source."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()

    def save_raw_race(self, season: int, round_num: int, race_data: Dict[str, Any]) -> Path:
        """Save raw race data to bronze layer."""
        output_file = self.config.bronze_dir / f"{season}_r{round_num}_raw.json"

        with open(output_file, "w") as f:
            json.dump(race_data, f, indent=2)

        logger.info(f"✓ Bronze: Saved {season} R{round_num} to {output_file.name}")
        return output_file

    def load_raw_race(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Load raw race data from bronze layer."""
        input_file = self.config.bronze_dir / f"{season}_r{round_num}_raw.json"

        if not input_file.exists():
            logger.warning(f"Bronze data not found: {input_file}")
            return None

        with open(input_file, "r") as f:
            return json.load(f)


class SilverLayer:
    """Silver layer: Clean, validate, and normalize data."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.bronze = BronzeLayer(config)

    def transform_race(self, season: int, round_num: int) -> Optional[pd.DataFrame]:
        """
        Transform raw race data to cleaned dataframe.

        Converts lap times from MM:SS.mmm format to seconds (float).
        Validates data integrity.
        """
        raw_race = self.bronze.load_raw_race(season, round_num)
        if not raw_race:
            logger.error(f"Failed to load raw data for {season} R{round_num}")
            return None

        try:
            # Extract laps data
            laps_dict = raw_race.get("Laps", {})

            records = []

            for lap_num, lap_data in laps_dict.items():
                timings = lap_data.get("Timings", [])

                for timing in timings:
                    driver_id = timing.get("driverId")
                    time_str = timing.get("time", "")

                    # Convert time from MM:SS.mmm to seconds
                    lap_time_seconds = self._parse_lap_time(time_str)

                    if lap_time_seconds is None:
                        logger.warning(f"Invalid time format for driver {driver_id}: {time_str}")
                        continue

                    records.append({
                        "season": season,
                        "round": round_num,
                        "lap_num": int(lap_num),
                        "driver_id": driver_id,
                        "lap_time_seconds": float(lap_time_seconds),
                        "timestamp": datetime.now().isoformat()
                    })

            if not records:
                logger.error(f"No valid lap data found for {season} R{round_num}")
                return None

            df = pd.DataFrame(records)

            # Validate data
            if not self._validate_data(df):
                logger.error(f"Data validation failed for {season} R{round_num}")
                return None

            # Save to silver layer
            self._save_silver_data(df, season, round_num)

            logger.info(f"✓ Silver: Cleaned {season} R{round_num} ({len(df)} records)")
            return df

        except Exception as e:
            logger.error(f"Error transforming race {season} R{round_num}: {e}")
            return None

    @staticmethod
    def _parse_lap_time(time_str: str) -> Optional[float]:
        """Convert MM:SS.mmm format to seconds."""
        try:
            if not time_str or ":" not in time_str:
                return None

            parts = time_str.split(":")
            if len(parts) != 2:
                return None

            minutes = int(parts[0])
            seconds = float(parts[1])

            return minutes * 60 + seconds

        except (ValueError, IndexError):
            return None

    @staticmethod
    def _validate_data(df: pd.DataFrame) -> bool:
        """Validate cleaned data."""
        # Check for required columns
        required_cols = {"season", "round", "lap_num", "driver_id", "lap_time_seconds"}
        if not required_cols.issubset(df.columns):
            logger.error(f"Missing columns: {required_cols - set(df.columns)}")
            return False

        # Check for null values in key columns
        if df[["driver_id", "lap_time_seconds"]].isnull().any().any():
            logger.error("Found null values in key columns")
            return False

        # Check for reasonable lap times (between 60 and 300 seconds)
        invalid_times = df[(df["lap_time_seconds"] < 60) | (df["lap_time_seconds"] > 300)]
        if len(invalid_times) > 0:
            logger.warning(f"Found {len(invalid_times)} potentially invalid lap times")

        return True

    def _save_silver_data(self, df: pd.DataFrame, season: int, round_num: int) -> Path:
        """Save cleaned data to silver layer."""
        output_file = self.config.silver_dir / f"{season}_r{round_num}_clean.csv"

        df.to_csv(output_file, index=False)
        logger.info(f"  Saved to {output_file.name}")
        return output_file

    def load_silver_data(self, season: int, round_num: int) -> Optional[pd.DataFrame]:
        """Load cleaned data from silver layer."""
        input_file = self.config.silver_dir / f"{season}_r{round_num}_clean.csv"

        if not input_file.exists():
            return None

        return pd.read_csv(input_file)


class GoldLayer:
    """Gold layer: Derive metrics and create analysis-ready data."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.silver = SilverLayer(config)

    def create_analysis_dataset(self, season: int, round_num: int) -> Optional[pd.DataFrame]:
        """
        Create analysis-ready dataset with derived metrics.

        Adds:
        - pace_delta: Change in lap time from previous lap
        - lap_position: Relative ranking by lap time
        - tyre_age_estimate: Estimated lap count in current stint
        - degradation_rate: m/s change per lap
        """
        df = self.silver.load_silver_data(season, round_num)
        if df is None:
            # Try transforming from raw
            df = self.silver.transform_race(season, round_num)

        if df is None:
            logger.error(f"Failed to load silver data for {season} R{round_num}")
            return None

        try:
            # Sort by driver and lap
            df = df.sort_values(["driver_id", "lap_num"]).reset_index(drop=True)

            # Calculate pace delta
            df["pace_delta"] = df.groupby("driver_id")["lap_time_seconds"].diff()

            # Calculate lap position (rank by time within each lap)
            df["lap_position"] = df.groupby("lap_num")["lap_time_seconds"].rank()

            # Estimate degradation rate
            for driver_id in df["driver_id"].unique():
                driver_laps = df[df["driver_id"] == driver_id].sort_values("lap_num")

                if len(driver_laps) >= 2:
                    # Calculate degradation per lap (seconds/lap)
                    time_diff = driver_laps["lap_time_seconds"].iloc[-1] - driver_laps["lap_time_seconds"].iloc[0]
                    lap_diff = driver_laps["lap_num"].iloc[-1] - driver_laps["lap_num"].iloc[0]

                    if lap_diff > 0:
                        degradation_rate = time_diff / lap_diff
                        df.loc[df["driver_id"] == driver_id, "degradation_rate"] = degradation_rate

            # Save to gold layer
            self._save_gold_data(df, season, round_num)

            logger.info(
                f"✓ Gold: Enhanced {season} R{round_num} with metrics "
                f"({len(df)} records, {df['driver_id'].nunique()} drivers)"
            )
            return df

        except Exception as e:
            logger.error(f"Error creating analysis dataset: {e}")
            return None

    def _save_gold_data(self, df: pd.DataFrame, season: int, round_num: int) -> Path:
        """Save enriched data to gold layer."""
        output_file = self.config.gold_dir / f"{season}_r{round_num}_analysis.csv"

        df.to_csv(output_file, index=False)
        logger.info(f"  Saved to {output_file.name}")
        return output_file

    def load_analysis_data(self, season: int, round_num: int) -> Optional[pd.DataFrame]:
        """Load analysis-ready data from gold layer."""
        input_file = self.config.gold_dir / f"{season}_r{round_num}_analysis.csv"

        if not input_file.exists():
            return None

        return pd.read_csv(input_file)


class Pipeline:
    """Main ETL Pipeline orchestrator."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.bronze = BronzeLayer(self.config)
        self.silver = SilverLayer(self.config)
        self.gold = GoldLayer(self.config)

    def process_race(self, season: int, round_num: int, raw_race_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Process a single race through all 3 layers.

        Returns analysis-ready DataFrame.
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing {season} R{round_num}")
        logger.info(f"{'=' * 60}")

        # Bronze: Save raw data
        self.bronze.save_raw_race(season, round_num, raw_race_data)

        # Silver: Clean and validate
        self.silver.transform_race(season, round_num)

        # Gold: Enrich with metrics
        analysis_df = self.gold.create_analysis_dataset(season, round_num)

        return analysis_df

    def process_season(self, season: int, races: List[Dict[str, Any]]) -> Dict[int, pd.DataFrame]:
        """Process all races in a season."""
        results = {}

        for race in races:
            round_num = int(race.get("round", 0))
            analysis_df = self.process_race(season, round_num, race)

            if analysis_df is not None:
                results[round_num] = analysis_df

        return results


if __name__ == "__main__":
    # Example usage
    from src.data_fetcher import get_fetcher

    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if season_data:
        pipeline = Pipeline()

        # Process first race
        races = season_data.get("races", [])
        if races:
            first_race = races[0]
            round_num = int(first_race.get("round", 0))

            # Fetch lap data
            laps_data = fetcher.fetch_race_laps(2024, round_num)
            first_race.update(laps_data or {})

            # Process
            result_df = pipeline.process_race(2024, round_num, first_race)

            if result_df is not None:
                print("\nSample analysis data:")
                print(result_df[["driver_id", "lap_num", "lap_time_seconds", "pace_delta", "lap_position"]].head(10))
