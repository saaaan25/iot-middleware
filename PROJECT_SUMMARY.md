# Resumen del Proyecto IoT Middleware

## 📋 Descripción General

**Middleware de transferencia puro** desarrollado en Django que actúa como puente entre dispositivos ESP32 y Supabase. **No tiene base de datos local** - todos los datos se envían directamente a Supabase.

## 🏗️ Arquitectura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   ESP32     │─────▶│   Django     │─────▶│  Supabase   │
│   PIR       │      │  Middleware  │      │  (Storage + │
│             │      │  (Transfer)  │      │   Database) │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │
       │                     │
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│ ESP32-CAM   │      │  AI Model    │
│ (10 fotos)  │      │  (PyTorch)   │
└─────────────┘      └──────────────┘
```

## 📁 Estructura del Proyecto

```
iot-middleware/
├── iot_middleware/           # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py           # Sin base de datos local
│   ├── urls.py               # URLs del proyecto
│   ├── wsgi.py              # WSGI para producción
│   └── asgi.py              # ASGI para async
│
├── api/                      # Aplicación principal
│   ├── __init__.py
│   ├── models.py            # Solo referencia (no se usan)
│   ├── serializers.py       # No necesarios (sin BD local)
│   ├── views.py             # Endpoints que transfieren a Supabase
│   ├── urls.py              # URLs de la API
│   └── services/
│       ├── __init__.py
│       ├── supabase_service.py  # Integración con Supabase
│       └── ai_service.py        # Procesamiento de imágenes IA
│
├── scripts/                  # Scripts útiles
│   ├── setup.sh             # Setup para Linux/Mac
│   ├── setup.bat            # Setup para Windows
│   └── train_model.py       # Entrenamiento de modelo IA
│
├── docs/                     # Documentación
│   ├── postman_collection.json  # Colección Postman
│   └── ESP32_CODE.md        # Código para ESP32
│
├── models/                   # Directorio de modelos IA
│   └── README.md
│
├── nginx/                    # Configuración Nginx
│   └── nginx.conf
│
├── media/                    # Almacenamiento temporal (se limpia)
│   └── .gitkeep
│
├── manage.py                 # CLI de Django
├── requirements.txt          # Dependencias Python
├── .env.example             # Variables de entorno ejemplo
├── .gitignore               # Archivos a ignorar
├── .dockerignore            # Archivos Docker a ignorar
├── Dockerfile               # Imagen Docker
├── docker-compose.yml       # Orquestación Docker
├── README.md                # Documentación principal
└── PROJECT_SUMMARY.md       # Este archivo
```

## 🔑 Características Principales

### 1. **Middleware de Transferencia Puro**
- ❌ NO tiene base de datos local
- ✅ Solo transfiere datos a Supabase
- ✅ Procesa imágenes temporalmente (se eliminan después)
- ✅ Sin migraciones de Django
- ✅ Sin ORM de Django

### 2. **API REST Completa**
- Endpoints sin autenticación para ESP32
- Endpoints con autenticación JWT para gestión
- Validación de datos
- Manejo de errores robusto

### 3. **Integración con Supabase**
- **Storage**: Almacena imágenes (5 por evento)
- **Database**: Guarda eventos y alertas
- Cliente Supabase configurado
- Único almacenamiento de datos

### 4. **Procesamiento IA**
- Clasificación de imágenes con PyTorch
- Modelo dummy incluido para testing
- Soporte para modelos personalizados
- Configuración de confianza ajustable
- Selección de mejores imágenes

### 5. **Flujo de Trabajo**

```
1. PIR detecta movimiento
   ↓
2. ESP32 envía POST a /api/pir/event/
   ↓
3. Middleware guarda evento en Supabase
   ↓
4. Middleware responde con event_id
   ↓
5. ESP32 captura 10 imágenes
   ↓
6. ESP32 envía imágenes a /api/images/upload/
   ↓
7. IA clasifica las imágenes (temporalmente)
   ↓
8. Si confianza > 70% y es persona/animal:
   - Guarda 5 mejores imágenes en Supabase Storage
   - Actualiza evento en Supabase Database
   - Crea alerta en Supabase
   - Elimina imágenes temporales
```

## 🚀 Inicio Rápido

### Opción 1: Setup Automático (Windows)

```bash
# Doble clic en
scripts/setup.bat
```

### Opción 2: Setup Manual

```bash
# 1. Clonar/descargar proyecto
cd iot-middleware

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables
copy .env.example .env
# Editar .env con tus configuraciones de Supabase

# 5. Configurar Supabase
# - Crear tablas (SQL en README.md)
# - Crear bucket 'event-images'

# 6. Ejecutar servidor
python manage.py runserver
```

### Opción 3: Docker

```bash
# 1. Configurar variables de entorno
copy .env.example .env
# Editar .env

# 2. Iniciar servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f
```

## 📡 Endpoints Principales

### IoT (Sin autenticación)

```http
POST /api/pir/event/          # Recibir evento PIR
POST /api/images/upload/      # Subir imágenes
GET  /api/health/             # Health check
```

### Gestión (Con JWT)

```http
POST /api/token/              # Obtener token JWT
GET  /api/events/             # Obtener eventos desde Supabase
GET  /api/alerts/             # Obtener alertas desde Supabase
POST /api/devices/register/   # Registrar dispositivo
POST /api/sensors/register/   # Registrar sensor
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Django
DEBUG=True
SECRET_KEY=tu-clave-secreta
ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase (ÚNICO almacenamiento)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-role-key

# IA
MODEL_PATH=models/best_model.pth
CONFIDENCE_THRESHOLD=0.7
MAX_IMAGES_TO_SAVE=5
IMAGES_PER_EVENT=10

# Media (Temporal)
MEDIA_ROOT=media
MEDIA_URL=/media/
```

## 🔧 Configuración de Supabase

### 1. Crear Tablas

Ejecuta el SQL proporcionado en `README.md` en el SQL Editor de Supabase.

### 2. Crear Bucket

1. Ve a Storage → Create bucket
2. Nombre: `event-images`
3. Configurar como público

### 3. Obtener Credenciales

1. Ve a Settings → API
2. Copia:
   - Project URL
   - anon/public key
   - service_role key

## 🤖 Modelo IA

### Usar Modelo Dummy (Testing)

No requiere configuración. Se usa automáticamente si no existe `models/best_model.pth`.

### Entrenar Modelo Propio

```bash
# 1. Preparar dataset
dataset/
├── train/
│   ├── person/
│   ├── animal/
│   ├── vehicle/
│   └── other/
└── val/
    ├── person/
    ├── animal/
    ├── vehicle/
    └── other/

# 2. Entrenar
python scripts/train_model.py --data-dir ./dataset --epochs 20

# 3. El modelo se guarda en models/best_model.pth
```

### Clases del Modelo

Por defecto:
- `person` - Personas
- `animal` - Animales
- `vehicle` - Vehículos
- `other` - Otros

Para cambiar, modificar `class_names` en `api/services/ai_service.py`.

## 🧪 Testing

### Probar PIR Event

```bash
curl -X POST http://localhost:8000/api/pir/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_CAM_001",
    "sensor_pin": 13,
    "motion_detected": true
  }'
```

### Probar Health Check

```bash
curl http://localhost:8000/api/health/
```

### Usar Postman

Importar `docs/postman_collection.json` en Postman.

## 📊 Flujo de Datos

### Evento PIR

1. **ESP32 → Django**
   ```json
   POST /api/pir/event/
   {
     "device_id": "ESP32_CAM_001",
     "sensor_pin": 13,
     "motion_detected": true
   }
   ```

2. **Django → Supabase**
   ```json
   {
     "type": "motion_detected",
     "value": "{...}",
     "sensor_id": "uuid",
     "event_date": "2024-..."
   }
   ```

3. **Django → ESP32**
   ```json
   {
     "success": true,
     "event_id": "uuid",
     "action": "capture_images",
     "images_to_capture": 10
   }
   ```

### Upload de Imágenes

1. **ESP32 → Django** (temporal)
   ```
   POST /api/images/upload/
   Content-Type: multipart/form-data
   ```

2. **Django procesa**:
   - Guarda temporalmente en `/media/temp`
   - Clasifica con IA
   - Selecciona mejores 5 imágenes

3. **Django → Supabase**:
   - Sube imágenes a Storage
   - Actualiza evento en Database
   - Crea alerta

4. **Django limpia**:
   - Elimina imágenes temporales

5. **Django → ESP32**
   ```json
   {
     "success": true,
     "ai_processing": {...},
     "supabase": {
       "event_updated": true,
       "images_uploaded": 5
     }
   }
   ```

## 🐛 Solución de Problemas

### Error de Conexión a Supabase

- Verificar `SUPABASE_URL` y `SUPABASE_KEY`
- Asegurar que el bucket existe
- Verificar que las tablas estén creadas

### Modelo IA no Carga

- El sistema usa modelo dummy automáticamente
- Verificar ruta en `MODEL_PATH`

### Error CORS

- Verificar `CORS_ALLOWED_ORIGINS` en settings.py

## 📦 Dependencias Principales

- **Django 4.2.7**: Framework web
- **Django REST Framework 3.14.0**: API REST
- **PyTorch 2.1.1**: Procesamiento IA
- **Supabase 1.0.3**: Cliente Supabase
- **Pillow 10.1.0**: Procesamiento de imágenes

## 🔒 Seguridad

- Endpoints IoT sin autenticación (considerar API Key en producción)
- Endpoints de gestión con JWT
- CORS configurado
- Variables de entorno para credenciales
- **No hay base de datos local** - Solo Supabase

## 📈 Escalabilidad

### Producción

1. **Servidor WSGI**: Gunicorn/uWSGI
2. **Cache**: Redis para modelos IA
3. **Colas**: Celery + Redis para procesamiento async de imágenes
4. **Monitoreo**: Sentry, Prometheus
5. **HTTPS**: Configurar SSL/TLS

### Mejoras Futuras

- [ ] Cola de tareas async (Celery) para procesamiento de imágenes
- [ ] Cache de modelos IA en memoria
- [ ] WebSocket para notificaciones en tiempo real
- [ ] Dashboard web para monitoreo
- [ ] App móvil
- [ ] Soporte para múltiples modelos IA
- [ ] Detección de objetos (YOLO)
- [ ] Reconocimiento facial
- [ ] Alertas push notification

## 📝 Notas Importantes

1. **Sin base de datos local**: Este middleware NO guarda datos en PostgreSQL/SQLite. Todo se envía directamente a Supabase.

2. **Almacenamiento temporal**: Las imágenes se guardan temporalmente en `/media/temp` solo para procesamiento con IA, luego se eliminan automáticamente.

3. **Modelos de referencia**: Los modelos en `api/models.py` son solo para documentación de la estructura de Supabase, no se usan en el middleware.

4. **Supabase es la única fuente de verdad**: Todos los datos (eventos, alertas, imágenes) se almacenan en Supabase.

5. **Procesamiento síncrono**: El procesamiento de imágenes es síncrono. Para producción con alto volumen, considerar colas async.

## 🎯 Próximos Pasos

1. Configurar Supabase (tablas + bucket)
2. Configurar variables de entorno
3. (Opcional) Entrenar modelo IA
4. Probar endpoints con Postman
5. Cargar código en ESP32
6. Probar flujo completo

## 📞 Soporte

Para preguntas o issues, consultar:
- README.md para documentación detallada
- docs/ESP32_CODE.md para código ESP32
- docs/postman_collection.json para testing API

---

**Versión**: 2.0.0  
**Arquitectura**: Middleware de transferencia puro  
**Base de Datos Local**: ❌ No  
**Almacenamiento**: ✅ Supabase únicamente  
**Estado**: Listo para desarrollo y producción