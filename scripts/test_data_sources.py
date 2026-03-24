"""
Test script to prototype and validate F1 data sources.

Tests:
1. Ergast API connectivity and data structure
2. Data availability for multiple seasons
3. Response times and reliability
4. Data completeness (races, drivers, lap times)
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# Configuration
ERGAST_BASE_URL = "https://ergast.com/api/f1"
TIMEOUT = 30
TEST_SEASONS = [2023, 2024]  # Recent seasons for testing
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


class ErgastAPITester:
    """Test Ergast F1 API data source."""

    def __init__(self, base_url: str = ERGAST_BASE_URL, timeout: int = TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "data_samples": {},
        }

    def test_connectivity(self) -> bool:
        """Test basic API connectivity."""
        print("\n[1/4] Testing API Connectivity...")
        try:
            response = requests.get(f"{self.base_url}/drivers", timeout=self.timeout)
            success = response.status_code == 200
            print(f"  ✓ API is {'reachable' if success else 'unreachable'}")
            self.results["tests"].append({
                "name": "connectivity",
                "status": "pass" if success else "fail",
                "status_code": response.status_code
            })
            return success
        except Exception as e:
            print(f"  ✗ Connection failed: {str(e)}")
            self.results["tests"].append({
                "name": "connectivity",
                "status": "fail",
                "error": str(e)
            })
            return False

    def test_season_data(self) -> Dict[int, Dict[str, Any]]:
        """Test data availability for target seasons."""
        print("\n[2/4] Testing Season Data Availability...")
        season_stats = {}

        for season in TEST_SEASONS:
            print(f"\n  Testing Season {season}...")
            try:
                # Get races for season
                races_response = requests.get(
                    f"{self.base_url}/{season}/races",
                    timeout=self.timeout
                )
                races_response.raise_for_status()
                races_data = races_response.json()

                races = races_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
                num_races = len(races)
                print(f"    - Found {num_races} races")

                # Get drivers for season
                drivers_response = requests.get(
                    f"{self.base_url}/{season}/drivers",
                    timeout=self.timeout
                )
                drivers_response.raise_for_status()
                drivers_data = drivers_response.json()

                drivers = drivers_data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
                num_drivers = len(drivers)
                print(f"    - Found {num_drivers} drivers")

                season_stats[season] = {
                    "races": num_races,
                    "drivers": num_drivers,
                    "sample_races": [race.get("raceName") for race in races[:3]]
                }

                self.results["tests"].append({
                    "name": f"season_{season}",
                    "status": "pass",
                    "races": num_races,
                    "drivers": num_drivers
                })

            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                season_stats[season] = {"status": "failed", "error": str(e)}
                self.results["tests"].append({
                    "name": f"season_{season}",
                    "status": "fail",
                    "error": str(e)
                })

        return season_stats

    def test_lap_times(self) -> Dict[str, Any]:
        """Test lap time data availability and structure."""
        print("\n[3/4] Testing Lap Time Data...")
        season = 2024
        race_round = 1  # First race of season

        try:
            print(f"\n  Fetching lap times for {season} R{race_round}...")

            # Get lap times for a specific race
            start_time = time.time()
            laps_response = requests.get(
                f"{self.base_url}/{season}/{race_round}/laps",
                timeout=self.timeout,
                params={"limit": 100}  # Limit to first 100 laps
            )
            laps_response.raise_for_status()
            elapsed = time.time() - start_time

            laps_data = laps_response.json()
            laps_table = laps_data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0]

            laps = laps_table.get("Laps", [])
            num_laps = len(laps)

            print(f"    - Retrieved {num_laps} laps in {elapsed:.2f}s")
            print(f"    - Response size: {len(laps_response.text) / 1024:.2f} KB")

            # Extract sample lap data
            if laps:
                sample_lap = laps[0]
                timings = sample_lap.get("Timings", [])
                print(f"    - Drivers with times in lap 1: {len(timings)}")

                # Show structure
                if timings:
                    sample_timing = timings[0]
                    print(f"    - Sample timing structure:")
                    for key in sample_timing.keys():
                        print(f"      • {key}: {sample_timing[key]}")

            self.results["tests"].append({
                "name": "lap_times",
                "status": "pass",
                "laps_retrieved": num_laps,
                "fetch_time_seconds": elapsed,
                "drivers_per_lap": len(timings) if laps else 0
            })

            self.results["data_samples"]["lap_times"] = {
                "sample": laps[0] if laps else None,
                "total_laps": num_laps
            }

            return {
                "status": "success",
                "laps": num_laps,
                "fetch_time": elapsed,
                "drivers_per_lap": len(timings) if laps else 0
            }

        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            self.results["tests"].append({
                "name": "lap_times",
                "status": "fail",
                "error": str(e)
            })
            return {"status": "failed", "error": str(e)}

    def test_data_structure(self) -> Dict[str, Any]:
        """Test and document data structure from a full race."""
        print("\n[4/4] Testing Full Race Data Structure...")
        season, race_round = 2024, 1

        try:
            print(f"\n  Fetching full race data for {season} R{race_round}...")

            start_time = time.time()
            race_response = requests.get(
                f"{self.base_url}/{season}/{race_round}",
                timeout=self.timeout
            )
            race_response.raise_for_status()
            elapsed = time.time() - start_time

            race_data = race_response.json()
            race = race_data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0]

            print(f"    - Fetch time: {elapsed:.2f}s")
            print(f"    - Available fields in race object:")

            for key in race.keys():
                print(f"      • {key}")

            # Test results availability
            results_response = requests.get(
                f"{self.base_url}/{season}/{race_round}/results",
                timeout=self.timeout
            )
            results_response.raise_for_status()
            results_data = results_response.json()
            results = results_data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0].get("Results", [])

            print(f"    - Found {len(results)} race results")

            if results:
                sample_result = results[0]
                print(f"    - Sample result structure:")
                for key in sample_result.keys():
                    print(f"      • {key}")

            self.results["tests"].append({
                "name": "data_structure",
                "status": "pass",
                "race_fields": list(race.keys()),
                "results_count": len(results)
            })

            return {
                "status": "success",
                "race_fields": list(race.keys()),
                "results_count": len(results)
            }

        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            self.results["tests"].append({
                "name": "data_structure",
                "status": "fail",
                "error": str(e)
            })
            return {"status": "failed", "error": str(e)}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate report."""
        print("=" * 70)
        print("F1 Data Sources Test Suite".center(70))
        print("=" * 70)

        if not self.test_connectivity():
            print("\n⚠️  API is not reachable. Stopping tests.")
            return self.results

        season_stats = self.test_season_data()
        lap_times = self.test_lap_times()
        data_structure = self.test_data_structure()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY".center(70))
        print("=" * 70)

        passed = sum(1 for test in self.results["tests"] if test.get("status") == "pass")
        failed = sum(1 for test in self.results["tests"] if test.get("status") == "fail")

        print(f"\n✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"\nErgast API Status: {'🟢 READY' if failed == 0 else '🟡 PARTIAL'}")

        # Save results
        output_file = OUTPUT_DIR / "test_data_sources_report.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nReport saved to: {output_file}")

        return self.results


def main():
    """Run data source tests."""
    tester = ErgastAPITester()
    results = tester.run_all_tests()
    return results


if __name__ == "__main__":
    main()
