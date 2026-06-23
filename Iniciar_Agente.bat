@echo off
title Agente PC Monitor v2.0
chcp 65001 > nul
cd /d "%~dp0agente"
python agente.py
pause
