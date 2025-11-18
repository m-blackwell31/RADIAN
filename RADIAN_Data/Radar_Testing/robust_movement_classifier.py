import json
import random
import time
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ---------------------------------------------------------
# STEP 1: Generate radar-like dummy data (REALISTIC)
# ---------------------------------------------------------

def add_noise(value, sigma=0.05):
    """Gaussian noise to simulate radar measurement noise."""
    return value + random.gauss(0, sigma)

def generate_cluster_center():
    """Returns the center of a body-reflection cluster."""
    return (
        random.uniform(-1.2, 1.2),
        random.uniform(-1.2, 1.2),
        random.uniform(0.1, 1.6)
    )

def generate_radar_training_data(num_frames=200, max_clusters=3):
    """
    Creates realistic radar-like data with:
      - noise & jitter
      - slow drift
      - multi-point Doppler clusters
      - nonlinear movement patterns
      - ambiguous cases
      - label noise
    Resulting accuracy should be around 85–95%.
    """
    data = []

    # Long-term drift (slow body lean or sway)
    drift_x = random.uniform(-0.3, 0.3)
    drift_y = random.uniform(-0.3, 0.3)
    drift_z = random.uniform(-0.2, 0.2)

    prev_z = None
    prev_v = None

    for frame in range(num_frames):

        # Frame-level jitter (radar noise floor)
        jitter_x = random.uniform(-0.05, 0.05)
        jitter_y = random.uniform(-0.05, 0.05)
        jitter_z = random.uniform(-0.05, 0.05)

        # Body clusters (torso, legs, arm)
        num_clusters = random.randint(1, max_clusters)
        cluster_centers = [generate_cluster_center() for _ in range(num_clusters)]

        for cx, cy, cz in cluster_centers:
            
            num_points = random.randint(1, 4)  # multi-reflection Doppler
        
            for _ in range(num_points):

                # Apply slow drift over time
                dx = drift_x * (frame / num_frames)
                dy = drift_y * (frame / num_frames)
                dz = drift_z * (frame / num_frames)

                # Position of reflected point
                x = add_noise(cx + jitter_x + dx)
                y = add_noise(cy + jitter_y + dy)
                z = add_noise(cz + jitter_z + dz)

                # Vertical movement pattern (breathing, leaning, steps)
                vertical_shift = random.uniform(-0.06, 0.06)
                if random.random() < 0.15:
                    z += vertical_shift  # small vertical movement

                # Doppler velocity generation
                base_v = random.uniform(-0.25, 0.25)

                # Random burst events (movement frames)
                if random.random() < 0.25:
                    v = random.uniform(-1.0, 1.0)  # real movement
                else:
                    v = base_v  # mostly static

                # Compute Δz (vertical motion cue)
                if prev_z is not None:
                    delta_z = z - prev_z
                else:
                    delta_z = 0

                # Compute Δv
                if prev_v is not None:
                    delta_v = v - prev_v
                else:
                    delta_v = 0

                prev_z = z
                prev_v = v

                # -------------------------------
                # Realistic Label Assignment
                # -------------------------------
                # Motion is determined by multiple cues:
                #   - velocity magnitude
                #   - vertical change
                #   - jitter bursts
                #   - random ambiguity near threshold
                # -------------------------------

                motion_score = 0

                # Velocity effect
                if abs(v) > 0.45:
                    motion_score += 1
                if abs(v) > 0.9:
                    motion_score += 1  # strong movement

                # Vertical movement effect
                if abs(delta_z) > 0.10:
                    motion_score += 1  # small step / torso shift

                # Frame jitter interpreted as false movement
                if random.random() < 0.03:
                    motion_score += 1  # false positive noise

                # Final label
                label = 1 if motion_score >= 2 else 0

                # Label noise — real sensors are imperfect
                if random.random() < 0.05:
                    label = 1 - label

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

    joblib.dump(model, "radar_random_forest_robust.pkl")
    print("[INFO] Model saved to radar_random_forest_robust.pkl")

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
