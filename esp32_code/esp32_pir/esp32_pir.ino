/*
 * ESP32 Dev Module (WROOM-32) - PIR + Traffic Light
 *
 * Pin map requested by user:
 * - GPIO 4  -> PIR sensor input
 * - GPIO 21 -> Yellow LED
 * - GPIO 18 -> Red LED
 * - GPIO 19 -> Green LED
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// -------------------- WIFI --------------------
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// -------------------- MIDDLEWARE --------------------
const char* apiHost = "iot-middleware-production-4aa8.up.railway.app";
const int apiPort = 443;
const char* apiBasePath = "/api";

const char* deviceId = "ESP32_PIR_001";

// -------------------- HARDWARE --------------------
const int pirPin = 4;
const int ledYellowPin = 21;
const int ledRedPin = 18;
const int ledGreenPin = 19;

// -------------------- TIMING --------------------
const unsigned long debounceMs = 5000;
const unsigned long resultTimeoutMs = 90000;
const unsigned long pollIntervalMs = 1500;
const unsigned long resultDisplayMs = 5000;

unsigned long lastTriggerMs = 0;
bool lastPirStateHigh = false;

void setTrafficLight(bool yellow, bool red, bool green) {
  digitalWrite(ledYellowPin, yellow ? HIGH : LOW);
  digitalWrite(ledRedPin, red ? HIGH : LOW);
  digitalWrite(ledGreenPin, green ? HIGH : LOW);
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("Connecting WiFi: %s\n", ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi OK. IP=%s RSSI=%d dBm\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
    return;
  }

  Serial.println("WiFi failed. Restarting in 5 seconds...");
  delay(5000);
  ESP.restart();
}

bool postJson(const String& path, const String& body, String& responseBody, int& httpCode) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  String url = String("https://") + apiHost + path;
  if (!http.begin(client, url)) {
    Serial.println("HTTP begin failed (POST)");
    return false;
  }

  http.setTimeout(15000);
  http.addHeader("Content-Type", "application/json");
  httpCode = http.POST(body);
  responseBody = http.getString();
  http.end();

  return httpCode > 0;
}

bool getJson(const String& path, String& responseBody, int& httpCode) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;
  String url = String("https://") + apiHost + path;
  if (!http.begin(client, url)) {
    Serial.println("HTTP begin failed (GET)");
    return false;
  }

  http.setTimeout(15000);
  httpCode = http.GET();
  responseBody = http.getString();
  http.end();

  return httpCode > 0;
}

bool sendPirEvent(String& eventIdOut) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["sensor_pin"] = pirPin;
  doc["motion_detected"] = true;

  String body;
  serializeJson(doc, body);

  String response;
  int httpCode = -1;
  String path = String(apiBasePath) + "/pir/event/";

  if (!postJson(path, body, response, httpCode)) {
    Serial.println("Failed to POST PIR event");
    return false;
  }

  Serial.printf("PIR event response code: %d\n", httpCode);
  if (httpCode != 200) {
    Serial.printf("Body: %s\n", response.c_str());
    return false;
  }

  StaticJsonDocument<768> res;
  DeserializationError err = deserializeJson(res, response);
  if (err) {
    Serial.printf("JSON parse error (pir/event): %s\n", err.c_str());
    return false;
  }

  bool success = res["success"] | false;
  const char* action = res["action"] | "none";
  const char* eventId = res["event_id"] | "";

  if (!success || String(action) != "capture_images" || strlen(eventId) == 0) {
    Serial.println("PIR event accepted but no capture action/event_id");
    return false;
  }

  eventIdOut = String(eventId);
  Serial.printf("Event created: %s\n", eventIdOut.c_str());
  return true;
}

// Returns: registered, unregistered, no_face, pending, timeout, error
String waitForEventResult(const String& eventId) {
  unsigned long start = millis();

  while ((millis() - start) < resultTimeoutMs) {
    String response;
    int httpCode = -1;
    String path = String(apiBasePath) + "/pir/result/?event_id=" + eventId;

    bool ok = getJson(path, response, httpCode);
    if (!ok || httpCode != 200) {
      Serial.printf("Result polling failed. code=%d\n", httpCode);
      delay(pollIntervalMs);
      continue;
    }

    StaticJsonDocument<768> res;
    DeserializationError err = deserializeJson(res, response);
    if (err) {
      Serial.printf("JSON parse error (pir/result): %s\n", err.c_str());
      delay(pollIntervalMs);
      continue;
    }

    const char* status = res["status"] | "pending";
    if (String(status) == "pending") {
      delay(pollIntervalMs);
      continue;
    }

    const char* signal = res["signal"] | "error";
    return String(signal);
  }

  return "timeout";
}

void showFinalSignal(const String& signal) {
  if (signal == "registered") {
    Serial.println("Result: REGISTERED -> GREEN");
    setTrafficLight(false, false, true);
    delay(resultDisplayMs);
    setTrafficLight(false, false, false);
    return;
  }

  if (signal == "unregistered") {
    Serial.println("Result: UNREGISTERED -> RED");
    setTrafficLight(false, true, false);
    delay(resultDisplayMs);
    setTrafficLight(false, false, false);
    return;
  }

  // no_face, timeout, error => yellow shortly, then off
  Serial.printf("Result: %s -> YELLOW then OFF\n", signal.c_str());
  setTrafficLight(true, false, false);
  delay(2000);
  setTrafficLight(false, false, false);
}

void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(pirPin, INPUT);
  pinMode(ledYellowPin, OUTPUT);
  pinMode(ledRedPin, OUTPUT);
  pinMode(ledGreenPin, OUTPUT);
  setTrafficLight(false, false, false);

  Serial.println();
  Serial.println("==================================================");
  Serial.println("ESP32 PIR + Traffic Light");
  Serial.println("Pins: PIR=4, YELLOW=21, RED=18, GREEN=19");
  Serial.println("==================================================");

  connectWiFi();
  Serial.println("System ready.");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  bool pirHigh = (digitalRead(pirPin) == HIGH);

  // Rising edge trigger + debounce
  if (pirHigh && !lastPirStateHigh) {
    unsigned long nowMs = millis();
    if (nowMs - lastTriggerMs >= debounceMs) {
      lastTriggerMs = nowMs;

      Serial.println();
      Serial.println("Motion detected. Sending PIR event...");

      // Yellow while middleware/camera workflow is in progress.
      setTrafficLight(true, false, false);

      String eventId;
      if (!sendPirEvent(eventId)) {
        showFinalSignal("error");
      } else {
        String signal = waitForEventResult(eventId);
        showFinalSignal(signal);
      }
    }
  }

  lastPirStateHigh = pirHigh;
  delay(80);
}