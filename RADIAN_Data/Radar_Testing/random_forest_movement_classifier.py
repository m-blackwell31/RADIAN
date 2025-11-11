import json
import random
import time
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ---------------------------------------------------------
# STEP 1: Generate radar-like dummy data
# ---------------------------------------------------------

def generate_radar_training_data(num_frames=200, max_points=5):
    """
    Creates dummy radar-like data with x, y, z, v per point
    and a simple binary label based on velocity.
    """
    data = []
    for frame in range(num_frames):
        num_points = random.randint(1, max_points)
        for _ in range(num_points):
            x = random.uniform(-2, 2)
            y = random.uniform(-2, 2)
            z = random.uniform(-0.5, 1.5)
            v = random.uniform(-1, 1)

            # Label rule: moving if |v| > 0.4, else static
            label = 1 if abs(v) > 0.4 else 0

            data.append({
                "frame": frame,
                "x": x,
                "y": y,
                "z": z,
                "v": v,
                "label": label
            })

    df = pd.DataFrame(data)
    df.to_csv("radar_movement_training_data.csv", index=False)
    print(f"[INFO] Saved {len(df)} data points to radar_training_data.csv")
    return df

# ---------------------------------------------------------
# STEP 2: Train the Random Forest model
# ---------------------------------------------------------

def train_random_forest(df):
    """
    Trains and validates a Random Forest classifier
    on radar-like dummy data.
    """
    X = df[["x", "y", "z", "v"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, "radar_random_forest.pkl")
    print("[INFO] Model saved to radar_random_forest.pkl")

    y_pred = model.predict(X_test)
    print("\n=== Validation Results ===")
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    return model

# ---------------------------------------------------------
# STEP 3: Test model with new dummy radar frames
# ---------------------------------------------------------

def generate_dummy_frame_points(num_points=3):
    """
    Creates a single dummy radar frame with N random points.
    """
    frame = []
    for _ in range(num_points):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        z = random.uniform(-0.5, 1.5)
        v = random.uniform(-1, 1)
        frame.append({"x": x, "y": y, "z": z, "v": v})
    return frame

def test_with_new_dummy_data(model, num_frames=5):
    """
    Simulates testing the trained model with fresh dummy radar frames.
    """
    print("\n=== Testing with New Dummy Data ===")
    for i in range(num_frames):
        dummy_frame = generate_dummy_frame_points(random.randint(1, 5))
        df_new = pd.DataFrame(dummy_frame)
        predictions = model.predict(df_new)
        df_new["predicted_label"] = predictions
        print(f"\n[FRAME {i}]")
        print(df_new)

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":
    print("[STEP 1] Generating training data...")
    df = generate_radar_training_data(num_frames=300)

    print("\n[STEP 2] Training Random Forest...")
    model = train_random_forest(df)

    print("\n[STEP 3] Testing with simulated radar frames...")
    test_with_new_dummy_data(model)
