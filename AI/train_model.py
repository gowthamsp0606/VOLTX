import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

np.random.seed(42)

# -----------------------------
# NORMAL ELECTRIC GRID DATA
# -----------------------------

normal_voltage = np.random.normal(230, 4, 4000)
normal_current = np.random.normal(7, 2, 4000)

# clip realistic limits
normal_voltage = np.clip(normal_voltage, 215, 245)
normal_current = np.clip(normal_current, 2, 12)

normal_data = np.column_stack((normal_voltage, normal_current))

# -----------------------------
# THEFT / ANOMALY DATA
# -----------------------------

theft_voltage = np.random.uniform(140, 180, 600)
theft_current = np.random.uniform(20, 40, 600)

anomaly_data = np.column_stack((theft_voltage, theft_current))

# -----------------------------
# COMBINE DATA
# -----------------------------

X = np.vstack((normal_data, anomaly_data))

# -----------------------------
# SCALE DATA
# -----------------------------

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# -----------------------------
# TRAIN MODEL
# -----------------------------

model = IsolationForest(
    contamination=0.12,
    n_estimators=200,
    random_state=42
)

model.fit(X_scaled)

# -----------------------------
# SAVE MODEL
# -----------------------------

joblib.dump(model, "theft_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("AI MODEL TRAINED SUCCESSFULLY")
