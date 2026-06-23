@echo off
title PC Monitor v2.0 — Sistema Completo
chcp 65001 > nul
set ROOT=%~dp0

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   PC MONITOR v2.0 — INICIANDO SISTEMA       ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  Abriendo:
echo   1. Servidor Central (puerto 8000)
echo   2. Agente local     (puerto 8001)
echo   3. Dashboard React  (puerto 5173)
echo.

REM Iniciar servidor central en ventana separada
start "Servidor Central :8000" cmd /k "chcp 65001 > nul && cd /d "%ROOT%servidor" && python main.py"

REM Esperar que el servidor arranque
timeout /t 3 /nobreak > nul

REM Iniciar agente local en ventana separada
start "Agente Local :8001" cmd /k "chcp 65001 > nul && cd /d "%ROOT%agente" && python agente.py"

REM Iniciar dashboard en ventana separada
start "Dashboard React :5173" cmd /k "chcp 65001 > nul && cd /d "%ROOT%dashboard" && npm run dev"

REM Esperar que el dashboard compile
timeout /t 5 /nobreak > nul

REM Abrir el navegador
echo  Abriendo dashboard en el navegador...
start http://localhost:5173

echo.
echo  Sistema iniciado. Podés cerrar esta ventana.
echo  Para detener: cerra las 3 ventanas negras que se abrieron.
timeout /t 5 /nobreak > nul
