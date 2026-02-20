const API_URL = "http://127.0.0.1:8000/predict";

let time = 0;
const labels = [];

const voltageData = [];
const currentData = [];

const voltageCtx = document.getElementById('voltageChart').getContext('2d');
const currentCtx = document.getElementById('currentChart').getContext('2d');

const voltageChart = new Chart(voltageCtx, {
  type: 'line',
  data: {
    labels,
    datasets: [{
      label: 'Voltage (V)',
      data: voltageData,
      borderColor: '#00ffff',
      tension: 0.4
    }]
  }
});

const currentChart = new Chart(currentCtx, {
  type: 'line',
  data: {
    labels,
    datasets: [{
      label: 'Current (A)',
      data: currentData,
      borderColor: '#ff0066',
      tension: 0.4
    }]
  }
});

async function fetchData() {
  // 🔥 simulate sensor data
  const voltage = Math.floor(Math.random() * (260 - 150) + 150);
  const current = Math.floor(Math.random() * (40 - 5) + 5);

  document.getElementById("voltageValue").innerText = voltage;
  document.getElementById("currentValue").innerText = current;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voltage, current })
    });

    const result = await response.json();

    const statusCard = document.getElementById("statusCard");
    const theftStatus = document.getElementById("theftStatus");
    const reasonText = document.getElementById("reasonText");

    if (result.theft === "YES") {
      theftStatus.innerText = "🚨 POWER THEFT DETECTED";
      reasonText.innerText = result.reason;
      statusCard.className = "status-card danger";
    } else {
      theftStatus.innerText = "✅ NORMAL OPERATION";
      reasonText.innerText = result.reason;
      statusCard.className = "status-card safe";
    }

  } catch (err) {
    console.error("API Error", err);
  }

  labels.push(time++);
  voltageData.push(voltage);
  currentData.push(current);

  if (labels.length > 20) {
    labels.shift();
    voltageData.shift();
    currentData.shift();
  }

  voltageChart.update();
  currentChart.update();
}

setInterval(fetchData, 1500);