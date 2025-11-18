import time
import random
import joblib
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------
STATIC_THRESHOLD = 0.5   # % of points classified static after fall
Z_DROP_THRESHOLD = 0.3   # meters drop indicating fall
STILL_FRAMES = 5         # how many frames person stays still

# ---------------------------------------------------------
# LOAD TRAINED MODEL
# ---------------------------------------------------------
model = joblib.load("radar_random_forest_robust.pkl")
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
def detect_fall(model, num_frames=100):
    """Simulate radar stream and detect falls."""
    # Randomly decide if a fall happens
    fall_start = random.choice([None, random.randint(15, 40)])
    print(f"[INFO] Simulating {'fall at frame ' + str(fall_start) if fall_start else 'no fall this time'}")

    history = []
    fall_detected = False

    for frame_idx in range(num_frames):
        # Simulate behavior: normal frames, sudden drop, then still
        if fall_start and frame_idx < fall_start:
          df = generate_dummy_frame(z_base=1.0, v_scale=1.0)   # standing/moving
        elif fall_start and fall_start <= frame_idx < fall_start + 5:
          df = generate_dummy_frame(z_base=0.1, v_scale=2.5)   # falling
        else:
          df = generate_dummy_frame(z_base=(0.1 if fall_start else 1.0),
                                    v_scale=(0.1 if fall_start else 1.0))   # still or normal movement


        # Predict movement/static
        predictions = model.predict(df[["x", "y", "z", "v"]])
        df["predicted_label"] = predictions

        # Track average z and % static
        avg_z = df["z"].mean()
        static_ratio = (df["predicted_label"] == 0).mean()

        history.append({"frame": frame_idx, "avg_z": avg_z, "static_ratio": static_ratio})

        # Check fall condition
        if len(history) > STILL_FRAMES:
            recent = history[-STILL_FRAMES:]
            prev = history[-(2*STILL_FRAMES):-STILL_FRAMES]
            if len(prev) == STILL_FRAMES:
                z_before = np.mean([f["avg_z"] for f in prev])
                z_after = np.mean([f["avg_z"] for f in recent])
                z_change = z_before - z_after
                avg_static = np.mean([f["static_ratio"] for f in recent])
                if z_change > Z_DROP_THRESHOLD and avg_static > STATIC_THRESHOLD:
                    print(f"\n🚨 Fall detected at frame {frame_idx}!")
                    show_recent_frames(history)
                    fall_detected = True
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

def detect_fall(model, num_frames=100):
    scenarios = ["fall", "sit", "bend", "kneel", "jump", "object_drop", "none"]
    scenario = random.choice(scenarios)

    print(f"[INFO] Scenario selected: {scenario}")

    # Random start time for the event
    event_start = random.randint(15, 40) if scenario != "none" else None

    history = []
    fall_detected = False

    for frame_idx in range(num_frames):

        # ---------------------------------------------------------
        # A) NORMAL MOVEMENT (default)
        # ---------------------------------------------------------
        z_base = 1.0
        v_scale = 1.0

        # ---------------------------------------------------------
        # B) EVENT-SPECIFIC BEHAVIOR
        # ---------------------------------------------------------
        if scenario == "fall" and event_start and event_start <= frame_idx < event_start + 5:
            # Very fast Z drop + fast velocity
            z_base = 0.1
            v_scale = 2.5

        elif scenario == "sit" and event_start:
            if event_start <= frame_idx < event_start + 10:
                # gradual decrease in height
                z_base = 1.0 - 0.05 * (frame_idx - event_start)
                z_base = max(z_base, 0.6)
                v_scale = 0.6

        elif scenario == "bend" and event_start:
            if event_start <= frame_idx < event_start + 3:
                z_base = 0.4  # bending down
                v_scale = 1.5
            elif event_start + 3 <= frame_idx < event_start + 6:
                z_base = 1.0  # stands back up
                v_scale = 1.2

        elif scenario == "kneel" and event_start:
            if event_start <= frame_idx < event_start + 8:
                z_base = 1.0 - 0.07 * (frame_idx - event_start)
                z_base = max(z_base, 0.5)
                v_scale = 0.4

        elif scenario == "jump" and event_start:
            if frame_idx == event_start:
                z_base = 1.3  # jump up
                v_scale = 2.0
            elif event_start < frame_idx < event_start + 4:
                z_base = 1.0  # back down
                v_scale = 1.8

        elif scenario == "object_drop" and event_start:
            # Add a few falling points but not whole person
            z_base = 1.0
            v_scale = 1.0

        # ---------------------------------------------------------
        # Frame generation
        # ---------------------------------------------------------
        df = generate_dummy_frame(num_points=5, z_base=z_base, v_scale=v_scale)

        # Extra logic for object-drop case:
        if scenario == "object_drop" and event_start <= frame_idx < event_start + 5:
            dropped = pd.DataFrame([{
                "x": random.uniform(-0.2, 0.2),
                "y": random.uniform(-0.2, 0.2),
                "z": random.uniform(0.3, 1.0),
                "v": random.uniform(2.0, 3.0)
            }])
            df = pd.concat([df, dropped], ignore_index=True)

        # Predict movement/static
        predictions = model.predict(df[["x","y","z","v"]])
        df["predicted_label"] = predictions

        avg_z = df["z"].mean()
        static_ratio = (df["predicted_label"] == 0).mean()

        history.append({"frame": frame_idx, "avg_z": avg_z, "static_ratio": static_ratio})

        # ---------------------------------------------------------
        # Fall detection logic stays the same
        # ---------------------------------------------------------
        if len(history) > STILL_FRAMES:
            recent = history[-STILL_FRAMES:]
            prev = history[-(2*STILL_FRAMES):-STILL_FRAMES]

            if len(prev) == STILL_FRAMES:
                z_before = np.mean([f["avg_z"] for f in prev])
                z_after = np.mean([f["avg_z"] for f in recent])
                z_change = z_before - z_after
                avg_static = np.mean([f["static_ratio"] for f in recent])

                if z_change > Z_DROP_THRESHOLD and avg_static > STATIC_THRESHOLD:
                    print(f"\n🚨 Fall DETECTED at frame {frame_idx}!")
                    show_recent_frames(history)
                    fall_detected = True
                    break

        time.sleep(0.05)

    if not fall_detected:
        print("\n✅ No fall detected — correct behavior for this scenario.")
