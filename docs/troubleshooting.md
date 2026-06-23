# Troubleshooting — Problemas Comunes

## El servidor no arranca

### Error: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solución: instalar dependencias
pip install -r servidor/requirements.txt
# O con pyproject.toml:
pip install -e ".[dev]"
```

### Error: `Address already in use` (puerto 8000 o 8001)
```powershell
# Encontrar qué proceso usa el puerto:
netstat -ano | findstr :8000

# Matar el proceso (reemplazar PID con el número encontrado):
taskkill /PID [PID] /F
```

---

## El agente no responde

### La PC aparece como offline pero está encendida

1. Verificar que el agente esté corriendo:
```powershell
# En la PC objetivo:
Get-Process python | Where-Object {$_.MainWindowTitle -like "*Agente*"}
# O:
Invoke-RestMethod http://localhost:8001/health
```

2. Verificar el firewall:
```powershell
# Test desde el servidor central:
Test-NetConnection -ComputerName [IP-PC] -Port 8001
```

3. Si el firewall bloquea:
```powershell
# En la PC con agente, como admin:
New-NetFirewallRule -DisplayName "PC Monitor Agente" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
```

---

## El WebSocket se desconecta constantemente

- Verificar que no haya proxy entre el cliente y el servidor que no soporte WebSockets
- El dashboard tiene auto-reconexión cada 3 segundos — esperar unos segundos
- Revisar los logs del servidor: buscar `WebSocketDisconnect`

---

## El escaneo de red no encuentra agentes

1. Asegurar que los agentes estén corriendo en las PCs
2. Verificar que el puerto 8001 esté abierto en el firewall de cada PC
3. Confirmar que las PCs estén en la misma subred `/24`
4. El escaneo usa 60 hilas paralelas — en redes lentas puede tardar 20-30 segundos

---

## Errores de base de datos

### Error: `database is locked`
El modo WAL debería prevenir esto. Si ocurre:
```bash
# Cerrar todas las conexiones y reiniciar el servidor
# La DB tiene WAL habilitado desde config
```

### Borrar la base de datos (reset completo)
```bash
# ¡CUIDADO! Esto borra todo el historial
del servidor\monitor.db
# El servidor la recrea automáticamente al arrancar
```

---

## El dashboard no carga en el navegador

1. Verificar que el proceso de Vite esté corriendo (ventana `Dashboard React :5173`)
2. Ir a `http://localhost:5173`
3. Si hay error de CORS: verificar que `CORS_ORIGINS` en `.env` incluya la URL del dashboard
4. En producción, usar el build estático:
```bash
cd dashboard && npm run build
# Luego servir desde servidor/main.py (ver docs/deployment.md)
```

---

## Logs del servidor

El servidor imprime logs en la terminal donde corre. Para guardarlos a archivo:

```bash
# Windows:
python servidor/main.py > logs\servidor.log 2>&1
```

Para aumentar el nivel de logs, en `.env`:
```
LOG_LEVEL=DEBUG
```
