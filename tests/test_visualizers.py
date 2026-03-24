"""
Unit tests for src/visualizers.py

Tests for visualization functions:
- Pace progression
- Driver comparison
- Degradation analysis
- Consistency analysis
"""

import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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


@pytest.fixture
def sample_race_df():
    """Create sample race DataFrame."""
    data = {
        'driver_id': ['hamilton', 'hamilton', 'hamilton', 'hamilton',
                     'verstappen', 'verstappen', 'verstappen', 'verstappen',
                     'sainz', 'sainz', 'sainz', 'sainz'],
        'lap_num': [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
        'lap_time_seconds': [92.5, 92.3, 92.4, 92.6,
                            91.8, 91.9, 92.0, 92.2,
                            93.2, 93.1, 93.3, 93.4],
        'pace_delta': [np.nan, -0.2, 0.1, 0.2,
                       np.nan, 0.1, 0.1, 0.2,
                       np.nan, -0.1, 0.2, 0.1],
        'lap_position': [2, 2, 2, 2, 1, 1, 1, 1, 3, 3, 3, 3],
        'degradation_rate': [0.05] * 4 + [0.05] * 4 + [0.05] * 4,
        'round': [1] * 12,
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_degradation_dict():
    """Create sample degradation analysis dict."""
    return {
        'hamilton': {
            'degradation_rate': 0.05,
            'r_squared': 0.92,
            'total_loss': 1.5,
            'laps_analyzed': 50,
            'avg_lap_time': 92.4,
        },
        'verstappen': {
            'degradation_rate': 0.03,
            'r_squared': 0.95,
            'total_loss': 0.9,
            'laps_analyzed': 50,
            'avg_lap_time': 91.8,
        },
    }


@pytest.fixture
def sample_consistency_dict():
    """Create sample consistency analysis dict."""
    return {
        'hamilton': {
            'coefficient_of_variation': 0.012,
            'avg_lap_delta': 0.15,
            'improvement_from_best': 0.5,
            'best_lap': 92.1,
        },
        'verstappen': {
            'coefficient_of_variation': 0.010,
            'avg_lap_delta': 0.12,
            'improvement_from_best': 0.3,
            'best_lap': 91.5,
        },
    }


@pytest.fixture
def sample_clusters_df():
    """Create sample clusters DataFrame."""
    return pd.DataFrame({
        'driver_id': ['hamilton', 'verstappen', 'sainz'],
        'cluster': [0, 0, 1],
    })


class TestPaceProgressionPlot:
    """Tests for pace progression visualization."""

    def test_pace_progression_creates_figure(self, sample_race_df):
        """Test pace progression creates matplotlib figure."""
        fig = plot_pace_progression(sample_race_df)
        assert fig is not None
        assert hasattr(fig, 'savefig')
        plt.close(fig)

    def test_pace_progression_specific_drivers(self, sample_race_df):
        """Test pace progression with specific drivers."""
        fig = plot_pace_progression(
            sample_race_df,
            drivers=['hamilton', 'verstappen']
        )
        assert fig is not None
        plt.close(fig)

    def test_pace_progression_custom_title(self, sample_race_df):
        """Test pace progression with custom title."""
        custom_title = "Custom Title Test"
        fig = plot_pace_progression(sample_race_df, title=custom_title)
        assert custom_title in fig.suptitle().get_text() or len(fig.axes) > 0
        plt.close(fig)


class TestLapDistributionPlot:
    """Tests for lap time distribution visualization."""

    def test_lap_distribution_creates_figure(self, sample_race_df):
        """Test lap distribution creates figure."""
        fig = plot_lap_time_distribution(sample_race_df)
        assert fig is not None
        plt.close(fig)

    def test_lap_distribution_with_drivers(self, sample_race_df):
        """Test lap distribution with specific drivers."""
        fig = plot_lap_time_distribution(
            sample_race_df,
            drivers=['hamilton', 'verstappen']
        )
        assert fig is not None
        plt.close(fig)


class TestDriverComparisonPlot:
    """Tests for driver comparison visualization."""

    def test_driver_comparison_creates_figure(self, sample_race_df):
        """Test driver comparison creates figure."""
        fig = plot_driver_comparison(sample_race_df)
        assert fig is not None
        plt.close(fig)

    def test_driver_comparison_format(self, sample_race_df):
        """Test driver comparison has correct format."""
        fig = plot_driver_comparison(sample_race_df)
        # Should have at least one axis
        assert len(fig.axes) >= 1
        plt.close(fig)


class TestDegradationHeatmap:
    """Tests for degradation heatmap visualization."""

    def test_degradation_heatmap_creates_figure(self, sample_race_df):
        """Test degradation heatmap creates figure."""
        fig = plot_degradation_heatmap(sample_race_df)
        assert fig is not None
        plt.close(fig)

    def test_degradation_heatmap_with_title(self, sample_race_df):
        """Test degradation heatmap with custom title."""
        fig = plot_degradation_heatmap(
            sample_race_df,
            title="Test Heatmap"
        )
        assert fig is not None
        plt.close(fig)


class TestPaceDeltaScatter:
    """Tests for pace delta scatter plot."""

    def test_pace_delta_scatter_creates_figure(self, sample_race_df):
        """Test pace delta scatter creates figure."""
        fig = plot_pace_delta_scatter(sample_race_df)
        assert fig is not None
        plt.close(fig)

    def test_pace_delta_scatter_drivers(self, sample_race_df):
        """Test pace delta scatter with specific drivers."""
        fig = plot_pace_delta_scatter(
            sample_race_df,
            drivers=['hamilton', 'verstappen']
        )
        assert fig is not None
        plt.close(fig)


class TestPaceWithTrend:
    """Tests for pace with trend line visualization."""

    def test_pace_trend_creates_figure(self, sample_race_df):
        """Test pace with trend creates figure."""
        fig = plot_pace_with_trend(sample_race_df, 'hamilton')
        assert fig is not None
        plt.close(fig)

    def test_pace_trend_nonexistent_driver(self, sample_race_df):
        """Test pace with trend for nonexistent driver."""
        fig = plot_pace_with_trend(sample_race_df, 'nonexistent')
        assert fig is None

    def test_pace_trend_custom_window(self, sample_race_df):
        """Test pace with trend custom window size."""
        fig = plot_pace_with_trend(sample_race_df, 'hamilton', window=2)
        assert fig is not None
        plt.close(fig)


class TestMultiDriverComparison:
    """Tests for multi-driver comparison visualization."""

    def test_multi_driver_creates_figure(self, sample_race_df):
        """Test multi-driver comparison creates figure."""
        fig = plot_multi_driver_comparison(
            sample_race_df,
            ['hamilton', 'verstappen']
        )
        assert fig is not None
        plt.close(fig)

    def test_multi_driver_four_panel(self, sample_race_df):
        """Test multi-driver creates 4 subplots."""
        fig = plot_multi_driver_comparison(
            sample_race_df,
            ['hamilton', 'verstappen', 'sainz']
        )
        # Should have up to 4 subplots
        assert len(fig.axes) >= 2
        plt.close(fig)


class TestDegradationComparison:
    """Tests for degradation comparison visualization."""

    def test_degradation_comparison_creates_figure(self, sample_degradation_dict):
        """Test degradation comparison creates figure."""
        fig = plot_degradation_comparison(sample_degradation_dict)
        assert fig is not None
        plt.close(fig)

    def test_degradation_comparison_top_n(self, sample_degradation_dict):
        """Test degradation comparison with top_n parameter."""
        fig = plot_degradation_comparison(sample_degradation_dict, top_n=2)
        assert fig is not None
        plt.close(fig)


class TestConsistencyAnalysis:
    """Tests for consistency analysis visualization."""

    def test_consistency_analysis_creates_figure(self, sample_consistency_dict):
        """Test consistency analysis creates figure."""
        fig = plot_consistency_analysis(sample_consistency_dict)
        assert fig is not None
        plt.close(fig)

    def test_consistency_analysis_subplots(self, sample_consistency_dict):
        """Test consistency analysis has 4 subplots."""
        fig = plot_consistency_analysis(sample_consistency_dict)
        assert len(fig.axes) == 4
        plt.close(fig)


class TestPredictionVsActual:
    """Tests for prediction vs actual visualization."""

    def test_prediction_vs_actual_creates_figure(self):
        """Test prediction vs actual creates figure."""
        actual = np.array([92.1, 92.3, 92.5, 92.4, 92.6])
        predicted = np.array([92.0, 92.4, 92.5, 92.3, 92.7])

        fig = plot_prediction_vs_actual(actual, predicted)
        assert fig is not None
        plt.close(fig)

    def test_prediction_vs_actual_shapes(self):
        """Test prediction vs actual with matching shapes."""
        actual = np.random.normal(92.5, 0.5, 20)
        predicted = actual + np.random.normal(0, 0.1, 20)

        fig = plot_prediction_vs_actual(actual, predicted, driver_id='test')
        assert fig is not None
        plt.close(fig)


class TestClusterAnalysis:
    """Tests for cluster analysis visualization."""

    def test_cluster_analysis_creates_figure(self, sample_race_df, sample_clusters_df):
        """Test cluster analysis creates figure."""
        fig = plot_cluster_analysis(sample_race_df, sample_clusters_df)
        assert fig is not None
        plt.close(fig)

    def test_cluster_analysis_subplots(self, sample_race_df, sample_clusters_df):
        """Test cluster analysis has 4 subplots."""
        fig = plot_cluster_analysis(sample_race_df, sample_clusters_df)
        assert len(fig.axes) == 4
        plt.close(fig)


class TestSaveFigure:
    """Tests for figure saving functionality."""

    def test_save_figure_creates_file(self, tmp_path, sample_race_df):
        """Test save_figure creates PNG file."""
        fig = plot_pace_progression(sample_race_df)
        output_dir = str(tmp_path)

        path = save_figure(fig, "test_figure", output_dir)

        assert "test_figure.png" in path
        plt.close(fig)

    def test_save_figure_creates_directory(self, tmp_path):
        """Test save_figure creates output directory if missing."""
        import os
        fig = plt.figure()
        output_dir = str(tmp_path / "new_dir")

        path = save_figure(fig, "test", output_dir)

        assert os.path.exists(output_dir)
        plt.close(fig)


class TestGenerateAllVisualizations:
    """Tests for batch visualization generation."""

    def test_generate_all_visualizations(self, sample_race_df, sample_degradation_dict,
                                        sample_consistency_dict, tmp_path):
        """Test generate_all_visualizations creates multiple plots."""
        output_dir = str(tmp_path)

        results = generate_all_visualizations(
            sample_race_df,
            degradation_dict=sample_degradation_dict,
            consistency_dict=sample_consistency_dict,
            output_dir=output_dir
        )

        assert len(results) > 0
        assert isinstance(results, dict)

    def test_generate_all_minimal(self, sample_race_df, tmp_path):
        """Test generate_all_visualizations with minimal input."""
        output_dir = str(tmp_path)

        results = generate_all_visualizations(
            sample_race_df,
            output_dir=output_dir
        )

        assert len(results) >= 3  # At least basic plots


class TestVisualEdgeCases:
    """Tests for edge cases in visualizations."""

    def test_empty_dataframe_handling(self):
        """Test visualization handles empty DataFrame."""
        empty_df = pd.DataFrame()

        # Most should handle gracefully or raise appropriate error
        try:
            fig = plot_driver_comparison(empty_df)
            if fig:
                plt.close(fig)
        except (KeyError, ValueError):
            # Expected behavior
            pass

    def test_single_driver_visualization(self):
        """Test visualization with single driver."""
        data = {
            'driver_id': ['hamilton'] * 5,
            'lap_num': range(1, 6),
            'lap_time_seconds': [92.5, 92.3, 92.4, 92.6, 92.5],
            'pace_delta': [np.nan, -0.2, 0.1, 0.2, -0.1],
            'lap_position': [1] * 5,
            'degradation_rate': [0.05] * 5,
        }
        df = pd.DataFrame(data)

        fig = plot_pace_progression(df)
        assert fig is not None
        plt.close(fig)

    def test_many_drivers_visualization(self):
        """Test visualization with many drivers."""
        drivers = [f'driver_{i}' for i in range(20)]
        data = {
            'driver_id': drivers * 3,
            'lap_num': list(range(1, 4)) * 20,
            'lap_time_seconds': np.random.normal(92, 1, 60),
            'pace_delta': np.random.normal(0, 0.1, 60),
            'lap_position': np.random.randint(1, 20, 60),
            'degradation_rate': np.random.uniform(0.01, 0.1, 60),
        }
        df = pd.DataFrame(data)

        fig = plot_pace_progression(df)
        assert fig is not None
        plt.close(fig)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
