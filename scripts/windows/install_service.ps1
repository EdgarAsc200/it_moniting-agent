# ============================================================
# IT MONITORING AGENT - SERVICE/TASK INSTALLER
# Version: 2.0
# Descripción: Instala el agente como servicio o tarea programada
# ============================================================

param(
    [switch]$TaskOnly,
    [switch]$ServiceOnly,
    [string]$InstallPath
)

# Colores y formato
function Write-Step {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "   $Message" -ForegroundColor Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

# Banner
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   IT MONITORING AGENT - INSTALLER v2.0" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar privilegios de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error-Message "ERROR: Este script requiere privilegios de administrador"
    Write-Host ""
    Write-Warning "Por favor:"
    Write-Host "1. Click derecho en PowerShell" -ForegroundColor White
    Write-Host "2. Selecciona 'Ejecutar como administrador'" -ForegroundColor White
    Write-Host "3. Vuelve a ejecutar este script" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

# Detectar ubicación de instalación
if ($InstallPath) {
    $InstallDir = $InstallPath
} else {
    $PossiblePaths = @(
        "C:\Program Files\ITMonitoringAgent",
        "C:\Archivos de programa\ITMonitoringAgent"
    )
    
    $InstallDir = $null
    foreach ($path in $PossiblePaths) {
        if (Test-Path $path) {
            $InstallDir = $path
            break
        }
    }
}

if (-not $InstallDir -or -not (Test-Path $InstallDir)) {
    Write-Error-Message "ERROR: No se encuentra la instalacion del agente"
    Write-Host ""
    Write-Warning "Ejecuta install.bat primero para instalar el agente"
    Write-Host ""
    pause
    exit 1
}

Write-Info "Ubicacion detectada: $InstallDir"
Write-Host ""

# Variables
$ServiceName = "ITMonitoringAgent"
$DisplayName = "IT Monitoring Agent"
$Description = "Agente de monitoreo y recoleccion de inventario IT"
$PythonExe = "$InstallDir\venv\Scripts\python.exe"
$MainScript = "$InstallDir\src\main.py"

# Cambiar al directorio de instalación
Set-Location $InstallDir

# ============================================================
# PASO 1: Verificar instalación
# ============================================================
Write-Step "[1/9] Verificando instalacion..."

if (-not (Test-Path $PythonExe)) {
    Write-Error-Message "ERROR: Python no encontrado en $PythonExe"
    pause
    exit 1
}
Write-Info "Python encontrado"

if (-not (Test-Path $MainScript)) {
    Write-Error-Message "ERROR: Script principal no encontrado en $MainScript"
    pause
    exit 1
}
Write-Info "Script principal encontrado"

# Verificar que el agente funciona
Write-Info "Probando agente..."
$testResult = & $PythonExe $MainScript --test 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error-Message "ERROR: El agente no funciona correctamente"
    Write-Host ""
    Write-Warning "Detalle del error:"
    Write-Host $testResult -ForegroundColor Gray
    Write-Host ""
    Write-Warning "Posibles soluciones:"
    Write-Host "1. Revisa config\agent.ini" -ForegroundColor White
    Write-Host "2. Verifica las dependencias: venv\Scripts\pip.exe list" -ForegroundColor White
    Write-Host "3. Revisa los logs: logs\agent.log" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}
Write-Success "   OK - Agente funciona correctamente"
Write-Host ""

# ============================================================
# PASO 2: Instalar dependencias
# ============================================================
Write-Step "[2/9] Instalando dependencias Python..."
$pipExe = "$InstallDir\venv\Scripts\pip.exe"

# Lista de dependencias necesarias
$dependencies = @("psutil", "requests", "APScheduler", "pyyaml", "pywin32")

foreach ($dep in $dependencies) {
    $installed = & $pipExe show $dep 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Info "Instalando $dep..."
        & $pipExe install $dep --quiet --disable-pip-version-check
    } else {
        Write-Info "$dep ya instalado"
    }
}
Write-Success "   Dependencias verificadas"
Write-Host ""

# ============================================================
# PASO 3: Decidir método de instalación
# ============================================================
if ($TaskOnly) {
    $installMethod = "task"
} elseif ($ServiceOnly) {
    $installMethod = "service"
} else {
    Write-Host "Metodos de instalacion disponibles:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Servicio de Windows" -ForegroundColor White
    Write-Host "   - Se ejecuta automaticamente al iniciar" -ForegroundColor Gray
    Write-Host "   - Requiere pywin32" -ForegroundColor Gray
    Write-Host "   - Mas complejo pero mas integrado" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Tarea Programada (RECOMENDADO)" -ForegroundColor White
    Write-Host "   - Se ejecuta automaticamente al iniciar" -ForegroundColor Gray
    Write-Host "   - Mas simple y confiable" -ForegroundColor Gray
    Write-Host "   - Mas facil de administrar" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $choice = Read-Host "Selecciona metodo (1=Servicio, 2=Tarea) [2]"
        if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "2" }
    } while ($choice -notin @("1", "2"))
    
    $installMethod = if ($choice -eq "1") { "service" } else { "task" }
}

Write-Host ""

# ============================================================
# INSTALACIÓN COMO SERVICIO
# ============================================================
if ($installMethod -eq "service") {
    
    Write-Step "[3/9] Deteniendo servicio existente..."
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Info "Servicio encontrado, deteniendo..."
        if ($existingService.Status -eq 'Running') {
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }
        
        # Intentar desinstalar
        Write-Info "Desinstalando servicio anterior..."
        try {
            & $PythonExe "$InstallDir\service_wrapper.py" remove 2>&1 | Out-Null
        } catch {}
        
        # Forzar eliminación
        sc.exe delete $ServiceName 2>$null | Out-Null
        Start-Sleep -Seconds 2
        Write-Success "   Servicio anterior eliminado"
    } else {
        Write-Info "No hay servicio anterior"
    }
    Write-Host ""
    
    Write-Step "[4/9] Creando service wrapper..."
    
    # Crear wrapper del servicio
    $wrapperCode = @"
# service_wrapper.py
# IT Monitoring Agent - Windows Service Wrapper
# ============================================================

import sys
import os
import time
import logging
from logging.handlers import RotatingFileHandler

# Configurar logging
log_file = r'$InstallDir\logs\service.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Configurar paths
INSTALL_DIR = r'$InstallDir'
sys.path.insert(0, os.path.join(INSTALL_DIR, 'src'))
os.chdir(INSTALL_DIR)

logger.info('='*60)
logger.info('Service wrapper starting')
logger.info(f'Install dir: {INSTALL_DIR}')
logger.info(f'Python: {sys.executable}')
logger.info(f'Python version: {sys.version}')
logger.info('='*60)

# Importar modulos de Windows
try:
    import servicemanager
    import win32serviceutil
    import win32service
    import win32event
    logger.info('Windows service modules imported successfully')
except Exception as e:
    logger.error(f'Failed to import Windows service modules: {e}')
    logger.error('Make sure pywin32 is installed: pip install pywin32')
    raise

# Importar main del agente
try:
    from main import main as agent_main
    logger.info('Agent main function imported successfully')
except Exception as e:
    logger.error(f'Failed to import agent main: {e}')
    raise

class ITMonitoringAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = '$ServiceName'
    _svc_display_name_ = '$DisplayName'
    _svc_description_ = '$Description'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        logger.info('Service instance initialized')
    
    def SvcStop(self):
        logger.info('Service stop requested')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logger.info('Service stopped')
    
    def SvcDoRun(self):
        logger.info('Service starting - SvcDoRun called')
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            # Dar tiempo para que el servicio se registre
            logger.info('Waiting for service registration...')
            time.sleep(2)
            
            # Reportar que estamos corriendo
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            logger.info('Service status set to RUNNING')
            
            # Ejecutar agente
            logger.info('Starting agent main function')
            agent_main()
            
            logger.info('Agent main function completed')
            
        except Exception as e:
            error_msg = f'Service error: {e}'
            logger.error(error_msg, exc_info=True)
            servicemanager.LogErrorMsg(error_msg)
            raise

if __name__ == '__main__':
    logger.info('Service wrapper main execution')
    try:
        win32serviceutil.HandleCommandLine(ITMonitoringAgentService)
    except Exception as e:
        logger.error(f'Service wrapper error: {e}', exc_info=True)
        raise
"@
    
    $wrapperCode | Out-File -FilePath "$InstallDir\service_wrapper.py" -Encoding UTF8
    Write-Success "   Service wrapper creado"
    Write-Host ""
    
    Write-Step "[5/9] Registrando servicio..."
    try {
        $installOutput = & $PythonExe "$InstallDir\service_wrapper.py" install 2>&1
        Write-Info $installOutput
        Write-Success "   Servicio registrado"
    } catch {
        Write-Error-Message "ERROR al registrar servicio: $_"
        Write-Host ""
        Write-Warning "Intentando con tarea programada en su lugar..."
        $installMethod = "task"
    }
    
    if ($installMethod -eq "service") {
        Write-Host ""
        
        Write-Step "[6/9] Configurando servicio..."
        sc.exe config $ServiceName start= auto | Out-Null
        sc.exe failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/restart/60000 | Out-Null
        Write-Success "   Servicio configurado"
        Write-Host ""
        
        Write-Step "[7/9] Iniciando servicio..."
        Write-Info "Esto puede tomar 10-15 segundos..."
        
        $startResult = net start $ServiceName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Success "   SERVICIO INICIADO EXITOSAMENTE"
            Write-Host ""
            Start-Sleep -Seconds 2
            
            $serviceStatus = sc.exe query $ServiceName
            Write-Host $serviceStatus
            
        } else {
            Write-Host ""
            Write-Error-Message "ERROR: No se pudo iniciar el servicio"
            Write-Info "Detalle: $startResult"
            Write-Host ""
            
            if (Test-Path "$InstallDir\logs\service.log") {
                Write-Warning "--- Ultimas lineas del log ---"
                Get-Content "$InstallDir\logs\service.log" -Tail 20
            }
            
            Write-Host ""
            $response = Read-Host "Deseas usar Tarea Programada en su lugar? (S/N) [S]"
            if ([string]::IsNullOrWhiteSpace($response)) { $response = "S" }
            
            if ($response -eq 'S' -or $response -eq 's') {
                Write-Info "Eliminando servicio fallido..."
                sc.exe delete $ServiceName 2>$null | Out-Null
                $installMethod = "task"
            } else {
                Write-Host ""
                pause
                exit 1
            }
        }
    }
}

# ============================================================
# INSTALACIÓN COMO TAREA PROGRAMADA
# ============================================================
if ($installMethod -eq "task") {
    
    Write-Host ""
    Write-Step "[3/9] Configurando Tarea Programada..."
    Write-Host ""
    
    Write-Step "[4/9] Eliminando tarea anterior..."
    $existingTask = Get-ScheduledTask -TaskName "IT Monitoring Agent" -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Info "Tarea encontrada, eliminando..."
        Unregister-ScheduledTask -TaskName "IT Monitoring Agent" -Confirm:$false
        Write-Success "   Tarea anterior eliminada"
    } else {
        Write-Info "No hay tarea anterior"
    }
    Write-Host ""
    
    Write-Step "[5/9] Creando accion de tarea..."
    $action = New-ScheduledTaskAction `
        -Execute "$InstallDir\venv\Scripts\python.exe" `
        -Argument "`"$InstallDir\src\main.py`"" `
        -WorkingDirectory $InstallDir
    Write-Success "   Accion creada"
    Write-Host ""
    
    Write-Step "[6/9] Configurando triggers..."
    
    # Trigger 1: Al iniciar Windows
    $triggerStartup = New-ScheduledTaskTrigger -AtStartup
    Write-Info "Trigger 1: Al iniciar Windows"
    
    # Trigger 2: Cada hora (CORREGIDO)
    $triggerHourly = New-ScheduledTaskTrigger -Once -At (Get-Date)
    $triggerHourly.Repetition.Duration = "P10000D"  # 10000 dias (~27 años)
    $triggerHourly.Repetition.Interval = "PT1H"     # Cada 1 hora
    Write-Info "Trigger 2: Cada hora"
    Write-Success "   Triggers configurados"
    Write-Host ""
    
    Write-Step "[7/9] Configurando opciones..."
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Write-Success "   Opciones configuradas"
    Write-Host ""
    
    Write-Step "[8/9] Configurando permisos..."
    $principal = New-ScheduledTaskPrincipal `
        -UserId "NT AUTHORITY\SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest
    Write-Success "   Permisos configurados"
    Write-Host ""
    
    Write-Step "[9/9] Registrando tarea..."
    try {
        Register-ScheduledTask `
            -TaskName "IT Monitoring Agent" `
            -Action $action `
            -Trigger @($triggerStartup, $triggerHourly) `
            -Settings $settings `
            -Principal $principal `
            -Description $Description `
            -Force | Out-Null
        
        Write-Success "   Tarea registrada exitosamente"
        Write-Host ""
        
        # Ejecutar la tarea ahora
        Write-Info "Ejecutando tarea ahora para verificar..."
        Start-ScheduledTask -TaskName "IT Monitoring Agent"
        Start-Sleep -Seconds 5
        
        # Verificar resultado
        $taskInfo = Get-ScheduledTaskInfo -TaskName "IT Monitoring Agent"
        $task = Get-ScheduledTask -TaskName "IT Monitoring Agent"
        
        Write-Host ""
        Write-Host "Estado de la tarea:" -ForegroundColor Cyan
        Write-Host "  Nombre:           $($task.TaskName)" -ForegroundColor White
        Write-Host "  Estado:           $($task.State)" -ForegroundColor White
        Write-Host "  Ultima ejecucion: $($taskInfo.LastRunTime)" -ForegroundColor White
        Write-Host "  Resultado:        $($taskInfo.LastTaskResult)" -ForegroundColor White
        
        if ($taskInfo.LastTaskResult -eq 0) {
            Write-Host ""
            Write-Success "TAREA EJECUTADA CORRECTAMENTE"
        } else {
            Write-Host ""
            Write-Warning "Codigo de resultado: $($taskInfo.LastTaskResult)"
            Write-Info "Revisa los logs para mas detalles"
        }
        
    } catch {
        Write-Error-Message "ERROR al crear tarea programada:"
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host ""
        pause
        exit 1
    }
}

# ============================================================
# RESUMEN FINAL
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
if ($installMethod -eq "service") {
    Write-Host "   SERVICIO INSTALADO CORRECTAMENTE" -ForegroundColor Green
} else {
    Write-Host "   TAREA PROGRAMADA INSTALADA CORRECTAMENTE" -ForegroundColor Green
}
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Informacion:" -ForegroundColor Yellow
Write-Host "  Ubicacion:  $InstallDir" -ForegroundColor White
Write-Host "  Metodo:     $(if ($installMethod -eq 'service') { 'Servicio de Windows' } else { 'Tarea Programada' })" -ForegroundColor White
Write-Host "  Log:        $InstallDir\logs\agent.log" -ForegroundColor White
Write-Host ""

Write-Host "El agente se ejecutara:" -ForegroundColor Yellow
Write-Host "  - Al iniciar Windows" -ForegroundColor White
if ($installMethod -eq "task") {
    Write-Host "  - Cada hora automaticamente" -ForegroundColor White
}
Write-Host ""

Write-Host "Comandos utiles:" -ForegroundColor Yellow
if ($installMethod -eq "service") {
    Write-Host "  Ver estado:  sc query $ServiceName" -ForegroundColor White
    Write-Host "  Iniciar:     net start $ServiceName" -ForegroundColor White
    Write-Host "  Detener:     net stop $ServiceName" -ForegroundColor White
    Write-Host "  Desinstalar: & '$PythonExe' '$InstallDir\service_wrapper.py' remove" -ForegroundColor White
} else {
    Write-Host "  Ver estado:  Get-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor White
    Write-Host "  Ejecutar:    Start-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor White
    Write-Host "  Detener:     Stop-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor White
    Write-Host "  Desinstalar: Unregister-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor White
}
Write-Host "  Ver logs:    type '$InstallDir\logs\agent.log'" -ForegroundColor White
Write-Host ""

pause