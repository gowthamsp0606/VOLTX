#include <WiFi.h>
#include <HTTPClient.h>

// 🔹 WiFi Credentials
const char* ssid = "STJC_GENTS";
const char* password = "admin@123";

// 🔹 Backend IP (Ubuntu laptop IP + FastAPI port)
const char* serverURL = "http://172.16.17.95:8000/predict";

// 🔹 Timing
unsigned long lastTime = 0;
unsigned long interval = 5000; // 5 seconds

// 🔹 Counter for anomaly injection
int counter = 0;

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  randomSeed(analogRead(0));
}

void loop() {
  if (millis() - lastTime > interval) {

    float voltage;
    float current;

    // 🔴 Inject anomaly every 6th reading (~30 sec)
    if (counter % 6 == 0 && counter != 0) {
      voltage = random(150, 170);
      current = random(35, 45);
      Serial.println("🚨 ANOMALY DATA SENT");
    } 
    else {
      voltage = random(220, 235);
      current = random(6, 12);
      Serial.println("✅ NORMAL DATA SENT");
    }

    sendToBackend(voltage, current);

    counter++;
    lastTime = millis();
  }
}

void sendToBackend(float voltage, float current) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"voltage\":" + String(voltage, 1) + ",";
  payload += "\"current\":" + String(current, 1);
  payload += "}";

  Serial.println("📤 Payload:");
  Serial.println(payload);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("🤖 AI Response:");
    Serial.println(response);
  } else {
    Serial.print("❌ HTTP Error: ");
    Serial.println(httpCode);
  }

  http.end();
}