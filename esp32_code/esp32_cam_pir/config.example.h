/*
 * Archivo de configuración para ESP32-CAM + PIR
 * Copia este archivo como config.h y modifica los valores
 */

#ifndef CONFIG_H
#define CONFIG_H

// ==================== CONFIGURACIÓN WiFi ====================
#define WIFI_SSID "TU_WIFI"
#define WIFI_PASSWORD "TU_PASSWORD"

// ==================== CONFIGURACIÓN DEL SERVIDOR ====================
#define SERVER_URL "http://TU_SERVIDOR:8000/api"
#define DEVICE_ID "ESP32_CAM_001"

// ==================== CONFIGURACIÓN DE PINES ====================
#define PIR_PIN 13
#define LED_PIN 2
#define FLASH_PIN 4

// ==================== CONFIGURACIÓN DE CÁMARA ====================
#define CAMERA_FRAME_SIZE FRAMESIZE_SVGA  // 800x600
#define CAMERA_JPEG_QUALITY 10            // 0-63 (menor = mejor calidad)
#define CAMERA_FB_COUNT 2

// ==================== CONFIGURACIÓN DE CAPTURA ====================
#define IMAGES_TO_CAPTURE 10
#define DEBOUNCE_DELAY 5000  // 5 segundos entre detecciones

// ==================== CONFIGURACIÓN DE RED ====================
#define HTTP_TIMEOUT 10000      // 10 segundos
#define HTTP_UPLOAD_TIMEOUT 120 // 2 minutos para upload

#endif // CONFIG_H