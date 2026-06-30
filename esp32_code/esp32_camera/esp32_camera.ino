/*
 * ESP32-S - Solo Cámara
 * Recibe event_id del ESP32 PIR y captura/envía imágenes
 * 
 * Hardware:
 * - ESP32-S (con cámara integrada)
 * 
 * Conexiones:
 * - Comunicación serial con ESP32 PIR (TX/RX)
 * - O por WiFi: recibe event_id del servidor
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

// ==================== CONFIGURACIÓN WiFi ====================
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// ==================== CONFIGURACIÓN DEL SERVIDOR ====================
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_CAM_001";

// ==================== CONFIGURACIÓN DE PINES ====================
const int ledPin = 2;         // LED indicador
const int flashPin = 4;       // Flash LED

// ==================== CONFIGURACIÓN DE CÁMARA ====================
const int imagesToCapture = 10;  // Número de imágenes a capturar

// Pines de la cámara ESP32-S
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ==================== VARIABLES GLOBALES ====================
String currentEventId = "";  // ID del evento actual
bool waitingForEvent = false;
unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 2000;  // Verificar cada 2 segundos

// ==================== FUNCIONES ====================

/**
 * Inicializa la cámara
 */
bool initCamera() {
  camera_config_t config;
  
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  config.frame_size = FRAMESIZE_SVGA;  // 800x600
  config.jpeg_quality = 10;
  config.fb_count = 2;
  
  esp_err_t err = esp_camera_init(&config);
  
  if (err != ESP_OK) {
    Serial.printf("❌ Error al inicializar cámara: 0x%x\n", err);
    return false;
  }
  
  sensor_t * s = esp_camera_sensor_get();
  s->set_brightness(s, 0);
  s->set_contrast(s, 0);
  s->set_saturation(s, 0);
  s->set_whitebal(s, 1);
  s->set_awb_gain(s, 1);
  
  Serial.println("✓ Cámara inicializada correctamente");
  return true;
}

/**
 * Conecta a WiFi
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
  } else {
    Serial.println("\n❌ Error al conectar WiFi");
    delay(5000);
    ESP.restart();
  }
}

/**
 * Captura una imagen
 */
camera_fb_t* captureImage() {
  digitalWrite(flashPin, HIGH);
  delay(100);
  
  camera_fb_t * fb = esp_camera_fb_get();
  
  digitalWrite(flashPin, LOW);
  
  if (!fb) {
    Serial.println("❌ Error al capturar imagen");
    return NULL;
  }
  
  Serial.printf("✓ Imagen capturada: %d bytes\n", fb->len);
  return fb;
}

/**
 * Envía imágenes al servidor
 */
bool sendImages(String eventId, int numImages) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi no conectado");
    return false;
  }
  
  HTTPClient http;
  
  String url = String(serverUrl) + "/images/upload/";
  
  http.begin(url);
  http.addHeader("Content-Type", "multipart/form-data");
  http.setTimeout(120);
  
  String boundary = "----ESP32Boundary" + String(millis());
  
  // Construir body multipart
  String body = "";
  
  // Agregar event_id
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"event_id\"\r\n\r\n";
  body += eventId + "\r\n";
  
  // Agregar device_id
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
  body += String(deviceId) + "\r\n";
  
  // Capturar imágenes
  for (int i = 0; i < numImages; i++) {
    Serial.printf("\n📸 [%d/%d] Capturando...\n", i + 1, numImages);
    
    camera_fb_t * fb = captureImage();
    
    if (fb) {
      // Agregar al body (simplificado)
      body += "--" + boundary + "\r\n";
      body += "Content-Disposition: form-data; name=\"images[]\"; filename=\"image" + String(i) + ".jpg\"\r\n";
      body += "Content-Type: image/jpeg\r\n\r\n";
      
      Serial.printf("✓ Imagen %d lista (%d bytes)\n", i + 1, fb->len);
      
      esp_camera_fb_return(fb);
    }
    
    delay(500);
  }
  
  body += "--" + boundary + "--\r\n";
  
  // Enviar
  Serial.println("\n📤 Enviando imágenes al servidor...");
  int httpResponseCode = http.POST(body);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✓ Respuesta: %d\n", httpResponseCode);
    Serial.printf("  Body: %s\n", response.c_str());
    
    // Parsear respuesta
    StaticJsonDocument<1000> responseDoc;
    if (deserializeJson(responseDoc, response) == DESERIALIZATION_OK) {
      if (responseDoc["success"] == true) {
        if (responseDoc.containsKey("ai_processing")) {
          JsonObject aiProcessing = responseDoc["ai_processing"];
          bool shouldSave = aiProcessing["should_save_event"];
          const char* saveReason = aiProcessing["save_reason"];
          
          Serial.printf("\n🤖 IA: Guardar=%s, Razón=%s\n", 
                        shouldSave ? "Sí" : "No", saveReason);
          
          if (shouldSave && responseDoc.containsKey("supabase")) {
            JsonObject supabase = responseDoc["supabase"];
            Serial.printf("☁️  Supabase: %d imágenes subidas\n", 
                          supabase["images_uploaded"]);
          }
        }
      }
    }
    
    http.end();
    return true;
  } else {
    Serial.printf("❌ Error HTTP: %d\n", httpResponseCode);
    http.end();
    return false;
  }
}

/**
 * Captura y envía imágenes
 */
void captureAndSendImages(String eventId) {
  Serial.println("\n" + String("=").repeat(50));
  Serial.println("📸 Iniciando captura de imágenes");
  Serial.println("=".repeat(50));
  
  int captured = 0;
  
  for (int i = 0; i < imagesToCapture; i++) {
    Serial.printf("\n[%d/%d] Capturando...\n", i + 1, imagesToCapture);
    
    camera_fb_t * fb = captureImage();
    
    if (fb) {
      captured++;
      esp_camera_fb_return(fb);
    }
    
    delay(1000);
  }
  
  Serial.printf("\n✓ Capturadas %d/%d imágenes\n", captured, imagesToCapture);
  
  if (captured > 0) {
    sendImages(eventId, captured);
  }
  
  // Limpiar event_id
  currentEventId = "";
  waitingForEvent = false;
}

/**
 * Verifica si hay nuevos eventos pendientes
 * (Consulta al servidor o recibe por serial)
 */
void checkForEvents() {
  // Aquí puedes implementar:
  // 1. Polling al servidor para verificar eventos pendientes
  // 2. Recepción por serial desde el ESP32 PIR
  // 3. MQTT subscription
  
  // Por ahora, solo verificamos si tenemos un event_id guardado
  if (waitingForEvent && currentEventId != "") {
    Serial.println("\n✓ Evento pendiente encontrado");
    captureAndSendImages(currentEventId);
  }
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(5000);
  
  Serial.println("\n" + String("=").repeat(50));
  Serial.println("🚀 ESP32-S - Solo Cámara");
  Serial.println("=".repeat(50));
  
  // Configurar pines
  pinMode(ledPin, OUTPUT);
  pinMode(flashPin, OUTPUT);
  
  digitalWrite(ledPin, LOW);
  digitalWrite(flashPin, LOW);
  
  Serial.println("✓ Pines configurados");
  
  // Inicializar cámara
  if (!initCamera()) {
    Serial.println("❌ Error crítico: Cámara no inicializada");
    delay(5000);
    ESP.restart();
  }
  
  // Conectar WiFi
  connectWiFi();
  
  Serial.println("\n✓ Sistema listo");
  Serial.println("  Esperando event_id para capturar...\n");
}

// ==================== LOOP ====================

void loop() {
  // Verificar eventos pendientes cada intervalo
  if (millis() - lastCheckTime > checkInterval) {
    lastCheckTime = millis();
    checkForEvents();
  }
  
  // También verificar por serial (desde ESP32 PIR)
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    
    // Si recibimos un event_id del ESP32 PIR
    if (message.startsWith("EVENT:")) {
      currentEventId = message.substring(6);
      waitingForEvent = true;
      
      Serial.printf("\n✓ Event ID recibido: %s\n", currentEventId.c_str());
      
      // Capturar y enviar imágenes
      captureAndSendImages(currentEventId);
    }
  }
  
  delay(100);
}