@echo off
REM IT Monitoring Agent - Windows Uninstaller
REM ==========================================

echo.
echo ============================================================
echo    IT MONITORING AGENT - WINDOWS UNINSTALLER
echo ============================================================
echo.

REM Verificar privilegios de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script requiere privilegios de administrador
    pause
    exit /b 1
)

set INSTALL_DIR=C:\Program Files\ITMonitoringAgent
set SERVICE_NAME=ITMonitoringAgent

echo [1/4] Deteniendo servicio (si existe)...
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    sc stop %SERVICE_NAME%
    sc delete %SERVICE_NAME%
    echo Servicio eliminado
) else (
    echo Servicio no encontrado, continuando...
)

echo [2/4] Eliminando tarea programada (si existe)...
schtasks /Delete /TN "IT Monitoring Agent" /F >nul 2>&1
if %errorLevel% equ 0 (
    echo Tarea programada eliminada
) else (
    echo Tarea no encontrada, continuando...
)

echo [3/4] Eliminando archivos...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo Archivos eliminados
)

echo [4/4] Limpiando variables de entorno...
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v ITMONITOR_HOME /f >nul 2>&1

echo.
echo ============================================================
echo    DESINSTALACION COMPLETADA
echo ============================================================
echo.
pause
