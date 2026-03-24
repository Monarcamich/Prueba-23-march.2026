"""
Unit tests for src/predictive_models.py

Tests for:
- TyreDegradationPredictor
- PaceTrajectoryPredictor
- DriverClusterer
"""

import pytest
import pandas as pd
import numpy as np
from src.predictive_models import (
    TyreDegradationPredictor,
    PaceTrajectoryPredictor,
    DriverClusterer,
)


@pytest.fixture
def sample_race_data():
    """Create sample race data for model testing."""
    data = {
        'driver_id': ['hamilton'] * 20 + ['verstappen'] * 20,
        'lap_num': list(range(1, 21)) * 2,
        'lap_time_seconds': (
            [92.5 + i * 0.05 for i in range(20)] +
            [91.8 + i * 0.08 for i in range(20)]
        ),
        'pace_delta': (
            [np.nan] + [0.05] * 19 +
            [np.nan] + [0.08] * 19
        ),
        'lap_position': [2] * 20 + [1] * 20,
        'degradation_rate': [0.05] * 20 + [0.08] * 20,
        'stint_lap': list(range(1, 21)) * 2,
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_analysis_data():
    """Create sample data with all required columns for analysis."""
    data = {
        'driver_id': ['hamilton'] * 15 + ['verstappen'] * 15 + ['sainz'] * 15,
        'lap_num': list(range(1, 16)) * 3,
        'lap_time_seconds': (
            [92.0 + i * 0.04 for i in range(15)] +
            [91.2 + i * 0.06 for i in range(15)] +
            [92.8 + i * 0.05 for i in range(15)]
        ),
        'pace_delta': (
            [np.nan] + [0.04] * 14 +
            [np.nan] + [0.06] * 14 +
            [np.nan] + [0.05] * 14
        ),
        'lap_position': [3] * 15 + [1] * 15 + [2] * 15,
        'degradation_rate': [0.04] * 15 + [0.06] * 15 + [0.05] * 15,
        'stint_lap': list(range(1, 16)) * 3,
    }
    df = pd.DataFrame(data)
    df['prev_lap_time'] = df.groupby('driver_id')['lap_time_seconds'].shift(1)
    return df


class TestTyreDegradationPredictor:
    """Tests for tire degradation prediction model."""

    def test_predictor_initialization(self):
        """Test predictor initializes correctly."""
        predictor = TyreDegradationPredictor(model_type='gradient_boosting')
        assert predictor.model_type == 'gradient_boosting'
        assert predictor.is_fitted is False

    def test_prepare_features(self, sample_analysis_data):
        """Test feature preparation."""
        predictor = TyreDegradationPredictor()
        X, y, df = predictor.prepare_features(sample_analysis_data)

        assert X is not None
        assert y is not None
        assert len(X) == len(y)
        assert len(X) > 0

    def test_fit_model(self, sample_analysis_data):
        """Test model fitting."""
        predictor = TyreDegradationPredictor()
        metrics = predictor.fit(sample_analysis_data)

        assert predictor.is_fitted is True
        assert 'r2_score' in metrics
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 0 <= metrics['r2_score'] <= 1

    def test_model_prediction(self, sample_analysis_data):
        """Test single lap time prediction."""
        predictor = TyreDegradationPredictor()
        predictor.fit(sample_analysis_data)

        prediction = predictor.predict_lap_time(
            driver_id='hamilton',
            lap_num=10,
            prev_lap_time=92.5,
            lap_position=2,
            pace_delta=0.05,
            stint_lap=10
        )

        assert isinstance(prediction, (float, np.floating))
        assert 80 < prediction < 120  # Reasonable lap time range

    def test_predict_race(self, sample_analysis_data):
        """Test full race prediction for driver."""
        predictor = TyreDegradationPredictor()
        predictor.fit(sample_analysis_data)

        predictions_df = predictor.predict_race(sample_analysis_data, 'hamilton')

        assert 'predicted_lap_time' in predictions_df.columns
        assert 'prediction_error' in predictions_df.columns
        assert len(predictions_df) > 0

    def test_model_not_fitted_error(self):
        """Test error when predicting with unfitted model."""
        predictor = TyreDegradationPredictor()

        with pytest.raises(ValueError):
            predictor.predict_lap_time(
                driver_id='hamilton',
                lap_num=1,
                prev_lap_time=92.5,
                lap_position=1,
                pace_delta=0,
                stint_lap=1
            )

    def test_model_types(self, sample_analysis_data):
        """Test both model types work."""
        for model_type in ['random_forest', 'gradient_boosting']:
            predictor = TyreDegradationPredictor(model_type=model_type)
            metrics = predictor.fit(sample_analysis_data)
            assert metrics['r2_score'] is not None


class TestPaceTrajectoryPredictor:
    """Tests for pace trajectory prediction."""

    def test_trajectory_init(self):
        """Test trajectory predictor initialization."""
        predictor = PaceTrajectoryPredictor()
        assert predictor.models == {}

    def test_trajectory_fit(self, sample_race_data):
        """Test trajectory model fitting."""
        predictor = PaceTrajectoryPredictor()
        metrics = predictor.fit(sample_race_data)

        assert len(metrics) > 0
        assert 'hamilton' in metrics
        assert 'r2' in metrics['hamilton']

    def test_trajectory_predict(self, sample_race_data):
        """Test trajectory prediction at specific lap."""
        predictor = PaceTrajectoryPredictor()
        predictor.fit(sample_race_data)

        prediction = predictor.predict_at_lap('hamilton', 10)

        assert prediction is not None
        assert isinstance(prediction, (float, np.floating))
        assert 80 < prediction < 120

    def test_trajectory_nonexistent_driver(self, sample_race_data):
        """Test prediction for driver not in model."""
        predictor = PaceTrajectoryPredictor()
        predictor.fit(sample_race_data)

        prediction = predictor.predict_at_lap('nonexistent', 10)

        assert prediction is None

    def test_trajectory_multiple_drivers(self, sample_race_data):
        """Test multiple drivers are modeled."""
        predictor = PaceTrajectoryPredictor()
        metrics = predictor.fit(sample_race_data)

        assert len(metrics) >= 2
        assert len(predictor.models) >= 2

    def test_trajectory_prediction_range(self, sample_race_data):
        """Test trajectory predictions are in reasonable range."""
        predictor = PaceTrajectoryPredictor()
        predictor.fit(sample_race_data)

        for driver in sample_race_data['driver_id'].unique():
            for lap in range(1, 21):
                pred = predictor.predict_at_lap(driver, lap)
                if pred is not None:
                    assert 80 < pred < 120


class TestDriverClusterer:
    """Tests for driver clustering."""

    def test_clusterer_init(self):
        """Test clusterer initialization."""
        clusterer = DriverClusterer(n_clusters=3)
        assert clusterer.n_clusters == 3

    def test_prepare_driver_features(self, sample_race_data):
        """Test feature preparation for clustering."""
        clusterer = DriverClusterer()
        feature_df, driver_ids = clusterer.prepare_driver_features(sample_race_data)

        assert len(feature_df) == len(driver_ids)
        assert len(feature_df) >= 2
        assert 'avg_lap_time' in feature_df.columns

    def test_fit_predict_clusters(self, sample_analysis_data):
        """Test clustering model fitting and prediction."""
        clusterer = DriverClusterer(n_clusters=2)
        clusters = clusterer.fit_predict(sample_analysis_data)

        assert 'driver_id' in clusters.columns
        assert 'cluster' in clusters.columns
        assert len(clusters) >= 2

    def test_cluster_assignment(self, sample_analysis_data):
        """Test that all drivers are assigned a cluster."""
        clusterer = DriverClusterer(n_clusters=3)
        clusters = clusterer.fit_predict(sample_analysis_data)

        unique_drivers = sample_analysis_data['driver_id'].nunique()
        assert len(clusters) == unique_drivers
        assert clusters['cluster'].notna().all()

    def test_cluster_range(self, sample_analysis_data):
        """Test cluster IDs are in valid range."""
        clusterer = DriverClusterer(n_clusters=3)
        clusters = clusterer.fit_predict(sample_analysis_data)

        assert clusters['cluster'].min() >= 0
        assert clusters['cluster'].max() < 3

    def test_different_cluster_counts(self, sample_analysis_data):
        """Test clustering with different numbers of clusters."""
        for n_clusters in [2, 3, 4]:
            clusterer = DriverClusterer(n_clusters=n_clusters)
            clusters = clusterer.fit_predict(sample_analysis_data)
            unique_clusters = clusters['cluster'].nunique()
            assert unique_clusters <= n_clusters


class TestModelIntegration:
    """Integration tests across all models."""

    def test_all_models_on_same_data(self, sample_analysis_data):
        """Test all models work on same dataset."""
        # Degradation predictor
        deg_pred = TyreDegradationPredictor()
        deg_metrics = deg_pred.fit(sample_analysis_data)
        assert deg_metrics['r2_score'] is not None

        # Trajectory predictor
        traj_pred = PaceTrajectoryPredictor()
        traj_metrics = traj_pred.fit(sample_analysis_data)
        assert len(traj_metrics) > 0

        # Clusterer
        clusterer = DriverClusterer(n_clusters=2)
        clusters = clusterer.fit_predict(sample_analysis_data)
        assert len(clusters) > 0

    def test_predictions_consistency(self, sample_analysis_data):
        """Test predictions are internally consistent."""
        predictor = TyreDegradationPredictor()
        predictor.fit(sample_analysis_data)

        # Make two predictions for same driver/lap and compare
        pred1 = predictor.predict_lap_time(
            driver_id='hamilton', lap_num=10, prev_lap_time=92.5,
            lap_position=2, pace_delta=0.05, stint_lap=10
        )
        pred2 = predictor.predict_lap_time(
            driver_id='hamilton', lap_num=10, prev_lap_time=92.5,
            lap_position=2, pace_delta=0.05, stint_lap=10
        )

        # Should be identical
        assert abs(pred1 - pred2) < 0.001

    def test_model_reproducibility(self, sample_analysis_data):
        """Test models give similar results on same data."""
        predictor1 = TyreDegradationPredictor(model_type='gradient_boosting')
        metrics1 = predictor1.fit(sample_analysis_data)

        predictor2 = TyreDegradationPredictor(model_type='gradient_boosting')
        metrics2 = predictor2.fit(sample_analysis_data)

        # R² should be similar (though not identical due to randomness)
        assert abs(metrics1['r2_score'] - metrics2['r2_score']) < 0.2


class TestEdgeCases:
    """Tests for edge cases in models."""

    def test_single_driver_clustering(self):
        """Test clustering with single driver."""
        data = {
            'driver_id': ['hamilton'] * 10,
            'lap_num': range(1, 11),
            'lap_time_seconds': [92.0 + i * 0.1 for i in range(10)],
            'pace_delta': [np.nan] + [0.1] * 9,
            'lap_position': [1] * 10,
            'degradation_rate': [0.1] * 10,
            'stint_lap': range(1, 11),
        }
        df = pd.DataFrame(data)

        clusterer = DriverClusterer(n_clusters=1)
        clusters = clusterer.fit_predict(df)
        assert len(clusters) >= 1

    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        data = {
            'driver_id': ['hamilton'],
            'lap_num': [1],
            'lap_time_seconds': [92.5],
            'pace_delta': [np.nan],
            'lap_position': [1],
            'degradation_rate': [0.0],
            'stint_lap': [1],
        }
        df = pd.DataFrame(data)

        predictor = TyreDegradationPredictor()
        # Should handle gracefully (may not fit well but shouldn't crash)
        try:
            metrics = predictor.fit(df)
            # R² might be very low or nan, but function completed
        except:
            pytest.fail("Model should handle single record gracefully")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
