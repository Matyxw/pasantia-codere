@echo off
title Instalador PC Monitor v2.0
chcp 65001 > nul
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   PC MONITOR v2.0 — INSTALACION COMPLETA    ║
echo  ╚══════════════════════════════════════════════╝
echo.

set ROOT=%~dp0

echo  [1/4] Instalando dependencias del AGENTE...
python -m pip install -r "%ROOT%agente\requirements.txt" -q
if %errorlevel% neq 0 (echo  ERROR en agente & pause & exit /b 1)
echo  OK - Agente

echo.
echo  [2/4] Instalando dependencias del SERVIDOR...
python -m pip install -r "%ROOT%servidor\requirements.txt" -q
if %errorlevel% neq 0 (echo  ERROR en servidor & pause & exit /b 1)
echo  OK - Servidor

echo.
echo  [3/4] Instalando dependencias del DASHBOARD...
cd /d "%ROOT%dashboard"
call npm install --silent
if %errorlevel% neq 0 (echo  ERROR en dashboard & pause & exit /b 1)
echo  OK - Dashboard

echo.
echo  [4/4] Creando acceso directo en el escritorio...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\PC Monitor v2.lnk');$s.TargetPath='%ROOT%Iniciar_TODO.bat';$s.WorkingDirectory='%ROOT%';$s.Description='PC Monitor v2.0';$s.Save()"
echo  OK - Acceso directo creado

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   INSTALACION COMPLETADA!                   ║
echo  ║                                              ║
echo  ║   Para MONITOREAR esta PC:                  ║
echo  ║     Ejecuta: Iniciar_Agente.bat             ║
echo  ║   Para abrir el PANEL CENTRAL:              ║
echo  ║     Ejecuta: Iniciar_TODO.bat               ║
echo  ║   Auto-start al iniciar Windows:            ║
echo  ║     Ejecuta: agente\instalar_servicio.ps1   ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
