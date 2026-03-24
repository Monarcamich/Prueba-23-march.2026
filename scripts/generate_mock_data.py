"""
Mock data generator for F1 Rhythm Analysis.

Generates realistic sample data that mirrors Ergast API structure
for local development and testing without internet connectivity.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Sample drivers for 2024 season
DRIVERS_2024 = [
    {"driverId": "max_verstappen", "code": "VER", "surname": "Verstappen", "givenName": "Max"},
    {"driverId": "lewis_hamilton", "code": "HAM", "surname": "Hamilton", "givenName": "Lewis"},
    {"driverId": "lando_norris", "code": "NOR", "surname": "Norris", "givenName": "Lando"},
    {"driverId": "charles_leclerc", "code": "LEC", "surname": "Leclerc", "givenName": "Charles"},
    {"driverId": "carlos_sainz", "code": "SAI", "surname": "Sainz", "givenName": "Carlos"},
    {"driverId": "george_russell", "code": "RUS", "surname": "Russell", "givenName": "George"},
    {"driverId": "oscar_piastri", "code": "PIA", "surname": "Piastri", "givenName": "Oscar"},
    {"driverId": "fernando_alonso", "code": "ALO", "surname": "Alonso", "givenName": "Fernando"},
    {"driverId": "nico_hulkenberg", "code": "HUL", "surname": "Hülkenberg", "givenName": "Nico"},
    {"driverId": "yuki_tsunoda", "code": "TSU", "surname": "Tsunoda", "givenName": "Yuki"},
]

# Sample races for 2024
RACES_2024 = [
    {"round": "1", "raceName": "Bahrain Grand Prix", "date": "2024-03-02", "circuit": "bahrain"},
    {"round": "2", "raceName": "Saudi Arabian Grand Prix", "date": "2024-03-09", "circuit": "saudi_arabia"},
    {"round": "3", "raceName": "Australian Grand Prix", "date": "2024-03-24", "circuit": "albert_park"},
    {"round": "4", "raceName": "Japanese Grand Prix", "date": "2024-04-07", "circuit": "suzuka"},
    {"round": "5", "raceName": "Chinese Grand Prix", "date": "2024-04-21", "circuit": "shanghai"},
]


def generate_lap_times(num_drivers: int, num_laps: int, driver_pace_variance: dict = None) -> dict:
    """
    Generate realistic lap times with:
    - Baseline pace difference between drivers
    - Tire degradation over laps
    - Random variation (yellow flags, track conditions)
    """
    if driver_pace_variance is None:
        driver_pace_variance = {i: random.uniform(0, 1.5) for i in range(num_drivers)}

    laps = {}
    base_time = 90.0  # Base lap time in seconds

    for lap_num in range(1, num_laps + 1):
        timings = []

        for driver_idx in range(num_drivers):
            # Base pace for driver (0.8-2.0 seconds slower than fastest)
            driver_offset = driver_pace_variance.get(driver_idx, random.uniform(0, 1.5))

            # Tire degradation (faster in early laps, slower later)
            if lap_num <= 5:  # Fresh tires
                degradation = 0
            elif lap_num <= 15:  # Mid-stint
                degradation = (lap_num - 5) * 0.05
            else:  # Tire wear
                degradation = (lap_num - 15) * 0.15 + 0.5

            # Random variation
            noise = random.gauss(0, 0.3)

            lap_time = base_time + driver_offset + degradation + noise

            # Format time as MM:SS.mmm
            minutes = int(lap_time // 60)
            seconds = lap_time % 60
            time_str = f"{minutes}:{seconds:06.3f}"

            timings.append({
                "driverId": DRIVERS_2024[driver_idx]["driverId"],
                "position": str(driver_idx + 1),
                "time": time_str
            })

        laps[str(lap_num)] = {
            "number": str(lap_num),
            "Timings": timings
        }

    return laps


def generate_race_result(race_id: int, race_name: str):
    """Generate race results with position, points, lap count."""
    results = []
    points_table = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

    for pos, driver in enumerate(DRIVERS_2024[:10]):
        results.append({
            "number": str(pos + 1),
            "position": str(pos + 1),
            "positionText": str(pos + 1),
            "points": str(points_table[pos]),
            "Driver": driver,
            "laps": str(58 - random.randint(0, 5)),
            "status": "Finished" if pos < 8 else random.choice(["Finished", "+1 Lap", "Retired"])
        })

    return results


def create_mock_data_structure():
    """Create mock data mirroring Ergast API structure."""
    data = {
        "2024": {
            "season": "2024",
            "drivers": DRIVERS_2024,
            "races": []
        }
    }

    for race_idx, race_info in enumerate(RACES_2024):
        race = {
            "round": race_info["round"],
            "raceName": race_info["raceName"],
            "date": race_info["date"],
            "Circuit": {"circuitId": race_info["circuit"]},
            "Results": generate_race_result(race_idx, race_info["raceName"]),
            "Laps": generate_lap_times(len(DRIVERS_2024), 58, None)
        }
        data["2024"]["races"].append(race)

    return data


def save_mock_data(output_dir: Path):
    """Save mock data to JSON files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating mock F1 data...")
    mock_data = create_mock_data_structure()

    # Save season overview
    season_file = output_dir / "mock_season_2024.json"
    with open(season_file, "w") as f:
        json.dump(mock_data["2024"], f, indent=2)
    print(f"✓ Created {season_file}")

    # Save individual race data
    races_dir = output_dir / "races"
    races_dir.mkdir(exist_ok=True)

    for race in mock_data["2024"]["races"]:
        race_file = races_dir / f"2024_r{race['round']}_{race['raceName'].lower().replace(' ', '_')}.json"
        with open(race_file, "w") as f:
            json.dump(race, f, indent=2)
        print(f"✓ Created {race_file.name}")

    print(f"\nMock data saved to {output_dir}")
    return mock_data


if __name__ == "__main__":
    mock_dir = Path(__file__).parent.parent / "data" / "mock"
    save_mock_data(mock_dir)
