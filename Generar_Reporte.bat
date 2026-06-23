@echo off
title Generador de Reportes Excel - Codere PC Monitor
color 0B
echo Iniciando entorno virtual...

:: Buscar el entorno de python si existe, o usar python del sistema
if exist .venv\Scripts\python.exe (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

%PYTHON_EXE% scripts\generar_excel.py
