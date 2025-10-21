from sklearn.tree import DecisionTreeClassifier #Machine Learning model I am training
from sklearn.model_selection import train_test_split #Splits the data into a training set (to train the model) and a test set (to evaluate)
from sklearn.metrics import accuracy_score #Function to check how well the model predicted the test data

# Example synthetic dataset: [feature1, feature2, feature3...]
# This dataset from GPT is specifcally using "Acceleration Magnitude (m/s^2)" and "Vertical Velocity Change (m/s)"
X = [
    [0.1, 5.2],  # not a fall
    [0.3, 6.0],  # not a fall
    [9.8, 0.5],  # fall
    [10.1, 0.4], # fall
]

#Some examples of what we can include as fall parameters
'''
1. Acceleration Magnitude (m/s^2)
2. Velocity Change (delta_v, m/s)
3. Jerk (m/s^3)
4. Movement Duration
5. Height Change (Radar-Estimated)
6. Body Orientation Change
7. Posture after event
8. Energy of Radar Return
9. Mirco-Doppler Signature
10. Frequency Spread (Doppler Bandwidth)
11. Mean, Variance, Skewness of acceleration
12. Root Mean Square (RMS) of Velocity
13. Peak-to-Peak Amplitude
'''

# Labels (0 = no fall, 1 = fall)
y = [0, 0, 1, 1]

# Split into training & test sets
# "random_state" makes the split reproducible
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# Create and train the decision tree
clf = DecisionTreeClassifier() # Creates a new decision model
clf.fit(X_train, y_train) # Trains the model on your training data (the tree “learns” how to map features → labels).

# Test the model
y_pred = clf.predict(X_test)
print("Predictions:", y_pred)
print("Accuracy:", accuracy_score(y_test, y_pred))
