# ============================================================
# INSTALAR IT MONITORING AGENT COMO TAREA PROGRAMADA
# Version sin caracteres especiales Unicode
# ============================================================

cd "C:\Program Files\ITMonitoringAgent"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   IT MONITORING AGENT - INSTALACION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Creando tarea programada..." -ForegroundColor Green

# Eliminar tarea anterior
Unregister-ScheduledTask -TaskName "IT Monitoring Agent" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Tarea anterior eliminada (si existia)" -ForegroundColor Gray

# Crear XML de la tarea
$pythonPath = "$pwd\venv\Scripts\python.exe"
$workDir = "$pwd"

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Agente de monitoreo y recoleccion de inventario IT</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
    <TimeTrigger>
      <Repetition>
        <Interval>PT1H</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2025-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$pythonPath</Command>
      <Arguments>src\main.py</Arguments>
      <WorkingDirectory>$workDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

# Guardar XML temporalmente
$xmlPath = "$env:TEMP\ITMonitoringAgent_Task.xml"
$xml | Out-File -FilePath $xmlPath -Encoding unicode

# Registrar tarea desde XML
Write-Host "Registrando tarea..." -ForegroundColor Green
schtasks /Create /TN "IT Monitoring Agent" /XML $xmlPath /F | Out-Null

# Limpiar archivo temporal
Remove-Item $xmlPath -Force -ErrorAction SilentlyContinue

Write-Host "[OK] Tarea creada exitosamente" -ForegroundColor Green

# Ejecutar tarea
Write-Host ""
Write-Host "Ejecutando tarea..." -ForegroundColor Green
Start-ScheduledTask -TaskName "IT Monitoring Agent"
Start-Sleep 5

# Ver estado
$task = Get-ScheduledTask -TaskName "IT Monitoring Agent"
$taskInfo = Get-ScheduledTaskInfo -TaskName "IT Monitoring Agent"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   INSTALACION COMPLETADA" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Estado de la tarea:" -ForegroundColor Yellow
Write-Host "  Nombre: $($task.TaskName)" -ForegroundColor White
Write-Host "  Estado: $($task.State)" -ForegroundColor White
Write-Host "  Habilitada: $($task.Settings.Enabled)" -ForegroundColor White
Write-Host "  Ultima ejecucion: $($taskInfo.LastRunTime)" -ForegroundColor White
Write-Host "  Proxima ejecucion: $($taskInfo.NextRunTime)" -ForegroundColor White
Write-Host "  Codigo resultado: $($taskInfo.LastTaskResult)" -ForegroundColor White
Write-Host ""

if ($taskInfo.LastTaskResult -eq 0) {
    Write-Host "[OK] Agente funcionando correctamente" -ForegroundColor Green
} else {
    Write-Host "[ADVERTENCIA] Revisa los logs en: logs\agent.log" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Comandos utiles:" -ForegroundColor Cyan
Write-Host "  Ver estado:  Get-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor Gray
Write-Host "  Ejecutar:    Start-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor Gray
Write-Host "  Detener:     Stop-ScheduledTask -TaskName 'IT Monitoring Agent'" -ForegroundColor Gray
Write-Host "  Ver logs:    Get-Content 'C:\Program Files\ITMonitoringAgent\logs\agent.log' -Tail 50" -ForegroundColor Gray
Write-Host "  Ver en vivo: Get-Content 'C:\Program Files\ITMonitoringAgent\logs\agent.log' -Wait" -ForegroundColor Gray
Write-Host ""

pause