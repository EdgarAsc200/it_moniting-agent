# Ir al directorio del proyecto
cd C:\it_moniting-agent

# Crear la versión corregida
cat > scripts/windows/install_service.ps1 << 'EOF'
# IT Monitoring Agent - Windows Service Installer
# ================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   IT MONITORING AGENT - SERVICE INSTALLER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar privilegios de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Este script requiere privilegios de administrador" -ForegroundColor Red
    Write-Host "Ejecuta PowerShell como Administrador" -ForegroundColor Yellow
    pause
    exit 1
}

# Variables
$ServiceName = "ITMonitoringAgent"
$DisplayName = "IT Monitoring Agent"
$Description = "Agente de monitoreo y recoleccion de inventario IT"
$InstallDir = "C:\Program Files\ITMonitoringAgent"
$PythonExe = "$InstallDir\venv\Scripts\python.exe"
$MainScript = "$InstallDir\src\main.py"

# Verificar que existe la instalacion
if (-not (Test-Path $InstallDir)) {
    Write-Host "ERROR: El agente no esta instalado en $InstallDir" -ForegroundColor Red
    Write-Host "Ejecuta install.bat primero" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[1/7] Verificando instalacion..." -ForegroundColor Green
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python no encontrado en $PythonExe" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path $MainScript)) {
    Write-Host "ERROR: Script principal no encontrado en $MainScript" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[2/7] Instalando dependencias Python..." -ForegroundColor Green
Write-Host "   Esto puede tomar algunos minutos..." -ForegroundColor Yellow

# Instalar requirements.txt (incluye psutil)
& "$InstallDir\venv\Scripts\pip.exe" install -r "$InstallDir\requirements.txt" --quiet

# Verificar que psutil se instaló
$psutilInstalled = & "$PythonExe" -c "import psutil; print('OK')" 2>&1
if ($psutilInstalled -ne "OK") {
    Write-Host "ERROR: No se pudo instalar psutil" -ForegroundColor Red
    Write-Host "Intentando instalacion manual..." -ForegroundColor Yellow
    & "$InstallDir\venv\Scripts\pip.exe" install psutil
}

Write-Host "[3/7] Instalando modulos de servicio Windows..." -ForegroundColor Green
& "$InstallDir\venv\Scripts\pip.exe" install pywin32 --quiet

Write-Host "[4/7] Deteniendo servicio existente (si existe)..." -ForegroundColor Green
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "   Deteniendo servicio existente..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Desinstalar servicio existente
    Write-Host "   Eliminando servicio existente..." -ForegroundColor Yellow
    & "$PythonExe" "$InstallDir\service_wrapper.py" remove 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "[5/7] Creando wrapper script..." -ForegroundColor Green
$WrapperScript = @"
# service_wrapper.py
# IT Monitoring Agent - Windows Service Wrapper
import sys
import os
import servicemanager
import win32serviceutil
import win32service
import win32event

# Configurar paths
INSTALL_DIR = r'$InstallDir'
sys.path.insert(0, os.path.join(INSTALL_DIR, 'src'))
os.chdir(INSTALL_DIR)

# Importar después de configurar paths
from main import main as agent_main

class ITMonitoringAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = '$ServiceName'
    _svc_display_name_ = '$DisplayName'
    _svc_description_ = '$Description'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
    
    def main(self):
        try:
            # Cambiar al directorio de trabajo
            os.chdir(INSTALL_DIR)
            
            # Ejecutar el agente
            agent_main()
        except Exception as e:
            servicemanager.LogErrorMsg(f'Error en servicio: {e}')

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ITMonitoringAgentService)
"@

$WrapperScript | Out-File -FilePath "$InstallDir\service_wrapper.py" -Encoding UTF8

Write-Host "[6/7] Verificando instalacion..." -ForegroundColor Green
# Test rápido que main.py se puede importar
$testImport = & "$PythonExe" -c "import sys; sys.path.insert(0, r'$InstallDir\src'); from core.agent import Agent; print('OK')" 2>&1
if ($testImport -ne "OK") {
    Write-Host "ADVERTENCIA: Hubo un problema al verificar la instalacion" -ForegroundColor Yellow
    Write-Host "Detalle: $testImport" -ForegroundColor Gray
    Write-Host "Continuando de todas formas..." -ForegroundColor Yellow
}

Write-Host "[7/7] Registrando servicio..." -ForegroundColor Green
try {
    & "$PythonExe" "$InstallDir\service_wrapper.py" install
    
    # Configurar servicio para inicio automatico
    Set-Service -Name $ServiceName -StartupType Automatic -ErrorAction Stop
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   SERVICIO INSTALADO CORRECTAMENTE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Comandos utiles:" -ForegroundColor Yellow
    Write-Host "  Iniciar:  net start $ServiceName" -ForegroundColor White
    Write-Host "  Detener:  net stop $ServiceName" -ForegroundColor White
    Write-Host "  Estado:   sc query $ServiceName" -ForegroundColor White
    Write-Host "  Logs:     type `"$InstallDir\logs\agent.log`"" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Iniciar servicio ahora? (S/N)"
    
    if ($response -eq 'S' -or $response -eq 's' -or $response -eq 'Y' -or $response -eq 'y') {
        Write-Host "Iniciando servicio..." -ForegroundColor Green
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 2
        
        # Verificar estado
        $serviceStatus = Get-Service -Name $ServiceName
        if ($serviceStatus.Status -eq 'Running') {
            Write-Host "✓ Servicio iniciado correctamente" -ForegroundColor Green
        } else {
            Write-Host "! El servicio no esta corriendo. Estado: $($serviceStatus.Status)" -ForegroundColor Yellow
            Write-Host "  Revisa los logs en: $InstallDir\logs\agent.log" -ForegroundColor Yellow
        }
    }
    
} catch {
    Write-Host ""
    Write-Host "ERROR al registrar el servicio:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Intenta instalar manualmente:" -ForegroundColor Yellow
    Write-Host "  cd `"$InstallDir`"" -ForegroundColor White
    Write-Host "  venv\Scripts\python.exe service_wrapper.py install" -ForegroundColor White
    pause
    exit 1
}

Write-Host ""
pause
EOF

echo "✅ Script corregido guardado"