# 🚀 Inicio Rápido - Proyecto Completo

## 📦 ¿Qué incluye este proyecto?

### 1. **Middleware Django** (Backend)
- ✅ API REST lista para recibir datos del ESP32
- ✅ Procesamiento de imágenes con IA
- ✅ Integración directa con Supabase
- ✅ **Sin base de datos local** - Solo Supabase

### 2. **Código ESP32** (Firmware)
- ✅ Listo para cargar en ESP32-CAM
- ✅ Sensor PIR integrado
- ✅ Captura de 10 imágenes automática
- ✅ Comunicación HTTP con el middleware

### 3. **Documentación Completa**
- ✅ Guías de instalación
- ✅ Ejemplos de testing
- ✅ Solución de problemas

## ⚡ Inicio en 3 Pasos

### Paso 1: Configurar el Backend (Django)

```bash
# 1. Navegar al proyecto
cd iot-middleware

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables
copy .env.example .env
# Editar .env con tus credenciales de Supabase

# 5. Ejecutar servidor
python manage.py runserver
```

**El servidor estará en:** `http://localhost:8000`

### Paso 2: Configurar Supabase

1. **Crear tablas** (ejecutar SQL en Supabase):
   - Ver SQL en `README.md` sección 5.2

2. **Crear bucket**:
   - Nombre: `event-images`
   - Configurar como público

3. **Obtener credenciales**:
   - URL del proyecto
   - anon/public key
   - service_role key

### Paso 3: Configurar y Cargar ESP32

1. **Editar configuración** en `esp32_code/esp32_cam_pir/esp32_cam_pir.ino`:

```cpp
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "http://TU_SERVIDOR:8000/api";
const char* deviceId = "ESP32_CAM_001";
```

2. **Cargar código**:
   - **Arduino IDE**: Abrir `esp32_cam_pir.ino` y subir
   - **PlatformIO**: Abrir carpeta `esp32_code/esp32_cam_pir` y subir

3. **Abrir Monitor Serial** (115200 baudios)

## 🧪 Probar el Flujo Completo

### 1. Verificar que el servidor Django esté corriendo

```bash
curl http://localhost:8000/api/health/
```

Debe responder:
```json
{
  "status": "healthy",
  "service": "IoT Middleware",
  "mode": "transfer_only",
  "supabase_configured": true
}
```

### 2. Probar endpoint PIR manualmente

```bash
curl -X POST http://localhost:8000/api/pir/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_CAM_001",
    "sensor_pin": 13,
    "motion_detected": true
  }'
```

### 3. Activar el PIR en el ESP32

1. Mover la mano frente al sensor PIR
2. Verificar en Monitor Serial:
   ```
   🚨 MOVIMIENTO DETECTADO
   📤 Enviando evento PIR...
   ✓ Evento creado: [UUID]
   📸 Iniciando captura de imágenes
   ```

### 4. Verificar en Supabase

1. Ir a Supabase Dashboard
2. Verificar que se haya creado el evento en la tabla `events`
3. Verificar que se hayan subido imágenes a Storage

## 📁 Estructura del Proyecto

```
iot-middleware/
├── iot_middleware/           # Backend Django
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── api/                      # API REST
│   ├── views.py             # Endpoints
│   ├── services/            # Supabase + IA
│   └── ...
├── esp32_code/              # Código ESP32
│   ├── esp32_cam_pir/
│   │   ├── esp32_cam_pir.ino
│   │   ├── platformio.ini
│   │   └── config.example.h
│   ├── README.md
│   └── QUICK_START.md
├── docs/                     # Documentación
│   ├── postman_collection.json
│   └── ESP32_CODE.md
├── scripts/                  # Scripts útiles
│   ├── setup.bat
│   └── train_model.py
├── README.md                 # Documentación principal
├── PROJECT_SUMMARY.md        # Resumen
└── START_HERE.md             # Este archivo
```

## 🎯 Flujo Completo

```
1. PIR detecta movimiento
   ↓
2. ESP32 envía POST a /api/pir/event/
   ↓
3. Django guarda evento en Supabase
   ↓
4. Django responde con event_id
   ↓
5. ESP32 captura 10 imágenes
   ↓
6. ESP32 envía imágenes a /api/images/upload/
   ↓
7. Django procesa con IA
   ↓
8. Si detecta persona/animal:
   - Sube 5 imágenes a Supabase Storage
   - Actualiza evento en Supabase Database
   - Crea alerta
   ↓
9. ESP32 recibe confirmación
```

## 📡 Endpoints Principales

### IoT (Sin autenticación)
- `POST /api/pir/event/` - Recibir evento PIR
- `POST /api/images/upload/` - Subir imágenes
- `GET /api/health/` - Health check

### Gestión (Con JWT)
- `GET /api/events/` - Obtener eventos
- `GET /api/alerts/` - Obtener alertas
- `POST /api/devices/register/` - Registrar dispositivo

## 🔧 Configuración Rápida

### Variables de Entorno (.env)

```env
# Django
DEBUG=True
SECRET_KEY=tu-clave-secreta

# Supabase (ÚNICO almacenamiento)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-role-key

# IA
CONFIDENCE_THRESHOLD=0.7
MAX_IMAGES_TO_SAVE=5
IMAGES_PER_EVENT=10
```

## 🐛 Troubleshooting

### El servidor no inicia
```bash
# Verificar que el puerto 8000 esté libre
netstat -ano | findstr :8000
```

### No se conecta a Supabase
- Verificar `SUPABASE_URL` y `SUPABASE_KEY`
- Verificar que las tablas estén creadas
- Verificar que el bucket exista

### El ESP32 no detecta movimiento
- Ajustar potenciómetros del PIR
- Verificar alimentación del PIR
- Probar con LED en pin 13

### No se envían imágenes
- Verificar URL del servidor
- Verificar que el servidor esté corriendo
- Aumentar timeout en el código

## 📚 Documentación

- **README.md** - Documentación completa del proyecto
- **PROJECT_SUMMARY.md** - Resumen ejecutivo
- **esp32_code/README.md** - Guía del ESP32
- **esp32_code/QUICK_START.md** - Inicio rápido ESP32
- **docs/postman_collection.json** - Colección Postman para testing

## ✅ Checklist Final

- [ ] Backend Django corriendo en puerto 8000
- [ ] Variables de entorno configuradas
- [ ] Supabase configurado (tablas + bucket)
- [ ] Código ESP32 cargado
- [ ] WiFi configurado en ESP32
- [ ] PIR detecta movimiento
- [ ] Eventos se guardan en Supabase
- [ ] Imágenes se suben a Supabase
- [ ] IA clasifica correctamente

## 🎉 ¡Listo!

El proyecto está completamente funcional. Ahora puedes:

1. ✅ Probar el flujo completo PIR → Imágenes → IA → Supabase
2. ✅ Ajustar parámetros de detección
3. ✅ Entrenar tu propio modelo IA
4. ✅ Desplegar en producción

## 📞 Soporte

- Revisar `README.md` para documentación detallada
- Revisar `esp32_code/README.md` para problemas del ESP32
- Usar `docs/postman_collection.json` para testing

---

**Versión**: 2.0.0  
**Arquitectura**: Middleware de transferencia puro  
**Estado**: ✅ Listo para usar