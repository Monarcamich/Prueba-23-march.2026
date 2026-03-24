"""
Data fetcher module for F1 Rhythm Analysis.

Handles data retrieval from:
1. Ergast API (primary)
2. Local mock data (fallback for offline development)

Provides abstraction layer for seamless data access.
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FetchConfig:
    """Configuration for data fetching."""
    ergast_base_url: str = "https://ergast.com/api/f1"
    timeout: int = 30
    use_mock_data: bool = True  # Default to mock for development
    mock_data_dir: Path = None
    retry_attempts: int = 3


class DataFetcher:
    """Fetch F1 data from Ergast API or local mock data."""

    def __init__(self, config: FetchConfig = None):
        self.config = config or FetchConfig()
        if self.config.mock_data_dir is None:
            self.config.mock_data_dir = Path(__file__).parent.parent / "data" / "mock"

    def fetch_season(self, season: int) -> Optional[Dict[str, Any]]:
        """Fetch all data for a season."""
        logger.info(f"Fetching season {season}...")

        if self.config.use_mock_data:
            return self._fetch_season_mock(season)
        else:
            return self._fetch_season_api(season)

    def _fetch_season_api(self, season: int) -> Optional[Dict[str, Any]]:
        """Fetch season data from Ergast API."""
        try:
            # Get races
            races_url = f"{self.config.ergast_base_url}/{season}/races.json"
            races_resp = requests.get(races_url, timeout=self.config.timeout)
            races_resp.raise_for_status()

            races_data = races_resp.json()
            races = races_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

            logger.info(f"✓ Retrieved {len(races)} races from Ergast API")

            # Get drivers
            drivers_url = f"{self.config.ergast_base_url}/{season}/drivers.json"
            drivers_resp = requests.get(drivers_url, timeout=self.config.timeout)
            drivers_resp.raise_for_status()

            drivers_data = drivers_resp.json()
            drivers = drivers_data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])

            logger.info(f"✓ Retrieved {len(drivers)} drivers from Ergast API")

            return {
                "season": str(season),
                "source": "ergast_api",
                "races": races,
                "drivers": drivers,
                "fetched_at": datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch from Ergast API: {e}")
            logger.info("Falling back to mock data...")
            return self._fetch_season_mock(season)
        except Exception as e:
            logger.error(f"Unexpected error fetching season {season}: {e}")
            return None

    def _fetch_season_mock(self, season: int) -> Optional[Dict[str, Any]]:
        """Fetch season data from local mock files."""
        try:
            mock_file = self.config.mock_data_dir / f"mock_season_{season}.json"

            if not mock_file.exists():
                logger.warning(f"Mock data file not found: {mock_file}")
                return None

            with open(mock_file, "r") as f:
                data = json.load(f)

            logger.info(f"✓ Loaded season {season} from mock data")
            logger.info(f"  - {len(data.get('drivers', []))} drivers")
            logger.info(f"  - {len(data.get('races', []))} races")

            return {
                "season": str(season),
                "source": "mock_data",
                **data,
                "fetched_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error loading mock data for season {season}: {e}")
            return None

    def fetch_race_laps(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Fetch lap times for a specific race."""
        logger.info(f"Fetching lap times for {season} R{round_num}...")

        if self.config.use_mock_data:
            return self._fetch_race_laps_mock(season, round_num)
        else:
            return self._fetch_race_laps_api(season, round_num)

    def _fetch_race_laps_api(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Fetch lap times from Ergast API."""
        try:
            url = f"{self.config.ergast_base_url}/{season}/{round_num}/laps.json"
            response = requests.get(url, timeout=self.config.timeout, params={"limit": 100})
            response.raise_for_status()

            data = response.json()
            race = data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0]

            laps = race.get("Laps", [])
            logger.info(f"✓ Retrieved {len(laps)} laps from Ergast API")

            return {
                "season": season,
                "round": round_num,
                "source": "ergast_api",
                "laps": laps,
                "fetched_at": datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch from Ergast API: {e}")
            return self._fetch_race_laps_mock(season, round_num)
        except Exception as e:
            logger.error(f"Error fetching laps: {e}")
            return None

    def _fetch_race_laps_mock(self, season: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Fetch lap times from local mock files."""
        try:
            # Find race file
            races_dir = self.config.mock_data_dir / "races"

            if not races_dir.exists():
                logger.warning(f"Mock races directory not found: {races_dir}")
                return None

            # Load all races and find the one matching round
            race_files = list(races_dir.glob(f"{season}_r{round_num}_*.json"))

            if not race_files:
                logger.warning(f"No mock race file found for {season} R{round_num}")
                return None

            with open(race_files[0], "r") as f:
                race = json.load(f)

            laps = race.get("Laps", {})
            logger.info(f"✓ Loaded {len(laps)} laps from mock data")

            return {
                "season": season,
                "round": round_num,
                "source": "mock_data",
                "laps": laps,
                "fetched_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error loading mock laps: {e}")
            return None

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """Validate fetched data structure."""
        if not data:
            return False

        required_keys = {"season", "source", "fetched_at"}
        if not required_keys.issubset(data.keys()):
            logger.error(f"Missing required keys in data: {required_keys - data.keys()}")
            return False

        return True


def get_fetcher(use_mock: bool = True) -> DataFetcher:
    """Factory function to get a DataFetcher instance."""
    config = FetchConfig(use_mock_data=use_mock)
    return DataFetcher(config)


if __name__ == "__main__":
    # Example usage
    fetcher = get_fetcher(use_mock=True)

    # Fetch season data
    season_data = fetcher.fetch_season(2024)
    if season_data:
        print(f"\nSeason: {season_data['season']}")
        print(f"Source: {season_data['source']}")
        print(f"Drivers: {len(season_data.get('drivers', []))}")
        print(f"Races: {len(season_data.get('races', []))}")

    # Fetch race laps
    print("\n" + "=" * 50)
    laps_data = fetcher.fetch_race_laps(2024, 1)
    if laps_data:
        print(f"Race: {laps_data['season']} R{laps_data['round']}")
        print(f"Source: {laps_data['source']}")
        print(f"Laps: {len(laps_data.get('laps', {}))}")
