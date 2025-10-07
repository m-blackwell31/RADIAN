# fall_detection_realistic.py

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score
import joblib

# ------------------------------
# 1. Generate realistic dummy data
# ------------------------------
np.random.seed(42)
n_samples = 500

# Simulated accelerometer + gyro data
# "No fall" readings: mostly stationary, light movement
no_fall = {
    'accel_x': np.random.normal(0.0, 0.5, n_samples),
    'accel_y': np.random.normal(0.0, 0.5, n_samples),
    'accel_z': np.random.normal(9.8, 0.3, n_samples),
    'gyro_x': np.random.normal(0.0, 0.2, n_samples),
    'gyro_y': np.random.normal(0.0, 0.2, n_samples)
}

# "Fall" readings: sudden acceleration + rotation, but overlapping with noise
fall = {
    'accel_x': np.random.normal(1.5, 1.5, n_samples),
    'accel_y': np.random.normal(1.0, 1.5, n_samples),
    'accel_z': np.random.normal(10.3, 1.0, n_samples),
    'gyro_x': np.random.normal(0.6, 0.5, n_samples),
    'gyro_y': np.random.normal(0.8, 0.5, n_samples)
}

# Combine and label
df_no_fall = pd.DataFrame(no_fall)
df_no_fall['fall'] = 0

df_fall = pd.DataFrame(fall)
df_fall['fall'] = 1

data = pd.concat([df_no_fall, df_fall], ignore_index=True)

# ------------------------------
# 2. Split into features and labels
# ------------------------------
feature_cols = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y']
X = data[feature_cols]
y = data['fall']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

# ------------------------------
# 3. Train the Random Forest
# ------------------------------
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ------------------------------
# 4. Evaluate the model
# ------------------------------
y_pred = model.predict(X_test)

cm = confusion_matrix(y_test, y_pred)
acc = accuracy_score(y_test, y_pred)

print("\nConfusion Matrix:\n", cm)
print(f"\nAccuracy: {acc*100:.2f}%")

# ------------------------------
# 5. Save the model
# ------------------------------
joblib.dump(model, "fall_detection_model.pkl")
print("\nModel saved as fall_detection_model.pkl")

# ------------------------------
# 6. Load and test a new reading
# ------------------------------
loaded_model = joblib.load("fall_detection_model.pkl")

# Simulate a new accelerometer/gyro reading
new_reading = pd.DataFrame(
    [[0.8, 0.3, 9.9, 0.2, 0.1]],  # Looks like "no fall"
    columns=feature_cols
)

prediction = loaded_model.predict(new_reading)
print("\nPredicted class (1 = fall, 0 = no fall):", prediction[0])
