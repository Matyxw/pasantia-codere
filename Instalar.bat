@echo off
REM Script de instalación automática para Windows
REM Instala todas las dependencias necesarias

color 0a
title Sistema de Monitoreo de PCs - Instalador

echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║   Sistema de Monitoreo de PCs en Red - Instalador                    ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

REM Verifica si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo.
    echo Descarga Python desde: https://www.python.org/
    echo Asegúrate de marcar "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

echo ✅ Python detectado
python --version
echo.

REM Instala pip
echo 📦 Actualizando pip...
python -m pip install --upgrade pip -q

REM Instala dependencias desde requirements.txt
if exist requirements.txt (
    echo 📦 Instalando dependencias desde requirements.txt...
    python -m pip install -r requirements.txt -q
) else (
    echo 📦 Instalando dependencias...
    python -m pip install flask psutil requests openpyxl pandas -q
)

if %errorlevel% neq 0 (
    echo ❌ Error durante la instalación
    pause
    exit /b 1
)

echo ✅ Dependencias instaladas correctamente
echo.

REM Ejecuta el instalador Python
echo ⚙️  Ejecutando configuración...
python instalar.py

echo.
echo ✅ ¡Instalación completada!
pause
