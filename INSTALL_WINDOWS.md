# Instalación en Windows - Guía Completa

## ⚠️ Error Común: Pillow en Windows

Si obtienes este error al instalar:
```
ERROR: Failed to build 'Pillow' when getting requirements to build wheel
KeyError: '__version__'
```

## ✅ Solución

### Opción 1: Instalación Rápida (Recomendada)

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependencias básicas (sin Pillow)
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install supabase==1.0.3
pip install python-dotenv==1.0.0
pip install numpy==1.26.2
pip install torch==2.1.1
pip install torchvision==0.16.1
pip install requests==2.31.0

# 3. Instalar Pillow (opcional, solo si lo necesitas)
pip install --only-binary :all: Pillow==9.5.0
```

### Opción 2: Instalación Completa con OpenCV

```bash
# 1. Activar entorno virtual
venv\Scripts\activate

# 2. Instalar OpenCV (alternativa a Pillow)
pip install opencv-python-headless==4.8.1.78

# 3. Instalar resto de dependencias
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install supabase==1.0.3
pip install python-dotenv==1.0.0
pip install numpy==1.26.2
pip install torch==2.1.1
pip install torchvision==0.16.1
pip install requests==2.31.0
```

### Opción 3: Usar el Script de Setup

```bash
# Doble clic en
scripts/setup.bat
```

El script instalará las dependencias automáticamente (sin Pillow).

## 🔧 Configuración de Pillow (Opcional)

Si necesitas Pillow para procesamiento de imágenes:

### Método 1: Usar Binarios Precompilados

```bash
# Instalar versión precompilada
pip install --only-binary :all: Pillow==9.5.0
```

### Método 2: Instalar con Visual C++ Build Tools

1. Descargar e instalar [Visual C++ Build Tools](https://visualstudio.microsoft.com/downloads/)
2. Durante la instalación, seleccionar "Desktop development with C++"
3. Reinizar la terminal
4. Intentar instalar Pillow:
   ```bash
   pip install Pillow==9.5.0
   ```

### Método 3: Usar WSL2 (Windows Subsystem for Linux)

```bash
# En WSL2 (Ubuntu)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📋 Dependencias por Función

### Mínimas (Funcionamiento Básico)
```
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
supabase==1.0.3
python-dotenv==1.0.0
numpy==1.26.2
torch==2.1.1
torchvision==0.16.1
requests==2.31.0
```

### Para Procesamiento de Imágenes (Elegir UNA)

**Opción A: Pillow (más ligero)**
```
Pillow==9.5.0
```

**Opción B: OpenCV (más robusto)**
```
opencv-python-headless==4.8.1.78
```

**Opción C: Ninguna (usa numpy)**
```
# No instalar nada adicional
# El sistema usará numpy para procesamiento básico
```

## 🚀 Instalación Paso a Paso (Windows)

### 1. Verificar Python

```bash
python --version
# Debe ser Python 3.8 o superior
```

### 2. Actualizar pip

```bash
python -m pip install --upgrade pip
```

### 3. Crear Entorno Virtual

```bash
# Navegar a la carpeta del proyecto
cd C:\Users\F20LAB109E10\Desktop\iot-middleware

# Crear entorno virtual
python -m venv venv

# Activar
venv\Scripts\activate
```

### 4. Instalar Dependencias

```bash
# Opción A: Sin Pillow (recomendado para evitar errores)
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1
pip install supabase==1.0.3
pip install python-dotenv==1.0.0
pip install numpy==1.26.2
pip install torch==2.1.1
pip install torchvision==0.16.1
pip install requests==2.31.0

# Opción B: Con OpenCV (mejor para imágenes)
pip install opencv-python-headless==4.8.1.78
```

### 5. Verificar Instalación

```bash
python -c "import django; print(f'Django: {django.VERSION}')"
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import supabase; print('Supabase: OK')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
```

## 🐛 Solución de Problemas

### Error: "pip no se reconoce"

```bash
# Usar python -m pip en lugar de pip
python -m pip install --upgrade pip
```

### Error: "No module named 'venv'"

```bash
# Instalar venv
python -m pip install virtualenv
virtualenv venv
venv\Scripts\activate
```

### Error al instalar PyTorch

```bash
# Instalar versión CPU (más ligera)
pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu
pip install torchvision==0.16.1 --index-url https://download.pytorch.org/whl/cpu
```

### Error de permisos

```bash
# Ejecutar PowerShell como administrador
# O instalar en usuario actual
pip install --user <paquete>
```

## ✅ Verificación Final

```bash
# Activar entorno virtual
venv\Scripts\activate

# Verificar que todo funciona
python manage.py check

# Debe mostrar:
# System check identified no issues (0 silenced).
```

## 📝 Notas

1. **Pillow es opcional**: El sistema funciona sin Pillow usando OpenCV o numpy
2. **OpenCV recomendado**: Mejor compatibilidad en Windows
3. **Entorno virtual**: Siempre activar antes de trabajar
4. **Python 3.8+**: Requerido para compatibilidad

## 🎯 Siguiente Paso

Una vez instaladas las dependencias:

```bash
# 1. Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales

# 2. Ejecutar servidor
python manage.py runserver
```

---

**Sistema**: Windows 10/11  
**Python**: 3.8+  
**Estado**: Solucionado error de Pillow