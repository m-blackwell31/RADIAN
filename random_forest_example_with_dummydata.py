# ============================================================
#  FALL DETECTION - RANDOM FOREST DEMO
#  Works on Raspberry Pi and standard desktops
#  ------------------------------------------------------------
#  Generates dummy sensor data for testing ML pipeline
#  Author: RADIAN Project
# ============================================================

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib

# ------------------------------------------------------------
# 1. Simulate Dummy Sensor Data
# ------------------------------------------------------------
# Features (you can later replace these with real radar or IMU features)
# - accel_mag_change: sudden acceleration magnitude (g)
# - velocity_var: variance of movement velocity
# - height_change: change in vertical height or body position
# - inactivity_dur: time of inactivity after impact (seconds)
# - impact_intensity: simulated impact force

np.random.seed(42)
num_samples = 500  # total examples

# Generate synthetic "no fall" (class = 0)
no_fall = np.column_stack([
    np.random.normal(0.5, 0.1, num_samples//2),   # accel_mag_change
    np.random.normal(0.4, 0.1, num_samples//2),   # velocity_var
    np.random.normal(0.1, 0.05, num_samples//2),  # height_change
    np.random.normal(0.3, 0.1, num_samples//2),   # inactivity_dur
    np.random.normal(0.2, 0.05, num_samples//2)   # impact_intensity
])

# Generate synthetic "fall" (class = 1)
fall = np.column_stack([
    np.random.normal(1.5, 0.2, num_samples//2),
    np.random.normal(1.2, 0.2, num_samples//2),
    np.random.normal(0.8, 0.15, num_samples//2),
    np.random.normal(1.0, 0.2, num_samples//2),
    np.random.normal(1.3, 0.2, num_samples//2)
])

# Combine into one dataset
X = np.vstack((no_fall, fall))
y = np.hstack((np.zeros(num_samples//2), np.ones(num_samples//2)))

# Convert to DataFrame for easy viewing
df = pd.DataFrame(X, columns=["accel_mag_change", "velocity_var", "height_change", "inactivity_dur", "impact_intensity"])
df["fall_detected"] = y

print("Sample of training data:\n")
print(df.head())

# ------------------------------------------------------------
# 2. Split Data
# ------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df.drop(columns=["fall_detected"]),
    df["fall_detected"],
    test_size=0.2,
    random_state=42
)

# ------------------------------------------------------------
# 3. Train Random Forest Model
# ------------------------------------------------------------
rf = RandomForestClassifier(
    n_estimators=25,     # number of trees
    max_depth=6,         # limit tree depth to keep model small
    random_state=42
)

rf.fit(X_train, y_train)

# ------------------------------------------------------------
# 4. Evaluate Model
# ------------------------------------------------------------
y_pred = rf.predict(X_test)

print("\nModel Evaluation:")
print("Accuracy:", round(accuracy_score(y_test, y_pred) * 100, 2), "%")
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nDetailed Report:\n", classification_report(y_test, y_pred))

# ------------------------------------------------------------
# 5. Save Model for Later (for Raspberry Pi use)
# ------------------------------------------------------------
joblib.dump(rf, "fall_detection_random_forest.pkl")
print("\nModel saved as 'fall_detection_random_forest.pkl'")

# ------------------------------------------------------------
# 6. Example of Loading and Using Model
# ------------------------------------------------------------
loaded_model = joblib.load("fall_detection_random_forest.pkl")

# Example dummy test case: [accel, velocity, height, inactivity, impact]
new_reading = np.array([[1.4, 1.1, 0.9, 1.1, 1.2]])
prediction = loaded_model.predict(new_reading)
print("\nPrediction for new reading:", "FALL" if prediction[0] == 1 else "NO FALL")