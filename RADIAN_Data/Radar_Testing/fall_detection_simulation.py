import time
import random
import joblib
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------
STATIC_THRESHOLD = 0.6   # % of points classified static after fall
Z_DROP_THRESHOLD = 0.5   # meters drop indicating fall
STILL_FRAMES = 5         # how many frames person stays still

# ---------------------------------------------------------
# LOAD TRAINED MODEL
# ---------------------------------------------------------
model = joblib.load("radar_random_forest.pkl")
print("[INFO] Loaded trained Random Forest model")

# ---------------------------------------------------------
# SIMULATE RADAR FRAME GENERATION
# ---------------------------------------------------------
def generate_dummy_frame(num_points=5, z_base=1.0, z_noise=0.1, v_scale=1.0):
    """Generate a dummy radar frame with a given z-base and velocity scale."""
    frame = []
    for _ in range(num_points):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        z = z_base + random.uniform(-z_noise, z_noise)
        v = random.uniform(-1, 1) * v_scale
        frame.append({"x": x, "y": y, "z": z, "v": v})
    return pd.DataFrame(frame)

# ---------------------------------------------------------
# FALL DETECTION LOGIC
# ---------------------------------------------------------
def detect_fall(model, num_frames=60):
    """Simulate radar stream and detect falls."""
    history = []
    fall_detected = False

    for frame_idx in range(num_frames):
        # Simulate behavior: normal frames, sudden drop, then still
        if frame_idx < 20:
            df = generate_dummy_frame(z_base=1.0, v_scale=1.0)  # standing/moving
        elif 20 <= frame_idx < 25:
            df = generate_dummy_frame(z_base=0.4, v_scale=2.0)  # fall in motion
        else:
            df = generate_dummy_frame(z_base=0.3, v_scale=0.1)  # lying still

        # Predict movement/static
        predictions = model.predict(df[["x", "y", "z", "v"]])
        df["predicted_label"] = predictions

        # Track average z and % static
        avg_z = df["z"].mean()
        static_ratio = (df["predicted_label"] == 0).mean()

        history.append({"frame": frame_idx, "avg_z": avg_z, "static_ratio": static_ratio})

        # Check fall condition
        if len(history) > 2:
            z_change = history[-2]["avg_z"] - avg_z
            if (z_change > Z_DROP_THRESHOLD and static_ratio > STATIC_THRESHOLD):
                print(f"\n🚨 Fall detected at frame {frame_idx}!")
                fall_detected = True
                show_recent_frames(history)
                break

        time.sleep(0.05)  # simulate real-time stream

    if not fall_detected:
        print("\n✅ No fall detected in simulation.")

# ---------------------------------------------------------
# VISUALIZATION HELPERS
# ---------------------------------------------------------
def show_recent_frames(history, lookback=10):
    """Display the last few frames to see what triggered the fall."""
    print("\n--- Recent Frames ---")
    recent = history[-lookback:]
    for h in recent:
        print(f"Frame {h['frame']:3d}: avg_z={h['avg_z']:.2f}, static_ratio={h['static_ratio']:.2f}")

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Starting fall detection simulation...\n")
    detect_fall(model)
