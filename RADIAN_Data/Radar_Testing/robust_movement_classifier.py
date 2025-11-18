# ---------------------------------------------------------
# STEP 1: Generate radar-like dummy data (UPGRADED)
# ---------------------------------------------------------

def add_noise(value, sigma=0.05):
    """Gaussian noise to simulate radar measurement noise."""
    return value + random.gauss(0, sigma)

def generate_cluster_center():
    """Returns the center of a Doppler cluster."""
    return (
        random.uniform(-1.5, 1.5),  # cx
        random.uniform(-1.5, 1.5),  # cy
        random.uniform(0, 1.5)      # cz (height)
    )

def generate_radar_training_data(num_frames=200, max_clusters=3):
    """
    Creates more realistic radar-like data with:
      - noise
      - jitter
      - slow drift
      - multi-point Doppler clusters
    Labels remain binary: movement if |v| > 0.4
    """
    data = []
    slow_drift_x = random.uniform(-0.1, 0.1)
    slow_drift_y = random.uniform(-0.1, 0.1)
    slow_drift_z = random.uniform(-0.1, 0.1)

    for frame in range(num_frames):

        # Small jitter per frame (simulate radar instability)
        frame_jitter_x = random.uniform(-0.05, 0.05)
        frame_jitter_y = random.uniform(-0.05, 0.05)
        frame_jitter_z = random.uniform(-0.05, 0.05)

        # Choose how many clusters exist in this frame
        num_clusters = random.randint(1, max_clusters)
        cluster_centers = [generate_cluster_center() for _ in range(num_clusters)]

        for cx, cy, cz in cluster_centers:
            num_points = random.randint(1, 4)  # multi-point Doppler returns

            for _ in range(num_points):

                # Apply slow drift (movement of body torso)
                drift_x = slow_drift_x * (frame / num_frames)
                drift_y = slow_drift_y * (frame / num_frames)
                drift_z = slow_drift_z * (frame / num_frames)

                x = add_noise(cx + frame_jitter_x + drift_x)
                y = add_noise(cy + frame_jitter_y + drift_y)
                z = add_noise(cz + frame_jitter_z + drift_z)

                # Doppler velocity: mixture of noise + occasional motion
                # Randomly simulate a "movement event" in ~20% of frames
                if random.random() < 0.2:
                    v = random.uniform(-1.2, 1.2)  # strong movement
                else:
                    v = random.uniform(-0.2, 0.2)  # mostly static noise

                # Label rule stays the same
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
