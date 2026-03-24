# F1 Rhythm Analysis - Quick Start Guide

## 🚀 Getting Started (5 minutes)

### 1. Verify Installation
```bash
cd f1-rhythm-analysis
/home/monarcamich/.venv/bin/python -c "import pandas; print('✓ Ready')"
```

### 2. Generate Sample Data
```bash
/home/monarcamich/.venv/bin/python scripts/generate_mock_data.py
```

### 3. Test the Pipeline
```bash
/home/monarcamich/.venv/bin/python scripts/test_pipeline.py
```

Expected output:
```
✓ PIPELINE TEST PASSED
```

### 4. Generate Visualizations
```bash
/home/monarcamich/.venv/bin/python scripts/generate_visualizations.py
```

Charts saved to `outputs/` directory.

---

## 📚 Project Modules

### `src/data_fetcher.py` - Data Sources
Fetch F1 data from Ergast API or local mock files.

**Quick Usage:**
```python
from src.data_fetcher import get_fetcher

fetcher = get_fetcher(use_mock=True)  # Use local mock data
season_data = fetcher.fetch_season(2024)
laps_data = fetcher.fetch_race_laps(2024, 1)  # Race 1

print(f"Drivers: {len(season_data['drivers'])}")
print(f"Laps in R1: {len(laps_data['laps'])}")
```

### `src/etl_pipeline.py` - Data Processing
Transform raw data through Bronze → Silver → Gold layers.

**Quick Usage:**
```python
from src.etl_pipeline import Pipeline
from src.data_fetcher import get_fetcher

fetcher = get_fetcher(use_mock=True)
pipeline = Pipeline()

# Process a single race
race_data = {...}  # Get from fetcher
analysis_df = pipeline.process_race(2024, 1, race_data)

print(analysis_df[['driver_id', 'lap_num', 'lap_time_seconds']].head())
```

### `src/analysis.py` - Analysis Functions
Reusable functions for data analysis.

**Quick Usage:**
```python
from src import analysis

# Tire degradation analysis
degradation = analysis.identify_tyre_degradation(df)
for driver, metrics in degradation.items():
    print(f"{driver}: {metrics['degradation_rate']:.4f} sec/lap")

# Driver consistency
consistency = analysis.calculate_consistency(df)

# Top drivers by pace
comparison = analysis.compare_pilots(df, metric='lap_time_seconds')
print(comparison.head())

# Smooth pace trajectory
df = analysis.smooth_pace_trajectory(df, window=3)
```

### `src/visualizers.py` - Visualizations
Publication-ready charts for analysis.

**Quick Usage:**
```python
from src.visualizers import (
    plot_pace_progression,
    plot_lap_time_distribution,
    plot_driver_comparison,
    save_figure
)

# Create visualizations
fig1 = plot_pace_progression(df, title="Race Pace")
fig2 = plot_lap_time_distribution(df)
fig3 = plot_driver_comparison(df)

# Save to PNG
save_figure(fig1, "my_chart", output_dir="outputs")
```

---

## 📊 Common Analysis Workflows

### Analyze a Single Race
```python
from src.data_fetcher import get_fetcher
from src.etl_pipeline import Pipeline
from src import analysis

# 1. Fetch data
fetcher = get_fetcher(use_mock=True)
season = fetcher.fetch_season(2024)
laps = fetcher.fetch_race_laps(2024, 1)

# 2. Process
race_data = {**season['races'][0], **laps}
pipeline = Pipeline()
df = pipeline.process_race(2024, 1, race_data)

# 3. Analyze
summary = analysis.get_race_summary(df)
print(summary)

degradation = analysis.identify_tyre_degradation(df)
consistency = analysis.calculate_consistency(df)
```

### Compare Multiple Races
```python
import pandas as pd

results = []
for race in season['races'][:3]:
    round_num = int(race['round'])
    laps = fetcher.fetch_race_laps(2024, round_num)
    race_data = {**race, **laps}
    
    df = pipeline.process_race(2024, round_num, race_data)
    results.append(df)

combined_df = pd.concat(results, ignore_index=True)

# Now analyze across all races
top_drivers = combined_df.groupby('driver_id')['lap_time_seconds'].mean().sort_values().head(5)
print(top_drivers)
```

### Find Consistency Patterns
```python
consistency = analysis.calculate_consistency(df)

# Sort by consistency (lower CV = more consistent)
consistent = sorted(consistency.items(), key=lambda x: x[1]['coefficient_of_variation'])
print("Most consistent drivers:")
for driver, metrics in consistent[:3]:
    print(f"  {driver}: {metrics['coefficient_of_variation']:.4f}")
```

---

## 📁 Data Files Location

```
data/
├── bronze/           # Raw data (JSON)
│   └── 2024_r1_raw.json
├── silver/          # Cleaned data (CSV)
│   └── 2024_r1_clean.csv
├── gold/            # Analysis-ready data (CSV)
│   └── 2024_r1_analysis.csv
└── mock/            # Mock data for development
    └── races/
```

### Understanding the Data

**Bronze (Raw):**
- Untouched data from API
- Preserves original structure
- Format: JSON

**Silver (Clean):**
- Validated, normalized data
- Lap times converted to seconds
- Removed invalid records
- Format: CSV

**Gold (Analysis):**
- Enriched with derived metrics:
  - `pace_delta`: Lap-to-lap time change
  - `lap_position`: Driver rank in each lap
  - `degradation_rate`: Tire wear per lap
- Format: CSV

---

## 🎯 Next Steps

### 1. Explore Your Own Races
Modify `scripts/generate_visualizations.py` to analyze:
- Different seasons
- Specific drivers
- Particular race events

### 2. Build Jupyter Notebooks
Create notebooks in `notebooks/` following the structure:
```
notebooks/
├── 01_eda_ritmo.ipynb          # Exploratory analysis
├── 02_visualizaciones.ipynb    # Visualization showcase
└── 03_modelos.ipynb            # Predictive models (optional)
```

### 3. Extend Functionality
Add new analysis functions to `src/analysis.py`:
```python
def my_custom_analysis(df):
    """My custom analysis function."""
    # Your code here
    return results
```

---

## 🔧 Troubleshooting

### Error: "API Unreachable"
**Expected when offline.** Solution: Ensure `USE_MOCK_DATA=true` in `.env`

### Error: "No module named 'src'"
Make sure you're running from the project root:
```bash
cd f1-rhythm-analysis
python scripts/test_pipeline.py  # ✓ Correct
# NOT: python ../scripts/test_pipeline.py  # ✗ Wrong
```

### Charts don't display
If running in notebook, add:
```python
%matplotlib inline
import matplotlib.pyplot as plt
```

### Memory issues with large datasets
Process by season instead of all at once:
```python
for season in [2023, 2024]:
    season_data = fetcher.fetch_season(season)
    # Process and save, don't keep all in memory
```

---

## 📖 Additional Resources

- **Project Structure**: See [README.md](README.md) for full documentation
- **Data Dictionary**: See README.md "Data Dictionary" section
- **Module Docstrings**: Read function docstrings in source files
  ```python
  from src import analysis
  help(analysis.identify_tyre_degradation)
  ```

---

## 💡 Tips & Tricks

### Quickly Check Race Data
```python
from src.data_fetcher import get_fetcher
fetcher = get_fetcher(use_mock=True)
season = fetcher.fetch_season(2024)

for race in season['races']:
    print(f"R{race['round']}: {race['raceName']}")
```

### Profile a Driver's Performance
```python
driver_id = 'max_verstappen'
df_driver = df[df['driver_id'] == driver_id].sort_values('lap_num')

print(f"Driver: {driver_id}")
print(f"  Avg Pace: {df_driver['lap_time_seconds'].mean():.2f}s")
print(f"  Best Lap: {df_driver['lap_time_seconds'].min():.2f}s")
print(f"  Degradation: {df_driver['degradation_rate'].iloc[0]:.4f} sec/lap")
```

### Export Analysis to CSV
```python
# Save analysis results
df.to_csv('outputs/race_analysis.csv', index=False)

# Export statistics
comparison.to_csv('outputs/driver_comparison.csv')
```

---

**Happy Analyzing!** 🏎️
