from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest

# ---------------- APP SETUP ----------------
app = FastAPI(title="VOLTX PRO – Adaptive AI Power Theft Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_FILE = "model.joblib"

# ---------------- LOAD / CREATE MODEL ----------------
def create_initial_model():
    # fallback training if no model exists
    normal_voltage = np.random.normal(230, 6, 1000)
    normal_current = np.random.normal(8, 3, 1000)
    X = np.column_stack((normal_voltage, normal_current))

    model = IsolationForest(n_estimators=200, contamination=0.02)
    model.fit(X)
    joblib.dump(model, MODEL_FILE)
    return model


if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    model = create_initial_model()

latest_status = {}

# ---------------- ADAPTIVE BUFFER ----------------
normal_buffer = []     # stores recent NORMAL samples
MAX_BUFFER = 200       # how many samples to remember
RETRAIN_INTERVAL = 50  # retrain after every 50 new normal points
normal_counter = 0

# ---------------- DATA MODEL ----------------
class SensorData(BaseModel):
    voltage: float
    current: float


# ---------------- ADAPTIVE RETRAIN ----------------
def retrain_model():
    global model, normal_buffer

    if len(normal_buffer) < 50:
        return

    X = np.array(normal_buffer)

    new_model = IsolationForest(
        n_estimators=200,
        contamination=0.02,
        random_state=42
    )
    new_model.fit(X)

    model = new_model
    joblib.dump(model, MODEL_FILE)

    print("🔁 Adaptive AI retrained using latest grid behavior")


# ---------------- AI PREDICTION ----------------
@app.post("/predict")
def predict(data: SensorData):
    global latest_status, normal_counter

    X = np.array([[data.voltage, data.current]])

    prediction = model.predict(X)[0]
    score = model.decision_function(X)[0]

    is_theft = prediction == -1

    # ---------------- STORE NORMAL DATA FOR LEARNING ----------------
    if not is_theft:
        normal_buffer.append([data.voltage, data.current])
        normal_counter += 1

        if len(normal_buffer) > MAX_BUFFER:
            normal_buffer.pop(0)

        # Retrain periodically
        if normal_counter >= RETRAIN_INTERVAL:
            retrain_model()
            normal_counter = 0

    # ---------------- RESPONSE ----------------
    latest_status = {
        "voltage": data.voltage,
        "current": data.current,
        "theft": "YES" if is_theft else "NO",
        "confidence": round(min(1.0, abs(score) * 5), 2),
        "reason": (
            "Adaptive AI detected abnormal voltage/current pattern"
            if is_theft
            else "Adaptive AI confirms normal grid behavior"
        )
    }

    return latest_status


# ---------------- FRONTEND STATUS ----------------
@app.get("/status")
def status():
    return latest_status