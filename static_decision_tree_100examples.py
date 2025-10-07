import random
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ---------------------------
# Generate synthetic dataset
# ---------------------------

X = []  # features
y = []  # labels

# Generate 50 "not fall" samples
for _ in range(50):
    accel = random.uniform(0.1, 3.0)       # low acceleration
    height_change = random.uniform(0.0, 0.5) # small change in height
    X.append([accel, height_change])
    y.append(0)  # label = not fall

# Generate 50 "fall" samples
for _ in range(50):
    accel = random.uniform(7.0, 12.0)      # high acceleration
    height_change = random.uniform(1.0, 2.0) # big drop in height
    X.append([accel, height_change])
    y.append(1)  # label = fall

# ---------------------------
# Split dataset into training/testing
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# ---------------------------
# Train decision tree
# ---------------------------
clf = DecisionTreeClassifier()
clf.fit(X_train, y_train)

# ---------------------------
# Test the model
# ---------------------------
y_pred = clf.predict(X_test)
print("Predictions:", y_pred)
print("True labels:", y_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
