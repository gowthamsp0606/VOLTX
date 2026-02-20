import joblib
import numpy as np

model = joblib.load("theft_model.pkl")

def detect_theft(voltage: float, current: float):
    X = np.array([[voltage, current]])
    prediction = model.predict(X)

    if prediction[0] == -1:
        return "⚠️ THEFT / ANOMALY DETECTED"
    else:
        return "✅ NORMAL"