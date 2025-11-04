import random
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ---------------------------------------------------------
# STEP 1: Simulate radar data sequences
# ---------------------------------------------------------

def simulate_fall_sequence(duration=10, fall_time=3):
    """
    Simulates a fall event:
    - Small motion before fall
    - Sudden large drop in position (especially z)
    - Then stillness
    """
    data = []
    x, y, z = 0, 0, 1.0  # start elevated
    for t in range(duration):
        if t < fall_time:
            # slight movement before fall
            x += random.uniform(-0.05, 0.05)
            y += random.uniform(-0.05, 0.05)
            z += random.uniform(-0.05, 0.05)
        elif t == fall_time:
            # sudden drop
            z -= random.uniform(0.8, 1.2)
            x += random.uniform(-0.2, 0.2)
            y += random.uniform(-0.2, 0.2)
        else:
            # mostly still after fall
            x += random.uniform(-0.01, 0.01)
            y += random.uniform(-0.01, 0.01)
            z += random.uniform(-0.01, 0.01)
        v = random.uniform(-0.5, 0.5) if t == fall_time else random.uniform(-0.1, 0.1)
        data.append({"time": t, "x": x, "y": y, "z": z, "v": v})
    return data, 1  # label 1 = fall


def simulate_normal_sequence(duration=10):
    """
    Simulates normal movement (no fall):
    - Smooth walking or small random motion
    - No drastic position or velocity change
    """
    data = []
    x, y, z = 0, 0, 1.0
    for t in range(duration):
        x += random.uniform(-0.1, 0.1)
        y += random.uniform(-0.1, 0.1)
        z += random.uniform(-0.05, 0.05)
        v = random.uniform(-0.2, 0.2)
        data.append({"time": t, "x": x, "y": y, "z": z, "v": v})
    return data, 0  # label 0 = normal

# ---------------------------------------------------------
# STEP 2: Feature extraction per sequence
# ---------------------------------------------------------

def extract_features(sequence):
    xs = [p["x"] for p in sequence]
    ys = [p["y"] for p in sequence]
    zs = [p["z"] for p in sequence]
    vs = [p["v"] for p in sequence]

    delta_x = xs[-1] - xs[0]
    delta_y = ys[-1] - ys[0]
    delta_z = zs[-1] - zs[0]
    total_movement = np.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
    stillness = np.mean([abs(v) < 0.05 for v in vs[-5:]])  # stillness over last ~5 frames

    features = {
        "delta_x": delta_x,
        "delta_y": delta_y,
        "delta_z": delta_z,
        "total_movement": total_movement,
        "v_mean": np.mean(vs),
        "v_max": np.max(vs),
        "v_std": np.std(vs),
        "stillness": stillness,
    }
    return features

# ---------------------------------------------------------
# STEP 3: Generate dataset
# ---------------------------------------------------------

def generate_fall_dataset(num_samples=500):
    samples = []
    for _ in range(num_samples):
        if random.random() < 0.5:
            seq, label = simulate_fall_sequence()
        else:
            seq, label = simulate_normal_sequence()
        features = extract_features(seq)
        features["label"] = label
        samples.append(features)

    df = pd.DataFrame(samples)
    df.to_csv("fall_detection_training_data.csv", index=False)
    print(f"[INFO] Generated {len(df)} labeled sequences → fall_detection_training_data.csv")
    return df

# ---------------------------------------------------------
# STEP 4: Train and validate Random Forest
# ---------------------------------------------------------

def train_fall_detector(df):
    X = df.drop(columns=["label"])
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, "fall_detector.pkl")
    print("[INFO] Model saved to fall_detector.pkl")

    y_pred = model.predict(X_test)
    print("\n=== Validation Results ===")
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    return model

# ---------------------------------------------------------
# STEP 5: Test model on new simulated data
# ---------------------------------------------------------

def test_model(model, num_tests=5):
    print("\n=== Testing on New Simulated Sequences ===")
    for i in range(num_tests):
        if random.random() < 0.5:
            seq, true_label = simulate_fall_sequence()
        else:
            seq, true_label = simulate_normal_sequence()
        features = extract_features(seq)
        X_new = pd.DataFrame([features])
        pred = model.predict(X_new)[0]
        print(f"Test #{i+1} → True: {true_label}, Predicted: {pred}")

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":
    print("[STEP 1] Generating training data...")
    df = generate_fall_dataset(num_samples=500)

    print("\n[STEP 2] Training fall detection model...")
    model = train_fall_detector(df)

    print("\n[STEP 3] Testing fall detection model...")
    test_model(model)
