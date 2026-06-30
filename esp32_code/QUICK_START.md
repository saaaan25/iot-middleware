# Inicio Rápido - 2 ESP32 (PIR + Cámara)

## ⚡ Configuración en 5 Pasos

### 1. 📦 Hardware (2 Dispositivos)

**Dispositivo 1 - PIR:**
```
✅ ESP32 WROOM-32
✅ Sensor PIR (HC-SR501)
✅ LED + resistencia 220Ω (opcional)
```

**Dispositivo 2 - Cámara:**
```
✅ ESP32-S (con cámara)
✅ LED + resistencia 220Ω (opcional)
```

### 2. 🔌 Conexiones

**ESP32 PIR:**
```
PIR VCC  → 3.3V o 5V
PIR GND  → GND
PIR OUT  → GPIO 19
LED+     → GPIO 2 (opcional)
```

**ESP32 Cámara:**
```
PIR TX   → Cámara RX (GPIO 16)
Cámara TX → PIR RX (GPIO 17)
GND      → GND (común)
```

### 3. ⚙️ Configuración (2 minutos)

**ESP32 PIR** (`esp32_pir/esp32_pir.ino`):
```cpp
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_PIR_001";
```

**ESP32 Cámara** (`esp32_camera/esp32_camera.ino`):
```cpp
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_CAM_001";
```

### 4. 🚀 Cargar Códigos

**ESP32 PIR:**
1. Abrir `esp32_pir/esp32_pir.ino`
2. Herramientas → Placa → ESP32 Dev Module
3. Subir código
4. Abrir Monitor Serial (115200)

**ESP32 Cámara:**
1. Abrir `esp32_camera/esp32_camera.ino`
2. Herramientas → Placa → AI Thinker ESP32-CAM
3. Subir código
4. Abrir Monitor Serial (115200)

### 5. 🧪 Probar Flujo

1. **Mover mano frente al PIR:**
```
ESP32 PIR:
🚨 MOVIMIENTO DETECTADO
📤 Enviando evento PIR...
✓ Evento creado: [UUID]
  Event ID para cámara: [UUID]
```

2. **ESP32 Cámara recibe y captura:**
```
ESP32 Cámara:
✓ Event ID recibido: [UUID]
📸 Iniciando captura de imágenes
[1/10] Capturando...
✓ Imagen capturada: 45230 bytes
...
✓ Capturadas 10/10 imágenes
```

3. **Verificar en Supabase:**
- Evento creado en tabla `events`
- Imágenes subidas a Storage
- Alerta creada

## 📊 Flujo Completo

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  ESP32 PIR   │      │ ESP32 Cámara │      │   Django     │
│              │      │              │      │  Middleware  │
└──────────────┘      └──────────────┘      └──────────────┘
       │                     │                     │
       │ 1. Detecta movimiento│                     │
       │────────────────────▶│                     │
       │                     │                     │
       │ 2. POST /api/pir/event/                   │
       │──────────────────────────────────────────▶│
       │                     │                     │
       │                     │ 3. Recibe event_id  │
       │                     │◀────────────────────│
       │                     │                     │
       │ 4. Envía event_id   │                     │
       │────────────────────▶│                     │
       │                     │                     │
       │                     │ 5. Captura 10 fotos │
       │                     │                     │
       │                     │ 6. POST /api/images/upload/
       │                     │────────────────────▶│
       │                     │                     │
       │                     │ 7. Procesa con IA   │
       │                     │ 8. Guarda en Supabase│
       │                     │                     │
       │                     │ 9. Respuesta        │
       │                     │◀────────────────────│
```

## ✅ Checklist

- [ ] ESP32 PIR conectado y funcionando
- [ ] ESP32 Cámara conectado y funcionando
- [ ] Ambos con WiFi configurado
- [ ] Conexión serial entre ambos (TX/RX/GND)
- [ ] Servidor Django corriendo
- [ ] Supabase configurado (tablas + bucket)
- [ ] PIR detecta movimiento
- [ ] Cámara recibe event_id
- [ ] Imágenes se capturan y envían
- [ ] Datos aparecen en Supabase

## 🐛 Problemas Comunes

| Problema | Solución |
|----------|----------|
| PIR no detecta | Ajustar potenciómetros, verificar pin 19 |
| Cámara no recibe event_id | Verificar TX/RX, GND común |
| No envía imágenes | Verificar URL servidor, timeout |
| WiFi no conecta | Verificar SSID, usar 2.4GHz |

## 📞 Soporte

- **Guía completa**: `esp32_code/README.md`
- **API**: `START_HERE.md`
- **Testing**: `docs/postman_collection.json`

---

**Tiempo**: 15-20 minutos  
**Dificultad**: Media  
**Estado**: Listo para producción