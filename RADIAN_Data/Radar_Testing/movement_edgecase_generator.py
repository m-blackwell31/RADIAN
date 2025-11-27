import numpy as np
import random

# -------------------------------------------------------------
# Utilities
# -------------------------------------------------------------
def add_noise(points, noise_std=0.05, dropout_prob=0.1, outlier_prob=0.05):
    """
    Adds gaussian noise, random dropouts, and outlier points
    """
    x, y, z, v = points.T

    # Gaussian noise (real sensors always have some jitter)
    x += np.random.normal(0, noise_std, size=len(points))
    y += np.random.normal(0, noise_std, size=len(points))
    z += np.random.normal(0, noise_std, size=len(points))

    # Dropout: randomly remove some points
    keep_mask = np.random.rand(len(points)) > dropout_prob
    x, y, z, v = x[keep_mask], y[keep_mask], z[keep_mask], v[keep_mask]

    # Outliers (ghost targets)
    num_outliers = int(outlier_prob * len(points))
    if num_outliers > 0:
        out_x = np.random.uniform(-1, 1, num_outliers)
        out_y = np.random.uniform(-1, 1, num_outliers)
        out_z = np.random.uniform(0, 2, num_outliers)
        out_v = np.random.uniform(-1, 1, num_outliers)
        x = np.concatenate([x, out_x])
        y = np.concatenate([y, out_y])
        z = np.concatenate([z, out_z])
        v = np.concatenate([v, out_v])

    return np.column_stack([x, y, z, v])


# -------------------------------------------------------------
# Edge Case Generators
# All return: list of frames, label_string
# Each frame: Nx4 array
# -------------------------------------------------------------

def simulate_sitting(num_frames=40, points=60):
    """
    Person moves from standing height (z≈1.6) down to sitting (z≈0.8)
    """
    frames = []
    for i in range(num_frames):
        z_height = 1.6 - 0.8 * (i / num_frames)   # smooth descent
        velocity = -0.02 if i < num_frames*(2/3) else 0
        frame = np.column_stack([
            np.random.uniform(-0.3, 0.3, points),
            np.random.uniform(-0.3, 0.3, points),
            np.random.normal(z_height, 0.05, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_bending_over(num_frames=30, points=50):
    """
    Upper body lowers but legs remain same height → average z drops mildly
    """
    frames = []
    for i in range(num_frames):
        z_height = 1.4 - 0.4 * (i / num_frames)   # partial drop
        velocity = -0.01 if i < num_frames*(0.7) else 0
        frame = np.column_stack([
            np.random.uniform(-0.3, 0.3, points),
            np.random.uniform(-0.3, 0.3, points),
            np.random.normal(z_height, 0.06, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_kneeling(num_frames=35, points=55):
    """
    Person drops from standing → knee height (~0.5m)
    but controlled, not a fall
    """
    frames = []
    for i in range(num_frames):
        z_height = 1.6 - 1.1*(i/num_frames)
        velocity = -0.03 if i < num_frames*(0.5) else 0
        frame = np.column_stack([
            np.random.uniform(-0.3, 0.3, points),
            np.random.uniform(-0.3, 0.3, points),
            np.random.normal(z_height, 0.07, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_slow_fall(num_frames=50, points=70):
    """
    Fall occurs but very slowly (elderly fall, sliding down wall)
    """
    frames = []
    for i in range(num_frames):
        z_height = 1.6 - 1.5*(i/num_frames)
        velocity = -0.05
        frame = np.column_stack([
            np.random.uniform(-0.3, 0.3, points),
            np.random.uniform(-0.3, 0.3, points),
            np.random.normal(z_height, 0.1, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "fall"


def simulate_trip_recover(num_frames=45, points=60):
    """
    Sharp drop then recovery → NOT a fall
    """
    frames = []
    for i in range(num_frames):
        if i < 10:
            z_height = 1.6 - 0.6*(i/10)  # sharp drop
            velocity = -0.10
        else:
            z_height = 1.0 + 0.6*((i-10)/(num_frames-10))  # recovery
            velocity = +0.10 if i < 20 else 0

        frame = np.column_stack([
            np.random.uniform(-0.3, 0.3, points),
            np.random.uniform(-0.3, 0.3, points),
            np.random.normal(z_height, 0.08, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_crawling(num_frames=50, points=80):
    """
    Low z (~0.3–0.4) but with ongoing movement
    """
    frames = []
    for i in range(num_frames):
        z_height = 0.3 + 0.05*np.sin(i/5)
        velocity = 0.05
        frame = np.column_stack([
            np.random.uniform(-0.5, 0.5, points),
            np.random.uniform(-0.5, 0.5, points),
            np.random.normal(z_height, 0.04, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_pet_walk(num_frames=30, points=40):
    """
    Small object at low Z moving fast
    """
    frames = []
    for i in range(num_frames):
        z_height = 0.2 + 0.03*np.sin(i)
        velocity = 0.3
        frame = np.column_stack([
            np.random.uniform(-1, 1, points),
            np.random.uniform(-1, 1, points),
            np.random.normal(z_height, 0.03, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_object_drop(num_frames=15, points=20):
    """
    Object falls extremely fast → NOT a human fall
    """
    frames = []
    for i in range(num_frames):
        z_height = 1.5 - 1.4*(i/num_frames)
        velocity = -1.0  # very fast
        frame = np.column_stack([
            np.random.uniform(-0.1, 0.1, points),
            np.random.uniform(-0.1, 0.1, points),
            np.random.normal(z_height, 0.02, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "not_fall"


def simulate_hard_fall(num_frames=30, points=80):
    """
    True sudden fall → large negative velocity & final low z
    """
    frames = []
    for i in range(num_frames):
        if i < 8:
            z_height = 1.6 - 1.5*(i/8)
            velocity = -0.5
        else:
            z_height = 0.1
            velocity = 0
        frame = np.column_stack([
            np.random.uniform(-0.4, 0.4, points),
            np.random.uniform(-0.4, 0.4, points),
            np.random.normal(z_height, 0.1, points),
            np.full(points, velocity)
        ])
        frames.append(add_noise(frame))
    return frames, "fall"
