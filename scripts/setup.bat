@echo off
REM Script de configuración inicial del proyecto IoT Middleware (Windows)
REM Middleware de transferencia - Sin base de datos local

echo =========================================
echo IoT Middleware - Script de Configuracion
echo =========================================
echo.
echo NOTA: Este es un middleware SIN base de datos local
echo       Todos los datos se guardan en Supabase
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python 3 no esta instalado. Por favor instala Python 3.8 o superior.
    pause
    exit /b 1
)
python --version
echo ✓ Python encontrado

REM Crear entorno virtual
echo.
echo Creando entorno virtual...
if exist "venv" (
    echo ! El entorno virtual ya existe
) else (
    python -m venv venv
    echo ✓ Entorno virtual creado
)

REM Activar entorno virtual
echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo.
echo Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
echo ✓ Dependencias instaladas

REM Crear archivo .env si no existe
echo.
if not exist ".env" (
    echo Creando archivo .env desde .env.example...
    copy .env.example .env
    echo ✓ Archivo .env creado
    echo.
    echo ! IMPORTANTE: Edita el archivo .env con tus configuraciones:
    echo    - SUPABASE_URL
    echo    - SUPABASE_KEY
    echo    - SUPABASE_SERVICE_KEY
    echo    - SECRET_KEY
) else (
    echo ! El archivo .env ya existe
)

REM Crear directorios necesarios
echo.
echo Creando directorios...
if not exist "models" mkdir models
if not exist "media\temp" mkdir media\temp
if not exist "logs" mkdir logs
if not exist "media" mkdir media
echo. > media\.gitkeep
echo ✓ Directorios creados

echo.
echo =========================================
echo ✓ Configuracion completada
echo =========================================
echo.
echo Proximos pasos:
echo 1. Edita el archivo .env con tus configuraciones de Supabase
echo 2. Configura Supabase:
echo    - Crea las tablas con el SQL del README.md
echo    - Crea el bucket 'event-images' en Storage
echo 3. (Opcional) Coloca tu modelo IA en models/best_model.pth
echo 4. Ejecuta: python manage.py runserver
echo.
echo El servidor estara disponible en: http://localhost:8000
echo.
echo NOTA: Este middleware NO usa base de datos local
echo       Todos los datos se guardan en Supabase
echo.
pause