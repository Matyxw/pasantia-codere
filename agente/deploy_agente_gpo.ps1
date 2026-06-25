<#
.SYNOPSIS
    Script de instalación y despliegue masivo del Agente PC Monitor para entornos empresariales (Active Directory / GPO).

.DESCRIPTION
    Este script está diseñado para ejecutarse de forma silenciosa (System/Admin) mediante 
    Group Policy Objects (GPO) o herramientas de despliegue (MECM, PDQ Deploy, etc.).
    
    Tareas que realiza:
    1. Verifica si se está ejecutando con privilegios de Administrador.
    2. Crea el directorio destino en C:\Program Files\PCMonitor (si no existe).
    3. Copia el ejecutable del agente (agente.exe) desde la ubicación de despliegue.
    4. Genera el archivo "agent_config.json" dinámicamente con la IP del Servidor Central.
    5. Elimina instalaciones anteriores si las hubiera.
    6. Crea una Tarea Programada de Windows para ejecutar el agente como SYSTEM en cada inicio.
    7. Inicia el servicio inmediatamente sin requerir reinicio.

.PARAMETER ServerIp
    (Obligatorio) La IP estática del Servidor Central donde corre FastAPI/WebSocket (ej: 192.168.1.50).

.PARAMETER SourceExe
    (Opcional) Ruta al ejecutable agente.exe. Por defecto busca en la misma carpeta que el script.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File deploy_agente_gpo.ps1 -ServerIp "192.168.1.50"
#>

Param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIp,

    [string]$SourceExe = ""
)

# 1. Configuración de Rutas
$InstallDir = "C:\Program Files\PCMonitor"
$TargetExe = Join-Path $InstallDir "agente.exe"
$ConfigPath = Join-Path $InstallDir "agent_config.json"
$TaskName = "PCMonitorAgente"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrEmpty($SourceExe)) {
    $SourceExe = Join-Path $ScriptPath "agente.exe"
}

# Inicio silencioso - redirigimos todo al log
$LogFile = "C:\Windows\Temp\PCMonitor_Install.log"
Function Write-Log {
    Param([string]$Message)
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$TimeStamp - $Message" | Out-File $LogFile -Append
}

Write-Log "=========================================="
Write-Log "Iniciando despliegue de PC Monitor Agente..."
Write-Log "IP Servidor Central configurada: $ServerIp"

# 2. Verificar origen
if (-not (Test-Path $SourceExe)) {
    Write-Log "ERROR: No se encontró el ejecutable en: $SourceExe"
    Write-Log "Asegúrate de compilar el agente con PyInstaller antes de desplegar."
    Exit 1
}

# 3. Crear directorio de destino
try {
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
        Write-Log "Directorio creado: $InstallDir"
    }
} catch {
    Write-Log "ERROR al crear el directorio de instalación: $_"
    Exit 1
}

# 4. Detener tarea existente si está corriendo para poder sobrescribir el .exe
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Log "Deteniendo tarea programada existente..."
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 5. Copiar archivo ejecutable
try {
    Copy-Item -Path $SourceExe -Destination $TargetExe -Force
    Write-Log "Ejecutable copiado exitosamente a: $TargetExe"
} catch {
    Write-Log "ERROR al copiar el ejecutable (¿el archivo está en uso?): $_"
    Exit 1
}

# 6. Generar agent_config.json dinámico
try {
    $ConfigJson = @{ server_ip = $ServerIp } | ConvertTo-Json
    $ConfigJson | Out-File -FilePath $ConfigPath -Encoding UTF8 -Force
    Write-Log "Archivo agent_config.json generado con IP: $ServerIp"
} catch {
    Write-Log "ERROR al generar config: $_"
    Exit 1
}

# 7. Registrar / Actualizar la Tarea Programada (Servicio)
try {
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Log "Tarea programada anterior eliminada."
    }

    $Action = New-ScheduledTaskAction -Execute $TargetExe -WorkingDirectory $InstallDir
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $Settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Settings $Settings `
        -Description "PC Monitor Agent v2.0 - Telemetría y Gestión Remota" `
        -Force | Out-Null

    Write-Log "Tarea programada '$TaskName' registrada exitosamente como SYSTEM."
} catch {
    Write-Log "ERROR al registrar tarea programada: $_"
    Exit 1
}

# 8. Iniciar el servicio ahora mismo
try {
    Start-ScheduledTask -TaskName $TaskName
    Write-Log "Agente iniciado exitosamente en background."
} catch {
    Write-Log "Advertencia al intentar iniciar la tarea: $_"
}

Write-Log "Instalación completada exitosamente."
Write-Log "=========================================="
Exit 0
