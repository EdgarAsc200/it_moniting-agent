# IT Monitoring Agent - Windows Task Scheduler
# =============================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   IT MONITORING AGENT - TASK SCHEDULER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar privilegios de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Este script requiere privilegios de administrador" -ForegroundColor Red
    pause
    exit 1
}

# Variables
$TaskName = "IT Monitoring Agent"
$InstallDir = "C:\Program Files\ITMonitoringAgent"
$PythonExe = "$InstallDir\venv\Scripts\python.exe"
$MainScript = "$InstallDir\src\main.py"

# Verificar instalacion
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: El agente no esta instalado" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[1/3] Eliminando tarea existente (si existe)..." -ForegroundColor Green
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "[2/3] Creando nueva tarea programada..." -ForegroundColor Green

# Accion: Ejecutar el agente
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$MainScript`" --once" -WorkingDirectory $InstallDir

# Trigger: Al iniciar el sistema y cada hora
$TriggerBoot = New-ScheduledTaskTrigger -AtStartup
$TriggerHourly = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)

# Configuracion
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Principal: Ejecutar como SYSTEM
$Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Write-Host "[3/3] Registrando tarea..." -ForegroundColor Green
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $TriggerBoot,$TriggerHourly -Settings $Settings -Principal $Principal -Description "Agente de monitoreo IT - Recoleccion de inventario"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   TAREA PROGRAMADA CREADA" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "La tarea se ejecutara:" -ForegroundColor Yellow
Write-Host "  - Al iniciar el sistema" -ForegroundColor White
Write-Host "  - Cada hora" -ForegroundColor White
Write-Host ""
Write-Host "Puedes ver/editar la tarea en: Programador de tareas" -ForegroundColor Yellow
Write-Host ""
pause
