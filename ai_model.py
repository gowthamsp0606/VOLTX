from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest

# ---------------- APP SETUP ----------------
app = FastAPI(title="VOLTX PRO – High Sensitivity Adaptive AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_FILE = "model.joblib"

# ---------------- CONFIG ----------------
CONTAMINATION = 0.08        # Higher sensitivity (8%)
THRESHOLD = -0.05           # Custom anomaly threshold
MAX_BUFFER = 300            # Store last 300 normal samples
RETRAIN_INTERVAL = 50       # Retrain after 50 normal samples

normal_buffer = []
normal_counter = 0
latest_status = {}

# ---------------- CREATE INITIAL MODEL ----------------
def create_initial_model():
    normal_voltage = np.random.normal(230, 5, 1500)
    normal_current = np.random.normal(8, 2, 1500)
    normal_power = normal_voltage * normal_current

    X = np.column_stack((normal_voltage, normal_current, normal_power))

    model = IsolationForest(
        n_estimators=400,
        contamination=CONTAMINATION,
        random_state=42
    )

    model.fit(X)
    joblib.dump(model, MODEL_FILE)
    return model

# ---------------- LOAD MODEL ----------------
if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    model = create_initial_model()

# ---------------- DATA MODEL ----------------
class SensorData(BaseModel):
    voltage: float
    current: float

# ---------------- RETRAIN MODEL ----------------
def retrain_model():
    global model

    if len(normal_buffer) < 100:
        return

    X = np.array(normal_buffer)

    new_model = IsolationForest(
        n_estimators=400,
        contamination=CONTAMINATION,
        random_state=42
    )

    new_model.fit(X)
    model = new_model
    joblib.dump(model, MODEL_FILE)

    print("🔁 Adaptive AI retrained (High Sensitivity Mode)")

# ---------------- PREDICTION ----------------
@app.post("/predict")
def predict(data: SensorData):
    global latest_status, normal_counter

    power = data.voltage * data.current

    X = np.array([[data.voltage, data.current, power]])

    score = model.decision_function(X)[0]

    # Custom threshold sensitivity
    is_theft = score < THRESHOLD

    # Store normal data for adaptive learning
    if not is_theft:
        normal_buffer.append([data.voltage, data.current, power])
        normal_counter += 1

        if len(normal_buffer) > MAX_BUFFER:
            normal_buffer.pop(0)

        if normal_counter >= RETRAIN_INTERVAL:
            retrain_model()
            normal_counter = 0

    confidence = min(1.0, abs(score) * 6)

    latest_status = {
        "voltage": data.voltage,
        "current": data.current,
        "power": round(power, 2),
        "theft": "YES" if is_theft else "NO",
        "confidence": round(confidence, 2),
        "reason": (
            "High Sensitivity AI detected abnormal voltage/current/power pattern"
            if is_theft
            else "AI confirms stable grid behavior"
        )
    }

    return latest_status

# ---------------- STATUS FOR DASHBOARD ----------------
@app.get("/status")
def status():
    return latest_status
