import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os


def generate_training_data(n_samples=15000):
    """Generate synthetic training data based on Zimbabwe geography and poaching patterns."""
    rng = np.random.default_rng(2026)
    data = []

    ZIM_PARKS = [
        (-18.56, 26.49, 0.7), (-21.73, 31.55, 0.65), (-15.75, 29.38, 0.6),
        (-20.55, 28.51, 0.45), (-17.93, 25.85, 0.35), (-17.93, 27.87, 0.7),
        (-16.92, 28.47, 0.6), (-18.18, 27.40, 0.5), (-17.88, 30.55, 0.25),
        (-16.52, 28.85, 0.4),
    ]

    for _ in range(n_samples):
        hour = rng.integers(0, 24)
        day_of_week = rng.integers(0, 7)
        month = rng.integers(1, 13)
        moon_illumination = rng.random()

        park = ZIM_PARKS[rng.integers(len(ZIM_PARKS))]
        lat = park[0] + rng.uniform(-0.3, 0.3)
        lng = park[1] + rng.uniform(-0.3, 0.3)
        park_risk = park[2]

        distance_to_road = rng.uniform(0, 10)
        distance_to_river = rng.uniform(0, 15)
        distance_to_park = rng.uniform(0, 20)

        if distance_to_park < 5:
            poaching_density = int(rng.integers(5, 10))
        elif distance_to_park < 15:
            poaching_density = int(rng.integers(1, 6))
        else:
            poaching_density = int(rng.integers(0, 3))

        patrol_frequency = int(max(0, min(20, 20 - distance_to_park * 0.8 + rng.normal(0, 3))))

        time_risk = 1.4 if (hour >= 20 or hour <= 4) else (1.1 if 5 <= hour <= 6 or 17 <= hour <= 19 else 0.7)
        seasonal_risk = 1.3 if month in {5, 6, 7, 8, 9, 10} else 0.8

        risk_score = (
            0.25 * park_risk
            + 0.20 * (1 if distance_to_road < 2 else 0.3)
            + 0.15 * (1 if moon_illumination < 0.3 else 0.2)
            + 0.15 * (poaching_density / 10)
            + 0.10 * time_risk
            + 0.10 * seasonal_risk
            + 0.05 * (1 - patrol_frequency / 20)
            - 0.15 * (distance_to_park / 20)
        )
        risk_score += rng.normal(0, 0.08)
        poached = 1 if risk_score > 0.5 else 0

        data.append([
            hour, day_of_week, month, moon_illumination,
            distance_to_road, distance_to_river, distance_to_park,
            park_risk, time_risk, seasonal_risk,
            poaching_density, patrol_frequency, poached
        ])

    columns = [
        "hour", "day_of_week", "month", "moon_illumination",
        "distance_to_road", "distance_to_river", "distance_to_park",
        "park_risk_base", "time_risk", "seasonal_risk",
        "poaching_density", "patrol_frequency", "poached"
    ]

    return pd.DataFrame(data, columns=columns)


def train_model():
    print("Generating Zimbabwe-based training data...")
    df = generate_training_data(15000)

    X = df.drop("poached", axis=1)
    y = df["poached"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    accuracy = model.score(X_test_scaled, y_test)
    print(f"Model accuracy: {accuracy:.2%}")

    feature_importance = dict(zip(X.columns, model.feature_importances_))
    print("\nTop features:")
    for feature, importance in sorted(feature_importance.items(), key=lambda x: -x[1])[:8]:
        print(f"  {feature}: {importance:.3f}")

    os.makedirs("ml/models", exist_ok=True)

    with open("ml/models/poaching_risk.pkl", "wb") as f:
        pickle.dump(model, f)
    print(f"\nModel saved to ml/models/poaching_risk.pkl")

    with open("ml/models/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print("Scaler saved to ml/models/scaler.pkl")


if __name__ == "__main__":
    train_model()
