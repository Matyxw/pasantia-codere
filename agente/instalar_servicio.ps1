# instalar_servicio.ps1
# Registra el agente como tarea programada de Windows para que arranque automaticamente al iniciar la PC
# Ejecutar como Administrador: powershell -ExecutionPolicy Bypass -File instalar_servicio.ps1

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgenteScript = Join-Path $ScriptPath "agente.py"
$PythonPath = (Get-Command python).Source

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  INSTALANDO AGENTE COMO SERVICIO" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Python   : $PythonPath" -ForegroundColor White
Write-Host "  Agente   : $AgenteScript" -ForegroundColor White
Write-Host ""

# Nombre de la tarea
$TaskName = "PCMonitorAgente"

# Eliminar tarea existente si hay
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "  [OK] Tarea anterior eliminada" -ForegroundColor Yellow
}

# Accion: ejecutar python agente.py
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument $AgenteScript `
    -WorkingDirectory $ScriptPath

# Disparador: al iniciar Windows
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Configuracion: correr como SYSTEM, sin importar si hay usuario conectado
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Opciones: reiniciar si falla, hasta 3 veces
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Registrar la tarea
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "PC Monitor Agent v2.0 - Se inicia automaticamente con Windows" `
    -Force

Write-Host ""
Write-Host "  [OK] Tarea '$TaskName' registrada exitosamente!" -ForegroundColor Green
Write-Host "  El agente iniciara automaticamente la proxima vez que prenda la PC." -ForegroundColor Green
Write-Host ""

# Preguntar si iniciar ahora
$start = Read-Host "  Iniciar el agente ahora? (s/n)"
if ($start -eq "s" -or $start -eq "S") {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "  [OK] Agente iniciado!" -ForegroundColor Green
    Start-Sleep -Seconds 2
    $status = (Get-ScheduledTask -TaskName $TaskName).State
    Write-Host "  Estado: $status" -ForegroundColor White
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Para desinstalar: ejecuta desinstalar_servicio.ps1" -ForegroundColor Gray
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
