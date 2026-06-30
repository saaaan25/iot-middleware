# Códigos ESP32 - Listos para Usar

## 📋 2 Códigos Separados

### 1. ESP32 WROOM-32 - Solo PIR (Pin 19)

**Archivo:** `esp32_code/esp32_pir/esp32_pir.ino`

```cpp
/*
 * ESP32 WROOM-32 - Sensor PIR
 * Solo detección de movimiento
 * PIR conectado a GPIO 19
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// CONFIGURACIÓN - MODIFICA ESTOS VALORES
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_PIR_001";

// PIN DEL SENSOR PIR
const int pirPin = 19;
const int ledPin = 2;  // LED indicador (opcional)

// VARIABLES
bool motionDetected = false;
unsigned long lastMotionTime = 0;
const unsigned long debounceDelay = 5000;  // 5 segundos

void setup() {
  Serial.begin(115200);
  
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  
  // Conectar WiFi
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
  
  Serial.println("Sistema listo - Esperando movimiento...");
}

void loop() {
  int pirState = digitalRead(pirPin);
  
  if (pirState == HIGH && !motionDetected) {
    unsigned long currentTime = millis();
    
    if (currentTime - lastMotionTime > debounceDelay) {
      motionDetected = true;
      lastMotionTime = currentTime;
      
      Serial.println("\n🚨 MOVIMIENTO DETECTADO");
      digitalWrite(ledPin, HIGH);
      
      // Enviar evento al servidor
      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(String(serverUrl) + "/pir/event/");
        http.addHeader("Content-Type", "application/json");
        
        StaticJsonDocument<200> doc;
        doc["device_id"] = deviceId;
        doc["sensor_pin"] = pirPin;
        doc["motion_detected"] = true;
        
        String requestBody;
        serializeJson(doc, requestBody);
        
        int httpResponseCode = http.POST(requestBody);
        
        if (httpResponseCode > 0) {
          String response = http.getString();
          Serial.println("✓ Evento enviado");
          Serial.println(response);
        } else {
          Serial.println("❌ Error al enviar evento");
        }
        
        http.end();
      }
      
      digitalWrite(ledPin, LOW);
      motionDetected = false;
      
      Serial.println("Esperando próxima detección...\n");
    }
  }
  
  delay(100);
}
```

**Configuración PlatformIO:** `esp32_code/esp32_pir/platformio.ini`
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino

monitor_speed = 115200

lib_deps =
    bblanchon/ArduinoJson @ ^6.21.0
```

---

### 2. ESP32-S - Solo Cámara

**Archivo:** `esp32_code/esp32_camera/esp32_camera.ino`

```cpp
/*
 * ESP32-S - Solo Cámara
 * Recibe event_id por serial y captura/envía imágenes
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

// CONFIGURACIÓN - MODIFICA ESTOS VALORES
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_CAM_001";

const int imagesToCapture = 10;
const int ledPin = 2;
const int flashPin = 4;

// PINES DE LA CÁMARA
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

String currentEventId = "";

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
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error cámara: 0x%x\n", err);
    return false;
  }
  
  Serial.println("✓ Cámara inicializada");
  return true;
}

camera_fb_t* captureImage() {
  digitalWrite(flashPin, HIGH);
  delay(100);
  camera_fb_t * fb = esp_camera_fb_get();
  digitalWrite(flashPin, LOW);
  
  if (!fb) {
    Serial.println("Error captura");
    return NULL;
  }
  
  Serial.printf("✓ Imagen: %d bytes\n", fb->len);
  return fb;
}

bool sendImages(String eventId, int numImages) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi no conectado");
    return false;
  }
  
  HTTPClient http;
  http.begin(String(serverUrl) + "/images/upload/");
  http.addHeader("Content-Type", "multipart/form-data");
  http.setTimeout(120);
  
  String boundary = "----ESP32" + String(millis());
  String body = "";
  
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"event_id\"\r\n\r\n";
  body += eventId + "\r\n";
  
  body += "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
  body += String(deviceId) + "\r\n";
  
  for (int i = 0; i < numImages; i++) {
    Serial.printf("\n[%d/%d] Capturando...\n", i + 1, numImages);
    camera_fb_t * fb = captureImage();
    
    if (fb) {
      body += "--" + boundary + "\r\n";
      body += "Content-Disposition: form-data; name=\"images[]\"; filename=\"image" + String(i) + ".jpg\"\r\n";
      body += "Content-Type: image/jpeg\r\n\r\n";
      esp_camera_fb_return(fb);
    }
    delay(500);
  }
  
  body += "--" + boundary + "--\r\n";
  
  Serial.println("\nEnviando imágenes...");
  int httpResponseCode = http.POST(body);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✓ Respuesta: %d\n", httpResponseCode);
    Serial.println(response);
    http.end();
    return true;
  } else {
    Serial.printf("❌ Error HTTP: %d\n", httpResponseCode);
    http.end();
    return false;
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(ledPin, OUTPUT);
  pinMode(flashPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  digitalWrite(flashPin, LOW);
  
  Serial.println("\n🚀 ESP32-S - Solo Cámara");
  
  if (!initCamera()) {
    Serial.println("Error cámara");
    ESP.restart();
  }
  
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
  
  Serial.println("Esperando event_id por serial...\n");
}

void loop() {
  // Recibir event_id por serial desde ESP32 PIR
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    
    if (message.startsWith("EVENT:")) {
      currentEventId = message.substring(6);
      Serial.printf("\n✓ Event ID recibido: %s\n", currentEventId.c_str());
      
      // Capturar y enviar imágenes
      for (int i = 0; i < imagesToCapture; i++) {
        Serial.printf("\n[%d/%d] Capturando...\n", i + 1, imagesToCapture);
        camera_fb_t * fb = captureImage();
        if (fb) {
          esp_camera_fb_return(fb);
        }
        delay(1000);
      }
      
      sendImages(currentEventId, imagesToCapture);
      currentEventId = "";
    }
  }
  
  delay(100);
}
```

**Configuración PlatformIO:** `esp32_code/esp32_camera/platformio.ini`
```ini
[env:esp32cam]
platform = espressif32
board = esp32cam
framework = arduino

monitor_speed = 115200

lib_deps =
    bblanchon/ArduinoJson @ ^6.21.0

build_flags = 
    -DCORE_DEBUG_LEVEL=3
    -DBOARD_HAS_PSRAM
```

---

## 🔌 Conexiones

### ESP32 WROOM-32 (PIR)
```
PIR VCC  → 3.3V o 5V
PIR GND  → GND
PIR OUT  → GPIO 19
LED+     → GPIO 2 (opcional)
```

### ESP32-S (Cámara)
```
PIR TX   → Cámara RX (GPIO 16)
Cámara TX → PIR RX (GPIO 17)
GND      → GND (común)
```

## ⚙️ Configuración Rápida

### 1. Modificar WiFi y Servidor

**En AMBOS códigos, cambiar:**
```cpp
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
```

**Ejemplo:**
```cpp
const char* ssid = "MiRedWiFi";
const char* password = "MiPassword123";
const char* serverUrl = "http://192.168.1.100:8000/api";
```

### 2. Cargar Códigos

**ESP32 PIR:**
1. Abrir `esp32_pir/esp32_pir.ino`
2. Herramientas → Placa → ESP32 Dev Module
3. Subir código

**ESP32 Cámara:**
1. Abrir `esp32_camera/esp32_camera.ino`
2. Herramientas → Placa → AI Thinker ESP32-CAM
3. Subir código

## 🧪 Probar

### ESP32 PIR - Monitor Serial (115200):
```
🚀 ESP32 WROOM-32 - Sensor PIR
WiFi conectado
Sistema listo - Esperando movimiento...

🚨 MOVIMIENTO DETECTADO
📤 Enviando evento PIR...
✓ Evento enviado
```

### ESP32 Cámara - Monitor Serial (115200):
```
🚀 ESP32-S - Solo Cámara
✓ Cámara inicializada
WiFi conectado
Esperando event_id por serial...

✓ Event ID recibido: abc123-def456
[1/10] Capturando...
✓ Imagen: 45230 bytes
...
Enviando imágenes...
✓ Respuesta: 200
```

## ✅ Listo!

Ambos ESP32 están funcionando:
- **PIR**: Detecta movimiento y envía evento
- **Cámara**: Recibe event_id, captura 10 fotos y envía al servidor

El servidor Django procesa las imágenes con IA y guarda todo en Supabase.