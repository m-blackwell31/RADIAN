"""
random_forest_fall_detection.py
Unified pipeline for radar-based fall detection simulation, training, and validation.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

# -------------------------------------------------------------------
# STEP 1: DATA GENERATION (based on AWR6843ISK-style frames)
# -------------------------------------------------------------------

def generate_sequence(with_fall=False, frames=50, points_per_frame=10):
    """Simulate a sequence of radar frames with optional fall event."""
    data = []
    x, y, z = 0, 0, 1.5  # starting at standing height

    for frame in range(frames):
        # normal motion
        x += np.random.normal(0, 0.02)
        y += np.random.normal(0, 0.02)
        z += np.random.normal(0, 0.005)
        v = np.random.normal(0, 0.05)

        # fall dynamics
        if with_fall and 20 <= frame < 25:
            z -= np.random.uniform(0.2, 0.5)  # sudden drop
            v = np.random.uniform(-1.0, -0.3)
        elif with_fall and frame >= 25:
            z = 0.3 + np.random.normal(0, 0.02)  # lying down
            v = np.random.normal(0, 0.01)        # almost no motion

        for _ in range(points_per_frame):
            data.append([
                frame,
                x + np.random.normal(0, 0.02),
                y + np.random.normal(0, 0.02),
                z + np.random.normal(0, 0.02),
                v + np.random.normal(0, 0.05),
                int(with_fall)
            ])

    return pd.DataFrame(data, columns=["frame", "x", "y", "z", "v", "fall"])


# -------------------------------------------------------------------
# STEP 2: FEATURE EXTRACTION
# -------------------------------------------------------------------

def extract_features(data: pd.DataFrame):
    """Aggregate radar points per frame to compute frame-level features."""
    features = data.groupby("frame").agg({
        "x": ["mean", "std"],
        "y": ["mean", "std"],
        "z": ["mean", "std"],
        "v": ["mean", "std"]
    }).reset_index()
    labels = data.groupby("frame")["fall"].max().values
    return features.iloc[:, 1:].values, labels


# -------------------------------------------------------------------
# STEP 3: MODEL TRAINING + VALIDATION
# -------------------------------------------------------------------

def train_and_validate(model_path="trained_models/fall_detector.pkl"):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    # Generate training data
    fall_data = pd.concat([generate_sequence(with_fall=True) for _ in range(50)])
    no_fall_data = pd.concat([generate_sequence(with_fall=False) for _ in range(50)])
    data = pd.concat([fall_data, no_fall_data]).reset_index(drop=True)

    X, y = extract_features(data)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # Train Random Forest
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Validate
    y_pred = clf.predict(X_test)
    print("\n=== Validation Results ===")
    print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(clf, model_path)
    print(f"✅ Model saved to {model_path}")

    return clf


# -------------------------------------------------------------------
# STEP 4: TEST MODEL ON NEW DUMMY DATA
# -------------------------------------------------------------------

def test_new_sequence(clf, with_fall=True):
    """Run a new dummy test sequence through the trained model."""
    test_seq = generate_sequence(with_fall=with_fall, frames=60)
    X_test, _ = extract_features(test_seq)

    # Predict per frame
    preds = clf.predict(X_test)

    # Identify which frames were predicted as 'fall'
    fall_frames = np.where(preds == 1)[0]

    fall_detected = len(fall_frames) > 0
    print(f"\nFall detected? {fall_detected}")

    if fall_detected:
        print(f"🟠 Fall predicted in frames: {fall_frames.tolist()}")
    else:
        print("🟢 No fall frames detected.")

    return fall_detected, fall_frames


# -------------------------------------------------------------------
# STEP 5: MAIN EXECUTION
# -------------------------------------------------------------------

if __name__ == "__main__":
    # Train and validate model
    model = train_and_validate()

    # Test fall detection on new sequences
    test_new_sequence(model, with_fall=True)
    test_new_sequence(model, with_fall=False)
