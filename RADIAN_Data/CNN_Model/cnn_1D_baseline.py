import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

# -----------------------------
# CONFIG
# -----------------------------
TIMESTEPS = 100     # frames per trial (10 sec @ 10 Hz)
FEATURES = 4        # x, y, z, v
NUM_CLASSES = 5     # sitting, standing, walking, laying, falling

# -----------------------------
# DUMMY DATA (replace later)
# -----------------------------
num_trials = 300

X = np.random.rand(num_trials, TIMESTEPS, FEATURES)
y = np.random.randint(0, NUM_CLASSES, size=num_trials)

y = to_categorical(y, NUM_CLASSES)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# MODEL
# -----------------------------
model = Sequential([
    Conv1D(32, kernel_size=5, activation='relu',
           input_shape=(TIMESTEPS, FEATURES)),
    MaxPooling1D(pool_size=2),

    Conv1D(64, kernel_size=5, activation='relu'),
    MaxPooling1D(pool_size=2),

    Flatten(),
    Dense(64, activation='relu'),
    Dropout(0.5),
    Dense(NUM_CLASSES, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# -----------------------------
# TRAIN
# -----------------------------
history = model.fit(
    X_train, y_train,
    epochs=20,
    batch_size=16,
    validation_split=0.2
)

# -----------------------------
# EVALUATE
# -----------------------------
test_loss, test_acc = model.evaluate(X_test, y_test)
print(f"Test accuracy: {test_acc:.3f}")

# -----------------------------
# SAVE MODEL
# -----------------------------
model.save("cnn_1d_activity_model.h5")
