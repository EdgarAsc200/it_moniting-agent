@echo off
REM =========================================
REM IT Monitoring Agent - Windows Installer
REM =========================================

echo.
echo ============================================================
echo    IT MONITORING AGENT - WINDOWS INSTALLER
echo ============================================================
echo.

REM Verificar privilegios de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script requiere privilegios de administrador
    echo Por favor, ejecuta como Administrador
    pause
    exit /b 1
)

REM Variables
set "INSTALL_DIR=C:\Program Files\ITMonitoringAgent"
set "VENV_DIR=%INSTALL_DIR%\venv"
set "PYTHON_MIN_VERSION=3.9"

echo [1/6] Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo Por favor, instala Python %PYTHON_MIN_VERSION% o superior
    echo Descarga desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/6] Creando directorio de instalacion...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [3/6] Copiando archivos...
if exist "%~dp0..\..\src" xcopy /E /I /Y "%~dp0..\..\src" "%INSTALL_DIR%\src\" >nul
if exist "%~dp0..\..\config" xcopy /E /I /Y "%~dp0..\..\config" "%INSTALL_DIR%\config\" >nul
if exist "%~dp0..\..\data" xcopy /E /I /Y "%~dp0..\..\data" "%INSTALL_DIR%\data\" >nul
if exist "%~dp0..\..\requirements.txt" copy /Y "%~dp0..\..\requirements.txt" "%INSTALL_DIR%\" >nul
if exist "%~dp0..\..\README.md" copy /Y "%~dp0..\..\README.md" "%INSTALL_DIR%\" >nul



echo [4/6] Creando entorno virtual...
python -m venv "%VENV_DIR%"

echo [5/6] Instalando dependencias...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul
"%VENV_DIR%\Scripts\pip.exe" install -r "%INSTALL_DIR%\requirements.txt"

echo [6/6] Configurando variables de entorno...
setx ITMONITOR_HOME "%INSTALL_DIR%" /M

echo.
echo ============================================================
echo    INSTALACION COMPLETADA
echo ============================================================
echo.
echo Ubicacion: %INSTALL_DIR%
echo.
echo Proximos pasos:
echo   1. Edita la configuracion: %INSTALL_DIR%\config\agent.ini
echo   2. Ejecuta: scripts\windows\install_service.ps1  (para servicio)
echo      O bien: scripts\windows\create_task.ps1       (para tarea programada)
echo.
pause
