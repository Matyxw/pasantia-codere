# Guía de Despliegue — Red Corporativa

## Requisitos mínimos

### Servidor Central (1 PC dedicada)
- Windows 10/11 o Windows Server 2019+
- Python 3.11+
- Node.js 20+ (solo si se sirve el dashboard desde aquí)
- RAM: 512 MB mínimo, 2 GB recomendado
- Disco: 10 GB para logs e historial

### PCs Monitoreadas (cada una)
- Windows 10/11
- Python 3.11+ **O** el archivo `PCMonitor-Agente.exe` (sin Python requerido)
- Red: Puerto 8001 abierto en el firewall

---

## Despliegue del Agente en múltiples PCs

### Opción A — Con .exe (recomendada para producción)
1. Descargar `PCMonitor-Agente.exe` de la última Release en GitHub
2. Copiar a cada PC (puede ser vía GPO, scripts, USB, red compartida)
3. Doble clic para iniciar, o registrar como servicio automático:

```powershell
# En cada PC, como Administrador:
powershell -ExecutionPolicy Bypass -File instalar_servicio.ps1
```

### Opción B — Con Python
1. Copiar la carpeta `agente/` a cada PC
2. `pip install -r agente/requirements.txt`
3. Registrar como servicio: `instalar_servicio.ps1`

---

## Firewall — Puertos necesarios

| Puerto | Dirección | Descripción |
|--------|-----------|-------------|
| 8000 | IN en servidor central | API REST + WebSocket |
| 8001 | IN en cada PC agente | Endpoint del agente |
| 5173 | IN en servidor central | Dashboard (dev) |
| 80/443 | IN en servidor central | Dashboard (producción con nginx) |

### Abrir puertos con PowerShell (ejecutar como admin en cada PC):
```powershell
# En PCs con agente:
New-NetFirewallRule -DisplayName "PC Monitor Agente" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow

# En el servidor central:
New-NetFirewallRule -DisplayName "PC Monitor Servidor" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

---

## Distribución masiva vía GPO (Active Directory)

Para desplegar el agente en 200+ PCs automáticamente:

1. Crear un script de inicio de sesión en GPO:
```powershell
# deploy_agent.ps1 — ejecutar como script de inicio en AD
$AgentPath = "\\SERVIDOR-CENTRAL\PCMonitor\agente"
$LocalPath = "C:\PCMonitor"

if (-not (Test-Path $LocalPath)) {
    Copy-Item $AgentPath $LocalPath -Recurse
    powershell -ExecutionPolicy Bypass -File "$LocalPath\instalar_servicio.ps1" -NonInteractive
}
```

2. En la Consola de Administración de Directivas de Grupo:
   - Crear nueva GPO: "PC Monitor Agent Deploy"
   - `Computer Configuration > Windows Settings > Scripts > Startup`
   - Agregar el script `deploy_agent.ps1`
   - Vincular la GPO a las OUs con las PCs a monitorear

---

## Producción — Servir dashboard con Python

Para no depender de Node.js en producción, el servidor FastAPI puede servir el build del dashboard:

```python
# En servidor/main.py, agregar al final:
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="../dashboard/dist", html=True), name="dashboard")
```

Luego buildear el dashboard:
```bash
cd dashboard && npm run build
```

Ahora `http://localhost:8000` sirve el dashboard directamente.

---

## Configurar inicio automático del Servidor Central

```powershell
# instalar_servidor_servicio.ps1 (en el servidor central, como admin)
$TaskName = "PCMonitorServidor"
$PythonPath = (Get-Command python).Source
$ScriptPath = "D:\pasantia-codere\servidor\main.py"

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action (New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath) `
    -Trigger (New-ScheduledTaskTrigger -AtStartup) `
    -Principal (New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest) `
    -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 3) `
    -Force
```
