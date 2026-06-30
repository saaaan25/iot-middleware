# IoT Middleware - Django + ESP32 + Supabase

**Middleware de transferencia puro** - Sin base de datos local. Todos los datos se envían directamente a Supabase.

## 🏗️ Arquitectura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   ESP32     │────▶│   Django     │─────▶│  Supabase   │
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

## ⚡ Características

- ✅ **Middleware puro** - Sin base de datos local
- ✅ API REST con Django REST Framework
- ✅ Endpoints sin autenticación para ESP32
- ✅ Procesamiento de imágenes con PyTorch
- ✅ Integración directa con Supabase (Storage + Database)
- ✅ Modelo de IA incluido (dummy para testing)
- ✅ CORS configurado para desarrollo
- ✅ Logging completo
- ✅ Modelos de referencia alineados con Supabase

## 📋 Requisitos

- Python 3.8+
- Supabase account
- ESP32 con sensores PIR y Cámara
- (Opcional) PostgreSQL solo para desarrollo/testing

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
cd iot-middleware
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**Editar `.env` con tus configuraciones:**

```env
# Django
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase (ÚNICO almacenamiento de datos)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-role-key

# AI Model
MODEL_PATH=models/best_model.pth
CONFIDENCE_THRESHOLD=0.7
MAX_IMAGES_TO_SAVE=5
IMAGES_PER_EVENT=10

# Media (Temporal - solo para procesamiento)
MEDIA_ROOT=media
MEDIA_URL=/media/
```

### 5. Configurar Supabase

#### 5.1 Crear proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Crea un nuevo proyecto
3. Anota la URL y las claves (Settings → API)

#### 5.2 Crear tablas en Supabase

Ejecuta este SQL en el SQL Editor de Supabase:

```sql
-- Tabla de perfiles (usuarios)
CREATE TABLE public.profiles (
  id uuid NOT NULL,
  name character varying NOT NULL,
  last_name character varying NOT NULL,
  phone character varying NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  role character varying NOT NULL DEFAULT 'user'::character varying,
  CONSTRAINT profiles_pkey PRIMARY KEY (id),
  CONSTRAINT profile_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);

-- Tabla de dispositivos
CREATE TABLE public.devices (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  address character varying NOT NULL,
  ubication character varying NOT NULL,
  status boolean NOT NULL DEFAULT true,
  user_id uuid,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT devices_pkey PRIMARY KEY (id),
  CONSTRAINT devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Tabla de sensores
CREATE TABLE public.sensors (
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  name character varying NOT NULL,
  type character varying NOT NULL,
  pin bigint NOT NULL,
  status boolean NOT NULL DEFAULT true,
  device_id uuid,
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  CONSTRAINT sensors_pkey PRIMARY KEY (id),
  CONSTRAINT sensors_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id)
);

-- Tabla de eventos
CREATE TABLE public.events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  type character varying NOT NULL,
  value text,
  sensor_id uuid NOT NULL,
  event_date timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT events_pkey PRIMARY KEY (id),
  CONSTRAINT events_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensors(id)
);

-- Tabla de alertas
CREATE TABLE public.alerts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL DEFAULT gen_random_uuid(),
  message text NOT NULL,
  status character varying NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT alerts_pkey PRIMARY KEY (id),
  CONSTRAINT alerts_id_fkey FOREIGN KEY (id) REFERENCES public.events(id)
);
```

#### 5.3 Crear bucket de Storage

1. Ve a Storage en Supabase
2. Crea un nuevo bucket llamado `event-images`
3. Configura como público (para acceso a las imágenes)

### 6. Ejecutar servidor

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## 📡 Endpoints API

### Endpoints IoT (Sin autenticación)

#### 1. Recibir evento PIR

```http
POST /api/pir/event/
Content-Type: application/json

{
    "device_id": "ESP32_CAM_001",
    "sensor_pin": 13,
    "motion_detected": true,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**Respuesta:**
```json
{
    "success": true,
    "event_id": "uuid-del-evento-en-supabase",
    "action": "capture_images",
    "message": "Motion detected. Please capture images.",
    "images_to_capture": 10
}
```

#### 2. Subir imágenes

```http
POST /api/images/upload/
Content-Type: multipart/form-data

event_id: uuid-del-evento
device_id: ESP32_CAM_001
images[]: [archivo1.jpg, archivo2.jpg, ...] (hasta 10)
```

**Respuesta:**
```json
{
    "success": true,
    "event_id": "uuid",
    "images_received": 10,
    "images_processed": 10,
    "ai_processing": {
        "should_save_event": true,
        "save_reason": "Detected person with confidence 0.95",
        "best_classification": {
            "class": "person",
            "confidence": 0.95,
            "all_probabilities": {
                "person": 0.95,
                "animal": 0.03,
                "vehicle": 0.01,
                "other": 0.01
            }
        }
    },
    "supabase": {
        "event_updated": true,
        "alert_created": true,
        "images_uploaded": 5,
        "uploaded_images": [
            {
                "path": "events/uuid.jpg",
                "url": "https://..."
            }
        ]
    }
}
```

#### 3. Health Check

```http
GET /api/health/
```

**Respuesta:**
```json
{
    "status": "healthy",
    "service": "IoT Middleware",
    "version": "1.0.0",
    "mode": "transfer_only",
    "supabase_configured": true,
    "ai_model_loaded": true
}
```

### Endpoints de Gestión (Con autenticación JWT)

#### Obtener token JWT

```http
POST /api/token/
Content-Type: application/json

{
    "username": "admin",
    "password": "tu-password"
}
```

#### Obtener eventos desde Supabase

```http
GET /api/events/?limit=100&offset=0&type=person
Authorization: Bearer <token>
```

#### Obtener alertas desde Supabase

```http
GET /api/alerts/?limit=100&status=completed
Authorization: Bearer <token>
```

#### Registrar dispositivo

```http
POST /api/devices/register/
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "ESP32_CAM_001",
    "address": "192.168.1.100",
    "ubication": "Entrada principal",
    "status": true
}
```

#### Registrar sensor

```http
POST /api/sensors/register/
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "PIR Entrada",
    "type": "pir",
    "pin": 13,
    "status": true,
    "device_id": "uuid-del-dispositivo"
}
```

## 🔄 Flujo de Trabajo

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
7. IA clasifica las imágenes
   ↓
8. Si confianza > 70% y es persona/animal:
   - Guarda 5 mejores imágenes en Supabase Storage
   - Actualiza evento en Supabase Database
   - Crea alerta en Supabase
```

## 🤖 Configuración del Modelo IA

### Usar modelo dummy (testing)

No requiere configuración. Se usa automáticamente si no encuentra `models/best_model.pth`.

### Entrenar modelo propio

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

### Ajustar parámetros

En `.env`:

```env
CONFIDENCE_THRESHOLD=0.7  # 70% de confianza mínima
MAX_IMAGES_TO_SAVE=5      # Guardar solo 5 imágenes
IMAGES_PER_EVENT=10       # Recibir hasta 10 imágenes
```

## 🔧 Configuración de Supabase

### 1. Crear tablas

Ejecuta el SQL proporcionado arriba en el SQL Editor de Supabase.

### 2. Crear bucket

1. Ve a Storage → Create bucket
2. Nombre: `event-images`
3. Configurar como público

### 3. Obtener credenciales

1. Ve a Settings → API
2. Copia:
   - Project URL
   - anon/public key
   - service_role key

## 🧪 Testing

### Probar endpoint PIR

```bash
curl -X POST http://localhost:8000/api/pir/event/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_CAM_001",
    "sensor_pin": 13,
    "motion_detected": true
  }'
```

### Probar health check

```bash
curl http://localhost:8000/api/health/
```

### Probar con Postman

Importa la colección de Postman en `docs/postman_collection.json`

## 📁 Estructura del Proyecto

```
iot-middleware/
├── iot_middleware/           # Configuración Django
│   ├── __init__.py
│   ├── settings.py           # Sin BD local
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── api/                      # Aplicación principal
│   ├── __init__.py
│   ├── models.py            # Solo referencia (no se usan)
│   ├── serializers.py       # No necesarios (sin BD local)
│   ├── views.py             # Endpoints que transfieren a Supabase
│   ├── urls.py              # URLs de la API
│   └── services/
│       ├── __init__.py
│       ├── supabase_service.py  # Cliente Supabase
│       └── ai_service.py        # Procesamiento IA
│
├── scripts/                  # Scripts útiles
│   ├── setup.sh
│   ├── setup.bat
│   └── train_model.py
│
├── docs/                     # Documentación
│   ├── postman_collection.json
│   └── ESP32_CODE.md
│
├── models/                   # Modelos IA
│   └── README.md
│
├── nginx/                    # Configuración Nginx
│   └── nginx.conf
│
├── media/                    # Temporal (se limpia automáticamente)
│   └── .gitkeep
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🐳 Docker

```bash
# 1. Configurar variables
copy .env.example .env
# Editar .env

# 2. Iniciar
docker-compose up -d

# 3. Ver logs
docker-compose logs -f
```

## 🔒 Seguridad

- Endpoints IoT sin autenticación (considerar API Key en producción)
- Endpoints de gestión con JWT
- CORS configurado (permite todas las rutas en desarrollo)
- Variables de entorno para credenciales
- **No hay base de datos local** - Solo Supabase

### Configuración CORS

**Desarrollo/Testing** (permite todas las rutas):
```python
# En settings.py
CORS_ALLOW_ALL_ORIGINS = True
```

**Producción** (solo orígenes específicos):
```python
# En settings.py
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio.com",
    "https://app.tu-dominio.com",
]
```

## 📝 Código ESP32

Ver `docs/ESP32_CODE.md` para el código completo del ESP32-CAM.

## 🐛 Solución de Problemas

### Error de conexión a Supabase

- Verifica `SUPABASE_URL` y `SUPABASE_KEY`
- Asegúrate de que el bucket `event-images` exista
- Verifica que las tablas estén creadas

### Modelo IA no carga

- El sistema usa modelo dummy automáticamente
- Verifica ruta en `MODEL_PATH`

### Error CORS

- Verifica `CORS_ALLOWED_ORIGINS` en settings.py

## 📦 Dependencias Principales

- **Django 4.2.7**: Framework web
- **Django REST Framework 3.14.0**: API REST
- **PyTorch 2.1.1**: Procesamiento IA
- **Supabase 1.0.3**: Cliente Supabase
- **Pillow 10.1.0**: Procesamiento de imágenes

## 🎯 Notas Importantes

1. **Sin base de datos local**: Este middleware NO guarda datos en PostgreSQL/SQLite. Todo se envía directamente a Supabase.

2. **Almacenamiento temporal**: Las imágenes se guardan temporalmente en `/media` solo para procesamiento con IA, luego se eliminan.

3. **Modelos de referencia**: Los modelos en `api/models.py` son solo para documentación, no se usan en el middleware.

4. **Supabase es la única fuente de verdad**: Todos los datos (eventos, alertas, imágenes) se almacenan en Supabase.

## 📞 Soporte

- **Documentación**: Este README
- **Código ESP32**: `docs/ESP32_CODE.md`
- **Testing**: `docs/postman_collection.json`
- **Resumen**: `PROJECT_SUMMARY.md`

---

**Versión**: 2.0.0  
**Arquitectura**: Middleware de transferencia puro  
**Estado**: Listo para producción