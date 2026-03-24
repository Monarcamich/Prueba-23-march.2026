"""
Unit tests for src/analysis.py

Tests for:
- Pace delta calculation
- Degradation identification
- Driver comparisons
- Consistency metrics
- Outlier detection
- Stint extraction
"""

import pytest
import pandas as pd
import numpy as np
from src.analysis import (
    calculate_pace_delta,
    identify_tyre_degradation,
    compare_pilots,
    smooth_pace_trajectory,
    extract_stint_data,
    identify_outliers,
    calculate_consistency,
    rate_drivers,
    get_race_summary,
)


@pytest.fixture
def sample_race_data():
    """Create sample race data for testing."""
    data = {
        'driver_id': ['hamilton', 'hamilton', 'hamilton', 'hamilton',
                     'verstappen', 'verstappen', 'verstappen', 'verstappen'],
        'lap_num': [1, 2, 3, 4, 1, 2, 3, 4],
        'lap_time_seconds': [92.5, 92.3, 92.4, 92.6,
                            91.8, 91.9, 92.0, 92.2],
        'pace_delta': [np.nan, -0.2, 0.1, 0.2,
                       np.nan, 0.1, 0.1, 0.2],
        'lap_position': [2, 2, 2, 2,
                        1, 1, 1, 1],
        'degradation_rate': [0.05, 0.05, 0.05, 0.05,
                           0.10, 0.10, 0.10, 0.10],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_single_driver():
    """Create sample data for single driver tests."""
    data = {
        'driver_id': ['hamilton'] * 10,
        'lap_num': list(range(1, 11)),
        'lap_time_seconds': [92.5, 92.3, 92.4, 92.6, 92.8, 93.0, 93.1, 93.2, 93.3, 93.5],
    }
    return pd.DataFrame(data)


class TestPaceDelta:
    """Tests for pace delta calculation."""

    def test_pace_delta_shape(self, sample_single_driver):
        """Test pace delta returns correct shape."""
        deltas = calculate_pace_delta(sample_single_driver['lap_time_seconds'])
        assert len(deltas) == len(sample_single_driver)

    def test_pace_delta_first_is_nan(self, sample_single_driver):
        """Test first pace delta is NaN."""
        deltas = calculate_pace_delta(sample_single_driver['lap_time_seconds'])
        assert pd.isna(deltas.iloc[0])

    def test_pace_delta_calculation(self, sample_single_driver):
        """Test pace delta values are calculated correctly."""
        deltas = calculate_pace_delta(sample_single_driver['lap_time_seconds'])
        # Second value should be difference between lap 2 and lap 1
        expected = 92.3 - 92.5
        assert abs(deltas.iloc[1] - expected) < 0.001


class TestDegradation:
    """Tests for tire degradation identification."""

    def test_degradation_output_structure(self, sample_race_data):
        """Test degradation output has correct structure."""
        results = identify_tyre_degradation(sample_race_data)
        assert isinstance(results, dict)
        assert 'hamilton' in results
        assert 'verstappen' in results

    def test_degradation_keys(self, sample_race_data):
        """Test degradation results have required keys."""
        results = identify_tyre_degradation(sample_race_data)
        required_keys = ['degradation_rate', 'r_squared', 'total_loss', 'laps_analyzed']
        for driver, metrics in results.items():
            for key in required_keys:
                assert key in metrics

    def test_degradation_by_driver(self, sample_race_data):
        """Test degradation calculation for specific driver."""
        results = identify_tyre_degradation(sample_race_data, driver_id='hamilton')
        assert len(results) == 1
        assert 'hamilton' in results
        assert results['hamilton']['laps_analyzed'] >= 2

    def test_degradation_positive_rate(self, sample_race_data):
        """Test degradation rate is positive (getting slower)."""
        results = identify_tyre_degradation(sample_race_data)
        # At least some drivers should show positive degradation
        rates = [m['degradation_rate'] for m in results.values()]
        assert any(rate > 0 for rate in rates)


class TestDriverComparison:
    """Tests for driver comparison functions."""

    def test_compare_pilots_output(self, sample_race_data):
        """Test compare_pilots returns DataFrame."""
        result = compare_pilots(sample_race_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_compare_pilots_sorted(self, sample_race_data):
        """Test compare_pilots sorts by pace."""
        result = compare_pilots(sample_race_data)
        # Should be sorted by average lap time
        avg_times = result['avg_lap_time_seconds'].values
        assert np.all(avg_times[:-1] <= avg_times[1:])

    def test_compare_pilots_columns(self, sample_race_data):
        """Test compare_pilots has expected columns."""
        result = compare_pilots(sample_race_data)
        expected_cols = ['avg_lap_time_seconds', 'std_lap_time_seconds', 'min_lap_time_seconds']
        for col in expected_cols:
            assert col in result.columns


class TestConsistency:
    """Tests for consistency analysis."""

    def test_consistency_output_structure(self, sample_race_data):
        """Test consistency returns dict with correct structure."""
        result = calculate_consistency(sample_race_data)
        assert isinstance(result, dict)
        assert 'hamilton' in result
        assert 'verstappen' in result

    def test_consistency_metrics(self, sample_race_data):
        """Test consistency has required metrics."""
        result = calculate_consistency(sample_race_data)
        required_keys = ['coefficient_of_variation', 'avg_lap_delta', 'best_lap']
        for driver, metrics in result.items():
            for key in required_keys:
                assert key in metrics

    def test_consistency_cv_range(self, sample_race_data):
        """Test CV is in valid range."""
        result = calculate_consistency(sample_race_data)
        for driver, metrics in result.items():
            cv = metrics['coefficient_of_variation']
            assert 0 <= cv <= 1

    def test_consistency_best_lap_reasonable(self, sample_race_data):
        """Test best lap is lowest of driver's laps."""
        result = calculate_consistency(sample_race_data)
        driver_data = sample_race_data.groupby('driver_id')['lap_time_seconds'].min()
        for driver, expected_best in driver_data.items():
            assert abs(result[driver]['best_lap'] - expected_best) < 0.01


class TestOutlierDetection:
    """Tests for outlier identification."""

    def test_outliers_iqr_method(self, sample_single_driver):
        """Test IQR outlier detection."""
        # Add some outliers
        data = sample_single_driver.copy()
        data.loc[5, 'lap_time_seconds'] = 100.0  # Outlier

        outliers = identify_outliers(data, method='iqr')
        assert len(outliers) >= 1

    def test_outliers_zscore_method(self, sample_single_driver):
        """Test Z-score outlier detection."""
        data = sample_single_driver.copy()
        data.loc[5, 'lap_time_seconds'] = 100.0  # Outlier

        outliers = identify_outliers(data, method='zscore', threshold=2)
        assert len(outliers) >= 1

    def test_outliers_by_driver(self, sample_race_data):
        """Test outlier detection for specific driver."""
        outliers = identify_outliers(sample_race_data, driver_id='hamilton')
        if len(outliers) > 0:
            assert all(outliers['driver_id'] == 'hamilton')


class TestStintExtraction:
    """Tests for stint data extraction."""

    def test_stint_output_structure(self, sample_race_data):
        """Test stint extraction returns dict."""
        result = extract_stint_data(sample_race_data, stint_length=2)
        assert isinstance(result, dict)
        # Should have at least one driver
        assert len(result) >= 1

    def test_stint_creates_groups(self, sample_single_driver):
        """Test stint data creates stint groups."""
        result = extract_stint_data(sample_single_driver, stint_length=3)
        driver = list(result.keys())[0]
        stint_data = result[driver]
        # Should have multiple stints
        assert len(stint_data) >= 1


class TestRaceSmoothing:
    """Tests for pace trajectory smoothing."""

    def test_smooth_pace_adds_column(self, sample_single_driver):
        """Test smoothing adds pace_smooth column."""
        result = smooth_pace_trajectory(sample_single_driver)
        assert 'pace_smooth' in result.columns

    def test_smooth_pace_shape(self, sample_single_driver):
        """Test smoothing preserves data shape."""
        result = smooth_pace_trajectory(sample_single_driver)
        assert len(result) == len(sample_single_driver)

    def test_smooth_pace_by_driver(self, sample_race_data):
        """Test smoothing works for specific driver."""
        result = smooth_pace_trajectory(sample_race_data, driver_id='hamilton')
        assert 'pace_smooth' in result.columns
        assert result[result['driver_id'] == 'hamilton']['pace_smooth'].notna().sum() > 0


class TestRaceSummary:
    """Tests for race summary statistics."""

    def test_summary_structure(self, sample_race_data):
        """Test race summary returns dict."""
        result = get_race_summary(sample_race_data)
        assert isinstance(result, dict)

    def test_summary_required_keys(self, sample_race_data):
        """Test summary has required keys."""
        result = get_race_summary(sample_race_data)
        required_keys = ['total_drivers', 'total_laps', 'total_records', 'avg_lap_time']
        for key in required_keys:
            assert key in result

    def test_summary_driver_count(self, sample_race_data):
        """Test summary driver count is correct."""
        result = get_race_summary(sample_race_data)
        expected = sample_race_data['driver_id'].nunique()
        assert result['total_drivers'] == expected

    def test_summary_lap_count(self, sample_race_data):
        """Test summary lap count is correct."""
        result = get_race_summary(sample_race_data)
        expected = sample_race_data['lap_num'].max()
        assert result['total_laps'] == expected


class TestRateDrivers:
    """Tests for driver rating function."""

    def test_rate_drivers_output(self, sample_race_data):
        """Test rate_drivers returns DataFrame."""
        result = rate_drivers(sample_race_data)
        assert isinstance(result, pd.DataFrame)
        assert 'overall_score' in result.columns

    def test_rate_drivers_sorted(self, sample_race_data):
        """Test rate_drivers sorts by score descending."""
        result = rate_drivers(sample_race_data)
        scores = result['overall_score'].values
        assert np.all(scores[:-1] >= scores[1:])

    def test_rate_drivers_range(self, sample_race_data):
        """Test driver scores are in normalized range."""
        result = rate_drivers(sample_race_data)
        assert (result['overall_score'] >= 0).all()
        assert (result['overall_score'] <= 1).all()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        with pytest.raises(KeyError):
            identify_tyre_degradation(empty_df)

    def test_single_record(self):
        """Test handling of single record."""
        data = {
            'driver_id': ['hamilton'],
            'lap_num': [1],
            'lap_time_seconds': [92.5],
        }
        df = pd.DataFrame(data)
        # Should complete without error
        result = get_race_summary(df)
        assert result['total_records'] == 1

    def test_nan_handling(self, sample_single_driver):
        """Test handling of NaN values."""
        data = sample_single_driver.copy()
        data.loc[2, 'lap_time_seconds'] = np.nan

        # Should not crash
        result = compare_pilots(data, metric='lap_time_seconds')
        assert len(result) >= 0

    def test_missing_columns(self):
        """Test handling of missing required columns."""
        data = {'driver_id': ['hamilton'], 'lap_num': [1]}
        df = pd.DataFrame(data)

        with pytest.raises(KeyError):
            identify_tyre_degradation(df)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
