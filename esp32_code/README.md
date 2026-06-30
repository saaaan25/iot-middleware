# ESP32 - Guía Completa (2 Dispositivos)

## 📋 Arquitectura del Sistema

Este proyecto utiliza **2 ESP32 separados**:

```
┌─────────────────┐         ┌─────────────────┐
│  ESP32 WROOM-32 │         │   ESP32-S       │
│   (Solo PIR)    │         │  (Solo Cámara)   │
│                 │         │                 │
│  - Sensor PIR   │         │  - Cámara OV2640│
│  - Pin 19       │         │  - 10 fotos      │
│  - Envía eventos│────────▶│  - Recibe event_id│
└─────────────────┘  Serial └─────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Django     │
                     │  Middleware  │
                     └──────────────┘
```

## 🔧 Hardware Requerido

### Dispositivo 1: ESP32 WROOM-32 (PIR)
- ESP32 WROOM-32
- Sensor PIR (HC-SR501)
- LED 5mm + resistencia 220Ω (opcional)

### Dispositivo 2: ESP32-S (Cámara)
- ESP32-S (con cámara integrada)
- LED 5mm + resistencia 220Ω (opcional)

## 📁 Estructura de Archivos

```
esp32_code/
├── esp32_pir/              # Código para ESP32 WROOM-32 (PIR)
│   ├── esp32_pir.ino
│   └── platformio.ini
│
├── esp32_camera/           # Código para ESP32-S (Cámara)
│   ├── esp32_camera.ino
│   └── platformio.ini
│
├── esp32_cam_pir/          # (Opcional) Código combinado anterior
│   ├── esp32_cam_pir.ino
│   ├── platformio.ini
│   └── config.example.h
│
├── README.md               # Este archivo
└── QUICK_START.md          # Inicio rápido
```

## ⚙️ Configuración

### 1. ESP32 WROOM-32 (Sensor PIR)

**Conexiones:**
```
PIR VCC  → 3.3V o 5V
PIR GND  → GND
PIR OUT  → GPIO 19
LED+     → GPIO 2 (opcional)
LED-     → GND
```

**Configuración en el código:**
```cpp
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_PIR_001";
```

**Funcionamiento:**
1. Detecta movimiento con el PIR
2. Envía evento a `/api/pir/event/`
3. Recibe event_id del servidor
4. Envía event_id por serial al ESP32-S

### 2. ESP32-S (Solo Cámara)

**Conexiones:**
```
- Comunicación serial con ESP32 PIR
- TX PIR → RX Cámara
- RX Cámara → TX PIR
- GND común
```

**Configuración en el código:**
```cpp
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_CAM_001";
```

**Funcionamiento:**
1. Recibe event_id por serial desde ESP32 PIR
2. Captura 10 imágenes
3. Envía imágenes a `/api/images/upload/`
4. Recibe confirmación del servidor

## 🔄 Flujo de Comunicación

```
┌──────────────┐                    ┌──────────────┐                    ┌──────────────┐
│  ESP32 PIR   │                    │ ESP32 Cámara │                    │   Django     │
│              │                    │              │                    │  Middleware  │
└──────────────┘                    └──────────────┘                    └──────────────┘
       │                                    │                                    │
       │ 1. PIR detecta movimiento         │                                    │
       │───────────────────────────────────│                                    │
       │                                    │                                    │
       │ 2. POST /api/pir/event/           │                                    │
       │──────────────────────────────────────────────────────────────────────▶
       │                                    │                                    │
       │                                    │ 3. Recibe event_id                 │
       │                                    │◀───────────────────────────────────│
       │                                    │                                    │
       │ 4. Envía event_id por serial      │                                    │
       │───────────────────────────────────▶│                                    │
       │                                    │                                    │
       │                                    │ 5. Captura 10 imágenes             │
       │                                    │                                    │
       │                                    │ 6. POST /api/images/upload/        │
       │                                    │───────────────────────────────────▶│
       │                                    │                                    │
       │                                    │ 7. Procesa con IA                  │
       │                                    │ 8. Guarda en Supabase              │
       │                                    │                                    │
       │                                    │ 9. Respuesta con resultados        │
       │                                    │◀───────────────────────────────────│
       │                                    │                                    │
```

## 🚀 Instalación

### ESP32 WROOM-32 (PIR)

**Arduino IDE:**
1. Abrir `esp32_pir/esp32_pir.ino`
2. Herramientas → Placa → ESP32 Arduino → ESP32 Dev Module
3. Configurar WiFi y servidor
4. Subir código

**PlatformIO:**
1. Abrir carpeta `esp32_code/esp32_pir`
2. Configurar puerto en `platformio.ini`
3. Click en "Upload"

### ESP32-S (Cámara)

**Arduino IDE:**
1. Abrir `esp32_camera/esp32_camera.ino`
2. Herramientas → Placa → AI Thinker ESP32-CAM
3. Configurar WiFi y servidor
4. Subir código

**PlatformIO:**
1. Abrir carpeta `esp32_code/esp32_camera`
2. Configurar puerto en `platformio.ini`
3. Click en "Upload"

## 🔌 Conexión Serial entre ESP32

### Conexión Física:
```
ESP32 PIR (TX)  →  ESP32 Cámara (RX)
ESP32 PIR (RX)  →  ESP32 Cámara (TX)
GND             →  GND (común)
```

### Niveles de Voltaje:
- Ambos ESP32 usan 3.3V
- No necesitas conversor de nivel

## 🧪 Testing

### 1. Probar ESP32 PIR

**Monitor Serial (115200):**
```
🚀 ESP32 WROOM-32 - Sensor PIR
✓ Pines configurados
✓ WiFi conectado
✓ Sistema listo

🚨 MOVIMIENTO DETECTADO
📤 Enviando evento PIR...
✓ Respuesta: 200
✓ Evento creado: [UUID]
  Acción: capture_images
  Imágenes a capturar: 10
  Event ID para cámara: [UUID]
```

### 2. Probar ESP32 Cámara

**Monitor Serial (115200):**
```
🚀 ESP32-S - Solo Cámara
✓ Pines configurados
✓ Cámara inicializada correctamente
✓ WiFi conectado
✓ Sistema listo

✓ Event ID recibido: [UUID]
📸 Iniciando captura de imágenes
[1/10] Capturando...
✓ Imagen capturada: 45230 bytes
...
✓ Capturadas 10/10 imágenes

📤 Enviando imágenes al servidor...
✓ Respuesta: 200

🤖 IA: Guardar=Sí, Razón=Detected person with confidence 0.95
☁️  Supabase: 5 imágenes subidas
```

## 📊 Monitor Serial - Flujo Completo

### ESP32 PIR:
```
==================================================
🚀 ESP32 WROOM-32 - Sensor PIR
==================================================
✓ Pines configurados
📡 Conectando a WiFi: MiRedWiFi
✓ WiFi conectado
  IP: 192.168.1.50
✓ Sistema listo

🚨 MOVIMIENTO DETECTADO
==================================================
📤 Enviando evento PIR...
✓ Respuesta: 200
  Body: {"success":true,"event_id":"abc123","action":"capture_images","images_to_capture":10}
✓ Evento creado: abc123
  Acción: capture_images
  Imágenes a capturar: 10
  Event ID para cámara: abc123
✓ Ciclo completado
```

### ESP32 Cámara:
```
==================================================
🚀 ESP32-S - Solo Cámara
==================================================
✓ Pines configurados
✓ Cámara inicializada correctamente
✓ WiFi conectado
✓ Sistema listo

✓ Event ID recibido: abc123
📸 Iniciando captura de imágenes
==================================================

[1/10] Capturando...
✓ Imagen capturada: 45230 bytes
✓ Imagen 1 lista (45230 bytes)

[2/10] Capturando...
✓ Imagen capturada: 44891 bytes
✓ Imagen 2 lista (44891 bytes)
...

✓ Capturadas 10/10 imágenes

📤 Enviando imágenes al servidor...
✓ Respuesta: 200

🤖 IA: Guardar=Sí, Razón=Detected person with confidence 0.95
☁️  Supabase: 5 imágenes subidas
```

## 🔧 Solución de Problemas

### ESP32 PIR no detecta movimiento
- Ajustar potenciómetros del PIR
- Verificar alimentación
- Probar con LED en pin 19

### ESP32 Cámara no recibe event_id
- Verificar conexión serial (TX/RX)
- Verificar que ambos GND estén conectados
- Verificar que el PIR envíe el mensaje "EVENT:"

### Cámara no inicializa
- Verificar placa "AI Thinker ESP32-CAM"
- Verificar conexiones de cámara
- Probar con diferente cable USB

### No se envían imágenes
- Verificar URL del servidor
- Verificar que el servidor esté corriendo
- Aumentar timeout en el código

## 📝 Notas Importantes

### Comunicación Serial
- El ESP32 PIR envía: `EVENT:[event_id]\n`
- El ESP32 Cámara lee del Serial y procesa
- Ambos deben compartir GND

### Event ID
- El event_id se genera en el servidor Django
- El PIR lo recibe en la respuesta del POST
- El PIR lo envía por serial a la cámara
- La cámara lo usa para enviar las imágenes

### Modo de Operación
- **PIR**: Solo detecta y notifica
- **Cámara**: Solo captura y envía
- **Django**: Coordina y procesa

## 🎯 Ventajas de 2 ESP32 Separados

✅ **Especialización**: Cada ESP32 hace una tarea específica  
✅ **Confiabilidad**: Si uno falla, el otro sigue funcionando  
✅ **Escalabilidad**: Fácil agregar más sensores o cámaras  
✅ **Mantenimiento**: Más fácil de debuggear  
✅ **Performance**: Cada uno optimizado para su función  

## 📞 Soporte

- **Documentación completa**: `README.md` del proyecto
- **API del servidor**: `START_HERE.md`
- **Testing**: `docs/postman_collection.json`

---

**Arquitectura**: 2 ESP32 especializados  
**Comunicación**: Serial + HTTP REST  
**Estado**: Listo para producción