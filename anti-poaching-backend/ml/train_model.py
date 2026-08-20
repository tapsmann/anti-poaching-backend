import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os
import random

def generate_training_data(n_samples=10000):
    """Generate synthetic training data for demo"""
    data = []
    
    for _ in range(n_samples):
        # Features
        hour = np.random.randint(0, 24)
        day_of_week = np.random.randint(0, 7)
        month = np.random.randint(1, 13)
        moon_illumination = np.random.random()
        distance_to_road = np.random.uniform(0, 10)
        distance_to_river = np.random.uniform(0, 15)
        poaching_density = np.random.randint(0, 10)
        patrol_frequency = np.random.randint(0, 20)
        
        # Generate label (poached or not)
        risk_score = (
            0.3 * (1 if hour >= 20 or hour <= 4 else 0) +
            0.2 * (1 if distance_to_road < 2 else 0) +
            0.2 * (1 if moon_illumination < 0.3 else 0) +
            0.2 * (1 if poaching_density > 5 else 0) +
            -0.3 * (1 if patrol_frequency > 10 else 0)
        )
        
        risk_score += np.random.normal(0, 0.1)
        poached = 1 if risk_score > 0.5 else 0
        
        data.append([
            hour, day_of_week, month, moon_illumination,
            distance_to_road, distance_to_river,
            poaching_density, patrol_frequency, poached
        ])
    
    columns = [
        "hour", "day_of_week", "month", "moon_illumination",
        "distance_to_road", "distance_to_river",
        "poaching_density", "patrol_frequency", "poached"
    ]
    
    return pd.DataFrame(data, columns=columns)

def train_model():
    print("Generating training data...")
    df = generate_training_data(10000)
    
    X = df.drop("poached", axis=1)
    y = df["poached"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    
    accuracy = model.score(X_test_scaled, y_test)
    print(f"Model accuracy: {accuracy:.2f}")
    
    feature_importance = dict(zip(X.columns, model.feature_importances_))
    print("\nTop 5 features:")
    for feature, importance in sorted(
        feature_importance.items(), key=lambda x: -x[1]
    )[:5]:
        print(f"  {feature}: {importance:.3f}")
    
    # Create models directory
    os.makedirs("ml/models", exist_ok=True)
    
    with open("ml/models/poaching_risk.pkl", "wb") as f:
        pickle.dump(model, f)
    print("\n✅ Model saved to 'ml/models/poaching_risk.pkl'")
    
    with open("ml/models/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print("✅ Scaler saved to 'ml/models/scaler.pkl'")

if __name__ == "__main__":
    train_model()