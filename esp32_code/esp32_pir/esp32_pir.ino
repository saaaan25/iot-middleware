/*
 * ESP32 WROOM-32 - Sensor PIR
 * Solo detección de movimiento - Sin cámara
 * 
 * Hardware:
 * - ESP32 WROOM-32
 * - Sensor PIR (HC-SR501)
 * 
 * Conexiones:
 * PIR VCC  → 3.3V o 5V
 * PIR GND  → GND
 * PIR OUT  → GPIO 19
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN WiFi ====================
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// ==================== CONFIGURACIÓN DEL SERVIDOR ====================
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_PIR_001";

// ==================== CONFIGURACIÓN DE PINES ====================
const int pirPin = 19;        // Pin del sensor PIR
const int ledPin = 2;         // LED indicador (opcional)

// ==================== VARIABLES GLOBALES ====================
bool motionDetected = false;
unsigned long lastMotionTime = 0;
const unsigned long debounceDelay = 5000;  // 5 segundos entre detecciones

// ==================== FUNCIONES ====================

/**
 * Conecta a la red WiFi
 */
void connectWiFi() {
  Serial.printf("\n📡 Conectando a WiFi: %s\n", ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi conectado");
    Serial.printf("  IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("  Señal: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\n❌ Error al conectar WiFi");
    Serial.println("  Reiniciando en 5 segundos...");
    delay(5000);
    ESP.restart();
  }
}

/**
 * Envía evento PIR al servidor
 */
bool sendPirEvent(bool motionDetected) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi no conectado");
    return false;
  }
  
  HTTPClient http;
  
  // Construir URL
  String url = String(serverUrl) + "/pir/event/";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  // 10 segundos timeout
  
  // Crear JSON
  StaticJsonDocument<200> doc;
  doc["device_id"] = deviceId;
  doc["sensor_pin"] = pirPin;
  doc["motion_detected"] = motionDetected;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  // Enviar POST
  Serial.printf("📤 Enviando evento PIR...\n");
  int httpResponseCode = http.POST(requestBody);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✓ Respuesta: %d\n", httpResponseCode);
    Serial.printf("  Body: %s\n", response.c_str());
    
    // Parsear respuesta
    StaticJsonDocument<500> responseDoc;
    if (deserializeJson(responseDoc, response) == DESERIALIZATION_OK) {
      if (responseDoc["success"] == true) {
        const char* eventId = responseDoc["event_id"];
        const char* action = responseDoc["action"];
        
        Serial.printf("✓ Evento creado: %s\n", eventId);
        Serial.printf("  Acción: %s\n", action);
        
        // Si la acción es capturar imágenes, guardar event_id
        if (strcmp(action, "capture_images") == 0) {
          int imagesToCapture = responseDoc["images_to_capture"];
          Serial.printf("  Imágenes a capturar: %d\n", imagesToCapture);
          
          // Guardar event_id en EEPROM o preferences para que la cámara lo use
          // Por ahora solo lo imprimimos
          Serial.printf("  Event ID para cámara: %s\n", eventId);
        }
        
        http.end();
        return true;
      }
    }
  } else {
    Serial.printf("❌ Error HTTP: %d\n", httpResponseCode);
  }
  
  http.end();
  return false;
}

// ==================== SETUP ====================

void setup() {
  // Inicializar Serial
  Serial.begin(115200);
  Serial.setTimeout(5000);
  
  Serial.println("\n" + String("=").repeat(50));
  Serial.println("🚀 ESP32 WROOM-32 - Sensor PIR");
  Serial.println("=".repeat(50));
  
  // Configurar pines
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  
  digitalWrite(ledPin, LOW);
  
  Serial.println("✓ Pines configurados");
  
  // Conectar WiFi
  connectWiFi();
  
  Serial.println("\n✓ Sistema listo");
  Serial.println("  Esperando detección de movimiento...\n");
}

// ==================== LOOP ====================

void loop() {
  // Leer sensor PIR
  int pirState = digitalRead(pirPin);
  
  // Detectar movimiento
  if (pirState == HIGH && !motionDetected) {
    unsigned long currentTime = millis();
    
    // Verificar debounce
    if (currentTime - lastMotionTime > debounceDelay) {
      motionDetected = true;
      lastMotionTime = currentTime;
      
      Serial.println("\n" + String("=").repeat(50));
      Serial.println("🚨 MOVIMIENTO DETECTADO");
      Serial.println("=".repeat(50));
      
      // Encender LED indicador
      digitalWrite(ledPin, HIGH);
      
      // Enviar evento PIR
      bool eventSent = sendPirEvent(true);
      
      if (!eventSent) {
        Serial.println("❌ No se pudo enviar el evento");
      }
      
      // Apagar LED indicador
      digitalWrite(ledPin, LOW);
      
      motionDetected = false;
      
      Serial.println("\n✓ Ciclo completado");
      Serial.println("  Esperando próxima detección...\n");
    }
  }
  
  delay(100);  // Pequeño delay para estabilidad
}