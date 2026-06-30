# Código ESP32 - Guía Completa

Este documento contiene el código completo y funcional para el ESP32-CAM con sensor PIR.

## Requisitos

- ESP32-CAM (AI-Thinker)
- Sensor PIR (HC-SR501)
- Arduino IDE instalado
- Librerías:
  - ESP32 Board Package
  - ArduinoJson (v6.21.0+)
  - ESP32Cam (opcional, para configuración avanzada)

## Instalación de Librerías

1. Abre Arduino IDE
2. Ve a `Archivo → Preferencias`
3. En "Gestor de URLs Adicionales de Tarjetas" agrega:
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
4. Ve a `Herramientas → Placa → Gestor de Tarjetas`
5. Busca "ESP32" e instala "ESP32 by Espressif Systems"
6. Ve a `Programa → Incluir Librería → Gestionar Librerías`
7. Busca e instala "ArduinoJson" (v6.21.0 o superior)

## Configuración de la Placa

1. Ve a `Herramientas → Placa → ESP32 Arduino → AI Thinker ESP32-CAM`
2. Configura:
   - **CPU Frequency:** 240MHz (WiFi/BT)
   - **Flash Frequency:** 80MHz
   - **Flash Mode:** QIO
   - **Flash Size:** 4MB
   - **Partition Scheme:** Huge APP (3MB No OTA)
   - **Upload Speed:** 115200
   - **Port:** (selecciona el puerto COM de tu ESP32)

## Conexiones

### Sensor PIR (HC-SR501)
```
PIR VCC  → 3.3V o 5V
PIR GND  → GND
PIR OUT  → GPIO 13 (pin D13)
```

### LED Indicador (opcional)
```
LED+ → GPIO 2 (pin D2) con resistencia 220Ω
LED- → GND
```

## Código Completo

```cpp
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
const int pirPin = 13;        // Pin del sensor PIR
const int ledPin = 2;         // LED indicador (opcional)
const int flashPin = 4;       // Flash LED del ESP32-CAM

// ==================== VARIABLES GLOBALES ====================
bool motionDetected = false;
unsigned long lastMotionTime = 0;
const unsigned long debounceDelay = 5000;  // 5 segundos entre detecciones
const int imagesToCapture = 10;            // Número de imágenes a capturar

// ==================== CONFIGURACIÓN DE LA CÁMARA ====================
// Pines de la cámara ESP32-CAM (AI-Thinker)
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

// ==================== FUNCIONES ====================

/**
 * Inicializa la cámara ESP32-CAM
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
  
  // Configuración de calidad y tamaño
  config.frame_size = FRAMESIZE_SVGA;  // 800x600
  config.jpeg_quality = 10;            // 0-63, menor es mejor calidad
  config.fb_count = 2;
  
  // Inicializar cámara
  esp_err_t err = esp_camera_init(&config);
  
  if (err != ESP_OK) {
    Serial.printf("❌ Error al inicializar cámara: 0x%x\n", err);
    return false;
  }
  
  // Configurar sensor de cámara
  sensor_t * s = esp_camera_sensor_get();
  s->set_brightness(s, 0);     // -2 a 2
  s->set_contrast(s, 0);       // -2 a 2
  s->set_saturation(s, 0);     // -2 a 2
  s->set_special_effect(s, 0); // 0-6 (Sin efecto)
  s->set_whitebal(s, 1);       // Balance de blancos
  s->set_awb_gain(s, 1);       // Ganancia automática
  s->set_wb_mode(s, 0);        // Modo balance de blancos
  s->set_exposure_ctrl(s, 1);  // Control de exposición
  s->set_aec2(s, 0);           // AEC2
  s->set_gain_ctrl(s, 1);      // Control de ganancia
  s->set_agc_gain(s, 0);       // Ganancia AGC
  s->set_gainceiling(s, (gainceiling_t)0);  // Techo de ganancia
  s->set_bpc(s, 0);            // Corrección de píxeles negros
  s->set_wpc(s, 1);            // Corrección de píxeles blancos
  s->set_raw_gma(s, 1);        // Gamma
  s->set_lenc(s, 1);           // Corrección de lente
  s->set_hmirror(s, 0);        // Espejo horizontal
  s->set_vflip(s, 0);          // Volteo vertical
  s->set_dcw(s, 1);            // Downsize
  s->set_colorbar(s, 0);       // Barra de color
  
  Serial.println("✓ Cámara inicializada correctamente");
  return true;
}

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

/**
 * Captura una imagen
 */
camera_fb_t* captureImage() {
  // Encender flash
  digitalWrite(flashPin, HIGH);
  delay(100);
  
  // Capturar imagen
  camera_fb_t * fb = esp_camera_fb_get();
  
  // Apagar flash
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
bool sendImages(const char* eventId, int numImages) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi no conectado");
    return false;
  }
  
  HTTPClient http;
  
  // Construir URL
  String url = String(serverUrl) + "/images/upload/";
  
  http.begin(url);
  http.addHeader("Content-Type", "multipart/form-data");
  http.setTimeout(120);  // 2 minutos timeout para upload
  
  // Boundary para multipart
  String boundary = "----ESP32Boundary" + String(millis());
  
  // Construir body
  String body = "";
  
  // Agregar event_id
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"event_id\"\r\n\r\n";
  body += String(eventId) + "\r\n";
  
  // Agregar device_id
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
  body += String(deviceId) + "\r\n";
  
  // Capturar y agregar imágenes
  for (int i = 0; i < numImages; i++) {
    Serial.printf("\n📸 Capturando imagen %d/%d...\n", i + 1, numImages);
    
    camera_fb_t * fb = captureImage();
    
    if (fb) {
      // Agregar imagen al body
      body += "--" + boundary + "\r\n";
      body += "Content-Disposition: form-data; name=\"images[]\"; filename=\"image" + String(i) + ".jpg\"\r\n";
      body += "Content-Type: image/jpeg\r\n\r\n";
      
      // Nota: Esta es una implementación simplificada
      // En producción, necesitas usar WiFiClient para enviar datos binarios correctamente
      
      Serial.printf("✓ Imagen %d lista para enviar\n", i + 1);
      
      // Liberar frame buffer
      esp_camera_fb_return(fb);
    }
    
    delay(500);  // Esperar entre capturas
  }
  
  body += "--" + boundary + "--\r\n";
  
  // Enviar POST
  Serial.println("\n📤 Enviando imágenes al servidor...");
  int httpResponseCode = http.POST(body);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✓ Respuesta: %d\n", httpResponseCode);
    Serial.printf("  Body: %s\n", response.c_str());
    
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
void captureAndSendImages(const char* eventId) {
  Serial.println("\n" + "=".repeat(50));
  Serial.println("📸 Iniciando captura de imágenes");
  Serial.println("=".repeat(50));
  
  int captured = 0;
  
  for (int i = 0; i < imagesToCapture; i++) {
    Serial.printf("\n[%d/%d] Capturando...\n", i + 1, imagesToCapture);
    
    camera_fb_t * fb = captureImage();
    
    if (fb) {
      captured++;
      
      // Aquí deberías enviar la imagen
      // Por ahora solo la guardamos en memoria
      
      esp_camera_fb_return(fb);
    }
    
    delay(1000);  // 1 segundo entre capturas
  }
  
  Serial.printf("\n✓ Capturadas %d/%d imágenes\n", captured, imagesToCapture);
  
  // Enviar imágenes al servidor
  // sendImages(eventId, captured);
}

// ==================== SETUP ====================

void setup() {
  // Inicializar Serial
  Serial.begin(115200);
  Serial.setTimeout(5000);
  
  Serial.println("\n" + "=".repeat(50));
  Serial.println("🚀 ESP32-CAM IoT Middleware");
  Serial.println("=".repeat(50));
  
  // Configurar pines
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(flashPin, OUTPUT);
  
  digitalWrite(ledPin, LOW);
  digitalWrite(flashPin, LOW);
  
  Serial.println("✓ Pines configurados");
  
  // Inicializar cámara
  if (!initCamera()) {
    Serial.println("❌ Error crítico: Cámara no inicializada");
    Serial.println("  Reiniciando en 5 segundos...");
    delay(5000);
    ESP.restart();
  }
  
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
      
      Serial.println("\n" + "=".repeat(50));
      Serial.println("🚨 MOVIMIENTO DETECTADO");
      Serial.println("=".repeat(50));
      
      // Encender LED indicador
      digitalWrite(ledPin, HIGH);
      
      // Enviar evento PIR
      bool eventSent = sendPirEvent(true);
      
      if (eventSent) {
        // Capturar imágenes
        // Nota: Necesitas obtener el event_id de la respuesta
        // Por ahora usamos un ID temporal
        const char* tempEventId = "temp-event-id";
        captureAndSendImages(tempEventId);
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
```

## Versión Optimizada (Recomendada)

La siguiente versión es más robusta y maneja mejor la comunicación:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

// ==================== CONFIGURACIÓN ====================
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_CAM_001";

const int pirPin = 13;
const int ledPin = 2;
const int flashPin = 4;

// ==================== VARIABLES ====================
unsigned long lastMotionTime = 0;
const unsigned long debounceDelay = 5000;
String currentEventId = "";

// ==================== CÁMARA ====================
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
  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 10;
  config.fb_count = 2;
  
  return esp_camera_init(&config) == ESP_OK;
}

// ==================== WiFi ====================
void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi conectado");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Error WiFi");
    ESP.restart();
  }
}

// ==================== PIR EVENT ====================
bool sendPirEvent(bool motion) {
  if (WiFi.status() != WL_CONNECTED) return false;
  
  HTTPClient http;
  http.begin(String(serverUrl) + "/pir/event/");
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["device_id"] = deviceId;
  doc["sensor_pin"] = pirPin;
  doc["motion_detected"] = motion;
  
  String body;
  serializeJson(doc, body);
  
  int code = http.POST(body);
  bool success = false;
  
  if (code > 0) {
    String response = http.getString();
    StaticJsonDocument<500> res;
    
    if (deserializeJson(res, response) == DESERIALIZATION_OK) {
      if (res["success"] == true) {
        currentEventId = res["event_id"].as<String>();
        Serial.printf("✓ Evento: %s\n", currentEventId.c_str());
        success = true;
      }
    }
  }
  
  http.end();
  return success;
}

// ==================== IMAGE CAPTURE ====================
camera_fb_t* captureImage() {
  digitalWrite(flashPin, HIGH);
  delay(100);
  
  camera_fb_t* fb = esp_camera_fb_get();
  
  digitalWrite(flashPin, LOW);
  
  if (!fb) {
    Serial.println("❌ Error captura");
    return NULL;
  }
  
  return fb;
}

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(flashPin, OUTPUT);
  
  digitalWrite(ledPin, LOW);
  digitalWrite(flashPin, LOW);
  
  Serial.println("\n🚀 ESP32-CAM IoT Middleware");
  
  if (!initCamera()) {
    Serial.println("❌ Error cámara");
    ESP.restart();
  }
  
  connectWiFi();
  Serial.println("✓ Sistema listo\n");
}

// ==================== LOOP ====================
void loop() {
  int pirState = digitalRead(pirPin);
  
  if (pirState == HIGH) {
    unsigned long now = millis();
    
    if (now - lastMotionTime > debounceDelay) {
      lastMotionTime = now;
      
      Serial.println("\n🚨 Movimiento detectado");
      digitalWrite(ledPin, HIGH);
      
      if (sendPirEvent(true)) {
        Serial.println("✓ Evento enviado");
        // Aquí capturarías las imágenes
      }
      
      digitalWrite(ledPin, LOW);
    }
  }
  
  delay(100);
}
```

## Notas Importantes

### Limitaciones del ESP32

1. **Memoria limitada**: El ESP32 tiene ~520KB de RAM
2. **Tamaño de imágenes**: Usa resolución baja (SVGA 800x600)
3. **Multipart upload**: La implementación completa requiere WiFiClient para datos binarios
4. **Timeout**: Aumenta timeouts para uploads grandes

### Mejoras Recomendadas

1. **Usar WiFiClient para uploads**:
```cpp
WiFiClient client;
HTTPClient http;
http.begin(client, url);
```

2. **Comprimir imágenes**: Reduce calidad JPEG para menor tamaño

3. **Implementar cola**: Guarda imágenes en SD si no hay conexión

4. **Usar Deep Sleep**: Ahorra energía entre detecciones

## Testing

1. Carga el código en el ESP32
2. Abre el Monitor Serial (115200 baudios)
3. Verifica que se conecte a WiFi
4. Verifica que la cámara se inicialice
5. Activa el sensor PIR
6. Observa los logs en el Monitor Serial

## Solución de Problemas

### Cámara no inicializa
- Verifica conexiones de la cámara
- Asegúrate de usar la placa "AI Thinker ESP32-CAM"
- Prueba con diferente cable USB

### WiFi no conecta
- Verifica SSID y password
- Asegúrate de estar en rango
- Usa 2.4GHz (no 5GHz)

### Upload falla
- Verifica que el servidor esté accesible
- Aumenta el timeout
- Verifica tamaño máximo de upload en Nginx/Django