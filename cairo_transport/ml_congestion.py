"""Machine-learning utilities for congestion prediction."""

from __future__ import annotations

import os
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    from sklearn.model_selection import train_test_split
except ImportError:  # pragma: no cover - graceful fallback when sklearn is missing
    LinearRegression = None
    mean_squared_error = None
    train_test_split = None


TIME_ENCODING = {
    "morning": 1,
    "afternoon": 2,
    "evening": 3,
    "night": 4,
}


@dataclass(frozen=True)
class CongestionModelArtifacts:
    """Store trained model and its basic evaluation details."""

    model: object
    mse: float
    sample_predictions: list[tuple[float, float]]
    dataset_origin: str
    sample_count: int


def _simulate_dataset(num_samples: int = 240, seed: int = 42) -> tuple[list[list[float]], list[float]]:
    """Create a synthetic dataset suitable for quick congestion model training."""
    rng = random.Random(seed)
    features: list[list[float]] = []
    targets: list[float] = []
    slot_multipliers = {
        1: 1.25,  # morning peak
        2: 1.0,   # afternoon
        3: 1.15,  # evening peak
        4: 0.8,   # night off-peak
    }

    for _ in range(num_samples):
        time_of_day = rng.choice((1, 2, 3, 4))
        capacity = rng.randint(500, 3000)
        distance = round(rng.uniform(0.8, 18.0), 2)
        base_flow = capacity * slot_multipliers[time_of_day]
        noise = rng.uniform(-0.12, 0.12) * capacity
        flow = max(0.0, base_flow + noise)

        congestion = flow / capacity if capacity else 0.0
        features.append([float(time_of_day), float(flow), float(capacity), distance])
        targets.append(congestion)

    return features, targets


def _load_project_dataset() -> tuple[list[list[float]], list[float]]:
    """Load training rows from the project's SQLite traffic tables."""
    db_path = Path(os.environ.get("CAIRO_TRANSPORT_DB_PATH", Path(__file__).parent / "cairo_transport.db"))
    if not db_path.exists():
        return [], []

    query = """
        SELECT t.time_slot, t.flow, r.capacity, r.distance_km
        FROM traffic_flows t
        JOIN roads r ON r.id = t.road_id
        WHERE r.capacity > 0 AND r.is_existing = 1
    """
    with sqlite3.connect(db_path) as con:
        rows = con.execute(query).fetchall()

    features: list[list[float]] = []
    targets: list[float] = []
    for time_slot, flow, capacity, distance in rows:
        encoded_time = float(TIME_ENCODING.get(str(time_slot), 2))
        flow_value = float(flow)
        capacity_value = float(capacity)
        distance_value = float(distance)
        congestion = flow_value / capacity_value if capacity_value else 0.0
        features.append([encoded_time, flow_value, capacity_value, distance_value])
        targets.append(congestion)
    return features, targets


def train_congestion_model() -> CongestionModelArtifacts | None:
    """Train and evaluate a simple linear regression congestion model."""
    if LinearRegression is None or train_test_split is None or mean_squared_error is None:
        return None

    features, targets = _load_project_dataset()
    dataset_origin = "project database"
    if len(features) < 20:
        features, targets = _simulate_dataset()
        dataset_origin = "simulated fallback"

    x_train, x_test, y_train, y_test = train_test_split(features, targets, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    mse = float(mean_squared_error(y_test, predictions))
    sample = list(zip(y_test[:10], predictions[:10]))
    return CongestionModelArtifacts(
        model=model,
        mse=mse,
        sample_predictions=sample,
        dataset_origin=dataset_origin,
        sample_count=len(features),
    )


def predict_congestion(model: object | None, time_of_day: str, flow: float, capacity: float, distance: float) -> float:
    """Predict congestion ratio using a trained model, with static fallback."""
    if capacity <= 0:
        return 0.0

    if model is None:
        return flow / capacity

    encoded_time = float(TIME_ENCODING.get(time_of_day, 2))
    raw_prediction = float(model.predict([[encoded_time, float(flow), float(capacity), float(distance)]])[0])
    return max(0.0, raw_prediction)


def run_demo() -> None:
    """Run an end-to-end demo: train, predict, evaluate, and print comparisons."""
    artifacts = train_congestion_model()
    if artifacts is None:
        print("scikit-learn is not installed. Install it with: pip install scikit-learn")
        return

    print("=== Congestion ML Demo (Linear Regression) ===")
    print(f"Training source: {artifacts.dataset_origin} ({artifacts.sample_count} rows)")
    print(f"Model Mean Squared Error: {artifacts.mse:.6f}")
    print("Actual vs Predicted congestion (sample):")
    for idx, (actual, predicted) in enumerate(artifacts.sample_predictions, start=1):
        print(f"{idx:02d}. actual={actual:.4f}, predicted={predicted:.4f}")

    # Example for routing integration weight update:
    # weight = distance * (1 + predicted_congestion)
    example_time = "morning"
    example_flow = 1800.0
    example_capacity = 1500.0
    example_distance = 6.5
    predicted = predict_congestion(
        artifacts.model,
        time_of_day=example_time,
        flow=example_flow,
        capacity=example_capacity,
        distance=example_distance,
    )
    old_weight = example_distance * (1 + (example_flow / example_capacity))
    new_weight = example_distance * (1 + predicted)

    print("\nWeight comparison for one road segment:")
    print(f"Old static weight: {old_weight:.4f}")
    print(f"New ML weight:     {new_weight:.4f}")
    print(f"Average absolute error (sample): {mean(abs(a - p) for a, p in artifacts.sample_predictions):.6f}")


if __name__ == "__main__":
    run_demo()
