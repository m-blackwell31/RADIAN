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
model = joblib.load("radar_random_forest_even_more_robust.pkl")
print("[INFO] Loaded trained Random Forest model")

# ---------------------------------------------------------
# IMPORT EDGECASE GENERATORS
# ---------------------------------------------------------
from movement_edgecase_generator import (
    simulate_sitting,
    simulate_bending_over,
    simulate_kneeling,
    simulate_slow_fall,
    simulate_trip_recover,
    simulate_crawling,
    simulate_pet_walk,
    simulate_object_drop,
    simulate_hard_fall
)

EDGECASE_GENERATORS = [
    simulate_sitting,
    simulate_bending_over,
    simulate_kneeling,
    simulate_slow_fall,
    simulate_trip_recover,
    simulate_crawling,
    simulate_pet_walk,
    simulate_object_drop,
    simulate_hard_fall
]

# ---------------------------------------------------------
# FRAME CONVERSION HELPERS
# ---------------------------------------------------------
def edgecase_frame_to_df(frame_arr):
    return pd.DataFrame({
        "x": frame_arr[:, 0],
        "y": frame_arr[:, 1],
        "z": frame_arr[:, 2],
        "v": frame_arr[:, 3]
    })

# ---------------------------------------------------------
# USER MODE SELECTION
# ---------------------------------------------------------
def choose_simulation_mode():
    print("\nSelect simulation mode:")
    print("1 → Normal fall simulation")
    print("2 → Edge case simulation")

    while True:
        mode_input = input("Enter 1 or 2: ").strip()
        if mode_input == "1":
            return "normal_fall", None
        elif mode_input == "2":
            return "edgecase", choose_edgecase()
        else:
            print("Invalid input. Please enter 1 or 2.")

def choose_edgecase():
    print("\nSelect which edgecase to run:")
    for i, gen in enumerate(EDGECASE_GENERATORS):
        print(f"{i+1} → {gen.__name__}")

    while True:
        case_input = input(f"Enter a number (1–{len(EDGECASE_GENERATORS)}): ").strip()
        if case_input.isdigit() and 1 <= int(case_input) <= len(EDGECASE_GENERATORS):
            return EDGECASE_GENERATORS[int(case_input) - 1]
        else:
            print("Invalid input. Try again.")

# ---------------------------------------------------------
# NORMAL SIMULATION FRAME GENERATION
# ---------------------------------------------------------
def generate_dummy_frame(num_points=5, z_base=1.0, z_noise=0.1, v_scale=1.0):
    frame = []
    for _ in range(num_points):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        z = z_base + random.uniform(-z_noise, z_noise)
        v = random.uniform(-1, 1) * v_scale
        frame.append({"x": x, "y": y, "z": z, "v": v})
    return pd.DataFrame(frame)

# ---------------------------------------------------------
# MAIN FALL DETECTION LOGIC
# ---------------------------------------------------------
def detect_fall(model, num_frames=100):
    history = []
    fall_detected = False

    # USER SELECTS MODE
    mode, selected_generator = choose_simulation_mode()
    print(f"[INFO] Simulation mode: {mode}")

    # -----------------------------------------------------
    # EDGECASE MODE
    # -----------------------------------------------------
    if mode == "edgecase":
        frames, label = selected_generator()
        edge_frames = [edgecase_frame_to_df(f) for f in frames]

        for frame_idx, df in enumerate(edge_frames):
            predictions = model.predict(df[["x", "y", "z", "v"]])
            df["predicted_label"] = predictions

            avg_z = df["z"].mean()
            static_ratio = (df["predicted_label"] == 0).mean()

            history.append({
                "frame": frame_idx,
                "avg_z": avg_z,
                "static_ratio": static_ratio
            })

            time.sleep(0.05)

        print("\n✅ Edge case simulation completed (no fall expected).")
        show_recent_frames(history)
        return

    # -----------------------------------------------------
    # NORMAL FALL SIMULATION MODE
    # -----------------------------------------------------
    fall_start = random.choice([None, random.randint(15, 40)])
    print(f"[INFO] Simulating {'fall at frame ' + str(fall_start) if fall_start else 'no fall this time'}")

    for frame_idx in range(num_frames):

        if fall_start and frame_idx < fall_start:
            df = generate_dummy_frame(z_base=1.0, v_scale=1.0)

        elif fall_start and fall_start <= frame_idx < fall_start + 5:
            df = generate_dummy_frame(z_base=0.1, v_scale=2.5)

        else:
            df = generate_dummy_frame(
                z_base=(0.1 if fall_start else 1.0),
                v_scale=(0.1 if fall_start else 1.0)
            )

        predictions = model.predict(df[["x", "y", "z", "v"]])
        df["predicted_label"] = predictions

        avg_z = df["z"].mean()
        static_ratio = (df["predicted_label"] == 0).mean()

        history.append({
            "frame": frame_idx,
            "avg_z": avg_z,
            "static_ratio": static_ratio
        })

        # FALL CHECK
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

        time.sleep(0.05)

    if not fall_detected:
        print("\n✅ No fall detected in simulation.")

# ---------------------------------------------------------
# VISUALIZATION
# ---------------------------------------------------------
def show_recent_frames(history, lookback=75):
    print(f"\n--- Showing last {lookback} frames ---")
    recent = history[-lookback:]

    for h in recent:
        print(
            f"Frame {h['frame']:3d}: "
            f"avg_z={h['avg_z']:.3f}, "
            f"static_ratio={h['static_ratio']:.3f}"
        )

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Starting fall detection simulation...\n")
    detect_fall(model)
