#!/bin/bash
# Script de configuración inicial del proyecto IoT Middleware

echo "========================================="
echo "IoT Middleware - Script de Configuración"
echo "========================================="
echo ""

# Verificar Python
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instala Python 3.8 o superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION encontrado"

# Verificar PostgreSQL
echo ""
echo "Verificando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL no encontrado. Asegúrate de tener PostgreSQL instalado."
else
    echo "✅ PostgreSQL encontrado"
fi

# Crear entorno virtual
echo ""
echo "Creando entorno virtual..."
if [ -d "venv" ]; then
    echo "⚠️  El entorno virtual ya existe"
else
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
fi

# Activar entorno virtual
echo ""
echo "Activando entorno virtual..."
source venv/bin/activate || venv\Scripts\activate

# Instalar dependencias
echo ""
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencias instaladas"

# Crear archivo .env si no existe
echo ""
if [ ! -f ".env" ]; then
    echo "Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo "✅ Archivo .env creado"
    echo ""
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones:"
    echo "   - SECRET_KEY"
    echo "   - Configuración de base de datos"
    echo "   - Credenciales de Supabase"
else
    echo "⚠️  El archivo .env ya existe"
fi

# Crear directorios necesarios
echo ""
echo "Creando directorios..."
mkdir -p models
mkdir -p media/events
mkdir -p logs
touch media/.gitkeep
echo "✅ Directorios creados"

# Verificar configuración de base de datos
echo ""
echo "Verificando base de datos..."
read -p "¿Deseas crear la base de datos ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    read -p "Nombre de la base de datos (default: iot_middleware): " db_name
    db_name=${db_name:-iot_middleware}
    
    read -p "Usuario de PostgreSQL (default: postgres): " db_user
    db_user=${db_user:-postgres}
    
    read -sp "Contraseña de PostgreSQL: " db_password
    echo
    
    # Crear base de datos
    PGPASSWORD=$db_password psql -U $db_user -c "CREATE DATABASE $db_name;" 2>/dev/null && \
    echo "✅ Base de datos '$db_name' creada" || \
    echo "⚠️  No se pudo crear la base de datos (puede que ya exista)"
fi

# Ejecutar migraciones
echo ""
read -p "¿Deseas ejecutar las migraciones ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "Ejecutando migraciones..."
    python manage.py makemigrations
    python manage.py migrate
    echo "✅ Migraciones ejecutadas"
fi

# Crear superusuario
echo ""
read -p "¿Deseas crear un superusuario ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "Creando superusuario..."
    python manage.py createsuperuser
fi

echo ""
echo "========================================="
echo "✅ Configuración completada"
echo "========================================="
echo ""
echo "Próximos pasos:"
echo "1. Edita el archivo .env con tus configuraciones"
echo "2. Configura Supabase (ver README.md)"
echo "3. Coloca tu modelo IA en models/best_model.pth (opcional)"
echo "4. Ejecuta: python manage.py runserver"
echo ""
echo "El servidor estará disponible en: http://localhost:8000"
echo ""