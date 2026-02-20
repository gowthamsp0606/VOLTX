import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

np.random.seed(42)

# ---------------- NORMAL GRID DATA ----------------
normal_voltage = np.random.normal(230, 6, 2000)   # realistic voltage range
normal_current = np.random.normal(8, 3, 2000)     # allow 5–12A normal load

X_train = np.column_stack((normal_voltage, normal_current))

# ---------------- TRAIN MODEL ----------------
model = IsolationForest(
    n_estimators=300,
    contamination=0.02,   # assume only 2% anomalies
    random_state=42
)

model.fit(X_train)

joblib.dump(model, "model.joblib")

print("✅ AI model trained with realistic grid behaviour")