"""
XGBoost Premium Model Training Script for Nexurance AI
Trains on synthetic data with 8 features for premium prediction.
"""
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split

def generate_synthetic_data(n_samples=5000):
    """Generate synthetic training data for premium model."""
    np.random.seed(42)
    zone_flood_risk = np.random.uniform(0.5, 1.5, n_samples)
    rainfall_forecast = np.random.uniform(0, 100, n_samples)
    aqi_forecast = np.random.uniform(30, 500, n_samples)
    day_of_week = np.random.randint(0, 7, n_samples)
    worker_active_days = np.random.randint(1, 90, n_samples)
    zone_claim_frequency = np.random.uniform(0, 5, n_samples)
    monsoon_indicator = np.random.choice([0, 1], n_samples, p=[0.6, 0.4])
    trust_score = np.random.uniform(0.3, 1.0, n_samples)

    X = np.column_stack([
        zone_flood_risk, rainfall_forecast, aqi_forecast, day_of_week,
        worker_active_days, zone_claim_frequency, monsoon_indicator, trust_score
    ])

    # Premium = base * risk factors
    base = 20
    premium = (base * zone_flood_risk *
               (1 + rainfall_forecast / 125) *
               (1 - (trust_score - 0.5) * 0.3) *
               (1 + monsoon_indicator * 0.2) +
               np.random.normal(0, 2, n_samples))
    premium = np.clip(premium, 10, 80)
    return X, premium

def train_model():
    """Train and save XGBoost premium model."""
    print("📊 Generating synthetic training data...")
    X, y = generate_synthetic_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    try:
        from xgboost import XGBRegressor
        print("🤖 Training XGBoost model...")
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1,
                             random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        print(f"✅ Model R² score: {score:.4f}")
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        print("🤖 Training GradientBoosting model (XGBoost fallback)...")
        model = GradientBoostingRegressor(n_estimators=100, max_depth=5,
                                          learning_rate=0.1, random_state=42)
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        print(f"✅ Model R² score: {score:.4f}")

    model_path = os.path.join(os.path.dirname(__file__), 'premium_model.pkl')
    joblib.dump(model, model_path)
    print(f"💾 Model saved to {model_path}")

    # Feature importance
    features = ['zone_flood_risk', 'rainfall_forecast', 'aqi_forecast', 'day_of_week',
                'worker_active_days', 'zone_claim_frequency', 'monsoon_indicator', 'trust_score']
    if hasattr(model, 'feature_importances_'):
        importances = sorted(zip(features, model.feature_importances_), key=lambda x: x[1], reverse=True)
        print("\n📈 Feature Importance:")
        for feat, imp in importances:
            print(f"  {feat:25s} {imp:.4f}")

    return model

if __name__ == '__main__':
    train_model()
