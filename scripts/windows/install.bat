cd C:\it_moniting-agent\scripts\windows

@echo off
REM IT Monitoring Agent - Windows Installer (CORREGIDO)
REM ======================================================

echo.
echo ============================================================
echo    IT MONITORING AGENT - WINDOWS INSTALLER
echo ============================================================
echo.

REM Verificar privilegios de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script requiere privilegios de administrador
    echo.
    echo Por favor:
    echo 1. Click derecho en install.bat
    echo 2. Selecciona "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

REM Variables
set INSTALL_DIR=C:\Program Files\ITMonitoringAgent
set PYTHON_MIN_VERSION=3.9
set VENV_DIR=%INSTALL_DIR%\venv

echo [1/8] Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo.
    echo Por favor, instala Python 3.9+ desde: https://www.python.org/downloads/
    echo Durante la instalacion, marca "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo.

echo [2/8] Limpiando instalacion anterior...
if exist "%INSTALL_DIR%" (
    echo    Eliminando directorio anterior...
    
    REM Detener procesos de Python que puedan estar usando archivos
    taskkill /F /IM python.exe >nul 2>&1
    taskkill /F /IM pythonw.exe >nul 2>&1
    
    REM Esperar un momento
    timeout /t 2 /nobreak >nul
    
    REM Eliminar directorio
    rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1
    
    REM Verificar que se elimino
    if exist "%INSTALL_DIR%" (
        echo    ADVERTENCIA: No se pudo eliminar completamente el directorio anterior
        echo    Algunos archivos pueden estar en uso
        echo.
    )
)

echo [3/8] Creando directorio de instalacion...
mkdir "%INSTALL_DIR%" 2>nul

echo [4/8] Copiando archivos...
cd /d "%~dp0\..\..\"
xcopy /E /I /Y /Q src "%INSTALL_DIR%\src\" >nul
xcopy /E /I /Y /Q config "%INSTALL_DIR%\config\" >nul
xcopy /E /I /Y /Q data "%INSTALL_DIR%\data\" >nul
copy /Y requirements.txt "%INSTALL_DIR%\" >nul
copy /Y README.md "%INSTALL_DIR%\" >nul 2>&1

REM Crear directorios adicionales
mkdir "%INSTALL_DIR%\logs" 2>nul
mkdir "%INSTALL_DIR%\data\cache" 2>nul
mkdir "%INSTALL_DIR%\data\backup" 2>nul

echo [5/8] Creando entorno virtual...
echo    Esto puede tomar un momento...

REM Ir al directorio de instalacion
cd /d "%INSTALL_DIR%"

REM Intentar crear venv con diferentes metodos
python -m venv venv --without-pip 2>nul
if %errorLevel% neq 0 (
    echo    Intentando metodo alternativo...
    python -m venv venv --clear
)

if %errorLevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    echo.
    echo Posibles soluciones:
    echo 1. Desactiva temporalmente el antivirus
    echo 2. Ejecuta: python -m pip install --upgrade pip
    echo 3. Reinstala Python marcando "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM Verificar que se creo correctamente
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ERROR: El entorno virtual no se creo correctamente
    pause
    exit /b 1
)

echo    OK - Entorno virtual creado
echo.

echo [6/8] Instalando pip en el entorno virtual...
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
"%VENV_DIR%\Scripts\python.exe" get-pip.py
del get-pip.py

echo [7/8] Instalando dependencias...
echo    Esto puede tomar varios minutos...
"%VENV_DIR%\Scripts\pip.exe" install --upgrade pip --quiet
"%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt --quiet
"%VENV_DIR%\Scripts\pip.exe" install psutil requests APScheduler PyYAML python-dateutil packaging

if %errorLevel% neq 0 (
    echo ERROR: Fallo al instalar dependencias
    echo.
    echo Intentando instalacion manual...
    "%VENV_DIR%\Scripts\pip.exe" install psutil
    "%VENV_DIR%\Scripts\pip.exe" install requests
    "%VENV_DIR%\Scripts\pip.exe" install APScheduler
    "%VENV_DIR%\Scripts\pip.exe" install pyyaml
)

echo [8/8] Configurando permisos...
icacls "%INSTALL_DIR%\logs" /grant Users:(OI)(CI)M >nul 2>&1
icacls "%INSTALL_DIR%\data" /grant Users:(OI)(CI)M >nul 2>&1

echo.
echo ============================================================
echo    INSTALACION COMPLETADA
echo ============================================================
echo.
echo Ubicacion: %INSTALL_DIR%
echo.
echo Proximos pasos:
echo   1. Edita la configuracion: %INSTALL_DIR%\config\agent.ini
echo   2. Ejecuta para instalar servicio o tarea:
echo.
echo      cd "%INSTALL_DIR%"
echo      powershell -ExecutionPolicy Bypass -File scripts\windows\install_service_v2_fixed.ps1
echo.
echo   O para tarea programada directamente:
echo      powershell -ExecutionPolicy Bypass -File scripts\windows\create_task_fixed.ps1
echo.
pause