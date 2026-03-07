# VoltGuard AI — Frontend

## Setup (3 commands)

```bash
npm install
npm run dev
```

Open → http://localhost:3000

## Usage

1. Make sure your FastAPI backend is running:
   ```
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. In the dashboard, type your machine's **local IP** into the input box
   (e.g. `192.168.1.42` — find it with `ipconfig` on Windows or `ifconfig` on Linux/Mac)

3. Click **CONNECT** — the dashboard will start polling every 2 seconds

4. Dashboard shows live data as soon as your ESP32 POSTs to `/predict`

## API Compatibility

Reads from your `main.py`:
- `GET /status`  → latest sensor reading
- `GET /history` → last 50 readings

Confidence is read as **0–100** (matches your `model.decision_function * 100` output).

## File Structure

```
src/
  components/
    Sidebar.jsx
    IPConfigBar.jsx
    StatusCards.jsx
    EnergyChart.jsx       ← uses Recharts
    AIPanel.jsx
    TransactionPanel.jsx
    SystemHealth.jsx
    HistoryTable.jsx
    TheftAlert.jsx
    PulseDot.jsx
    SparkLine.jsx
  services/
    api.js
  App.jsx
  app.css
  main.jsx
```
