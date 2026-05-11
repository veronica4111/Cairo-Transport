"""Standalone script: train an ML model and use predicted congestion for weight."""

from __future__ import annotations

from cairo_transport.ml_congestion import predict_congestion, train_congestion_model


def main() -> None:
    # Step 1-4: build dataset from project traffic DB and train model.
    artifacts = train_congestion_model()
    if artifacts is None:
        print("scikit-learn is not installed. Install it with: pip install scikit-learn")
        return

    print("=== Congestion Prediction using Linear Regression ===")
    print(f"Training source: {artifacts.dataset_origin} ({artifacts.sample_count} rows)")
    print(f"Mean Squared Error: {artifacts.mse:.6f}\n")

    # Step 5: show model predictions.
    print("Sample Actual vs Predicted Congestion:")
    for i, (actual, predicted) in enumerate(artifacts.sample_predictions[:10], start=1):
        print(f"{i:02d}. actual={actual:.4f}, predicted={predicted:.4f}")

    # Step 6: Replace static weight with ML-based weight.
    time_of_day = "morning"
    flow = 1800.0
    capacity = 1500.0
    distance = 6.5

    predicted_congestion = predict_congestion(
        artifacts.model,
        time_of_day=time_of_day,
        flow=flow,
        capacity=capacity,
        distance=distance,
    )

    old_weight = distance * (1 + flow / capacity)
    new_weight = distance * (1 + predicted_congestion)

    print("\nWeight Formula Comparison:")
    print(f"Old formula  -> weight = distance * (1 + flow / capacity)      = {old_weight:.4f}")
    print(f"New formula  -> weight = distance * (1 + predicted_congestion) = {new_weight:.4f}")


if __name__ == "__main__":
    main()
