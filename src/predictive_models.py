"""
Predictive models for F1 Rhythm Analysis.

Models for:
- Tire degradation prediction
- Pace trajectory forecasting
- Driver clustering and classification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import logging

logger = logging.getLogger(__name__)


class TyreDegradationPredictor:
    """
    Predicts tire degradation using machine learning.

    Features:
    - Lap number
    - Previous lap time
    - Driver characteristics
    - Environmental factors
    """

    def __init__(self, model_type: str = "gradient_boosting"):
        """
        Initialize predictor.

        Args:
            model_type: 'random_forest' or 'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.driver_encoder = LabelEncoder()
        self.is_fitted = False

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for model training.

        Features:
        - lap_num: Lap number in race
        - prev_lap_time: Previous lap time
        - lap_position: Position on lap
        - pace_delta: Pace change from previous lap
        - stint_lap: Laps into current stint

        Args:
            df: DataFrame with columns ['driver_id', 'lap_num', 'lap_time_seconds', 'pace_delta']

        Returns:
            (X, y) feature matrix and target variable
        """
        df = df.sort_values(['driver_id', 'lap_num']).reset_index(drop=True)

        # Calculate stint lap (laps since start or tire change)
        df['stint_lap'] = df.groupby('driver_id').cumcount() + 1

        # Previous lap time (within same driver)
        df['prev_lap_time'] = df.groupby('driver_id')['lap_time_seconds'].shift(1)

        # Features for training
        feature_cols = [
            'lap_num',
            'prev_lap_time',
            'lap_position',
            'pace_delta',
            'stint_lap'
        ]

        # Handle missing values
        df = df.dropna(subset=feature_cols + ['lap_time_seconds'])

        X = df[feature_cols].copy()
        y = df['lap_time_seconds'].copy()

        return X, y, df

    def fit(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Fit degradation model on training data.

        Args:
            df: Full race DataFrame with lap data

        Returns:
            Dict with training metrics (R2, MAE, RMSE)
        """
        X, y, _ = self.prepare_features(df)

        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        else:  # gradient_boosting
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        # Evaluate
        y_pred = self.model.predict(X_scaled)

        metrics = {
            'r2_score': r2_score(y, y_pred),
            'mae': mean_absolute_error(y, y_pred),
            'rmse': np.sqrt(mean_squared_error(y, y_pred))
        }

        logger.info(f"Degradation model fitted. R²={metrics['r2_score']:.3f}, RMSE={metrics['rmse']:.3f}")

        return metrics

    def predict_lap_time(self, driver_id: str, lap_num: int,
                        prev_lap_time: float, lap_position: int,
                        pace_delta: float, stint_lap: int) -> float:
        """
        Predict lap time for a driver at a specific lap.

        Args:
            driver_id: Driver identifier
            lap_num: Lap number in race
            prev_lap_time: Previous lap time (seconds)
            lap_position: Driver position on this lap
            pace_delta: Pace change from previous lap (seconds)
            stint_lap: Laps into current stint

        Returns:
            Predicted lap time in seconds
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        features = np.array([
            [lap_num, prev_lap_time, lap_position, pace_delta, stint_lap]
        ])

        features_scaled = self.scaler.transform(features)
        prediction = self.model.predict(features_scaled)[0]

        return prediction

    def predict_race(self, df: pd.DataFrame, driver_id: str) -> pd.DataFrame:
        """
        Predict lap times for entire race for a driver.

        Args:
            df: Race DataFrame
            driver_id: Driver to predict for

        Returns:
            DataFrame with actual and predicted lap times
        """
        driver_data = df[df['driver_id'] == driver_id].sort_values('lap_num')

        predictions = []
        for idx, row in driver_data.iterrows():
            try:
                pred = self.predict_lap_time(
                    driver_id=driver_id,
                    lap_num=row['lap_num'],
                    prev_lap_time=row.get('prev_lap_time', row['lap_time_seconds']),
                    lap_position=row['lap_position'],
                    pace_delta=row.get('pace_delta', 0),
                    stint_lap=row.get('stint_lap', row['lap_num'])
                )
                predictions.append(pred)
            except:
                predictions.append(np.nan)

        driver_data = driver_data.copy()
        driver_data['predicted_lap_time'] = predictions
        driver_data['prediction_error'] = driver_data['lap_time_seconds'] - driver_data['predicted_lap_time']

        return driver_data


class PaceTrajectoryPredictor:
    """
    Predicts pace trajectory evolution during a race.

    Models how a driver's pace changes (improves/degrades) over lap number.
    """

    def __init__(self):
        self.models = {}  # One model per driver
        self.scaler = StandardScaler()

    def fit(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Fit trajectory models for all drivers.

        Args:
            df: Race DataFrame

        Returns:
            Dict with metrics for each driver
        """
        results = {}

        for driver_id in df['driver_id'].unique():
            driver_data = df[df['driver_id'] == driver_id].sort_values('lap_num')

            if len(driver_data) < 3:
                continue

            X = driver_data[['lap_num']].values
            y = driver_data['lap_time_seconds'].values

            model = GradientBoostingRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )

            model.fit(X, y)
            self.models[driver_id] = model

            # Metrics
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)

            results[driver_id] = {
                'r2': r2,
                'mae': mae,
                'laps': len(driver_data)
            }

        logger.info(f"Trajectory models fitted for {len(self.models)} drivers")
        return results

    def predict_at_lap(self, driver_id: str, lap_num: int) -> Optional[float]:
        """
        Predict pace at specific lap number.

        Args:
            driver_id: Driver identifier
            lap_num: Lap number to predict for

        Returns:
            Predicted lap time or None if driver not in model
        """
        if driver_id not in self.models:
            return None

        model = self.models[driver_id]
        prediction = model.predict([[lap_num]])[0]
        return prediction


class DriverClusterer:
    """
    Clusters drivers based on performance characteristics.

    Identifies groups of drivers with similar:
    - Pace
    - Consistency
    - Degradation patterns
    """

    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42)
        self.scaler = StandardScaler()
        self.cluster_labels = None

    def prepare_driver_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extract driver-level features for clustering.

        Features:
        - avg_lap_time: Average pace
        - std_lap_time: Consistency
        - degradation_rate: Tire wear rate
        - best_lap_improvement: Best vs average

        Args:
            df: Race DataFrame

        Returns:
            (Feature DataFrame, driver ID list)
        """
        driver_stats = []
        driver_ids = []

        for driver_id in df['driver_id'].unique():
            driver_data = df[df['driver_id'] == driver_id]

            stats = {
                'avg_lap_time': driver_data['lap_time_seconds'].mean(),
                'std_lap_time': driver_data['lap_time_seconds'].std(),
                'degradation_rate': driver_data.get('degradation_rate', 0).mean(),
                'best_lap_improvement': (
                    (driver_data['lap_time_seconds'].mean() -
                     driver_data['lap_time_seconds'].min()) /
                    driver_data['lap_time_seconds'].min() * 100
                ) if driver_data['lap_time_seconds'].min() > 0 else 0
            }

            driver_stats.append(stats)
            driver_ids.append(driver_id)

        feature_df = pd.DataFrame(driver_stats, index=driver_ids)
        return feature_df, driver_ids

    def fit_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit clustering model and assign drivers to clusters.

        Args:
            df: Race DataFrame

        Returns:
            DataFrame with driver_id and cluster assignment
        """
        feature_df, driver_ids = self.prepare_driver_features(df)

        # Scale features
        features_scaled = self.scaler.fit_transform(feature_df)

        # Fit and predict
        clusters = self.model.fit_predict(features_scaled)

        # Create result
        result = pd.DataFrame({
            'driver_id': driver_ids,
            'cluster': clusters
        })

        logger.info(f"Clustered {len(driver_ids)} drivers into {self.n_clusters} groups")

        return result


# Convenience function for complete analysis
def analyze_predictive_models(df: pd.DataFrame, test_size: float = 0.2) -> Dict:
    """
    Run complete predictive analysis on race data.

    Args:
        df: Full race DataFrame
        test_size: Fraction of data for testing

    Returns:
        Dict with all model results
    """
    results = {}

    # 1. Degradation predictor
    logger.info("Training degradation predictor...")
    degradation = TyreDegradationPredictor()
    deg_metrics = degradation.fit(df)
    results['degradation_metrics'] = deg_metrics

    # 2. Trajectory predictor
    logger.info("Training trajectory predictors...")
    trajectory = PaceTrajectoryPredictor()
    traj_metrics = trajectory.fit(df)
    results['trajectory_metrics'] = traj_metrics

    # 3. Driver clustering
    logger.info("Clustering drivers...")
    clusterer = DriverClusterer(n_clusters=3)
    clusters = clusterer.fit_predict(df)
    results['clusters'] = clusters

    return results


if __name__ == "__main__":
    # Example usage
    from src.data_fetcher import get_fetcher
    from src.etl_pipeline import Pipeline

    fetcher = get_fetcher(use_mock=True)
    season_data = fetcher.fetch_season(2024)

    if season_data:
        pipeline = Pipeline()
        race = season_data["races"][0]

        laps_data = fetcher.fetch_race_laps(2024, int(race["round"]))
        race.update(laps_data or {})

        df = pipeline.process_race(2024, int(race["round"]), race)

        if df is not None:
            print("\n" + "=" * 60)
            print("PREDICTIVE MODELS DEMO".center(60))
            print("=" * 60)

            results = analyze_predictive_models(df)

            print(f"\nDegradation Model:")
            print(f"  R² Score: {results['degradation_metrics']['r2_score']:.3f}")
            print(f"  RMSE: {results['degradation_metrics']['rmse']:.3f}s")

            print(f"\nDriver Clusters:")
            print(results['clusters'].to_string(index=False))
