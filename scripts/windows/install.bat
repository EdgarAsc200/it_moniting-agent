@echo off
REM IT Monitoring Agent - Windows Installer v2.1
REM ======================================================

echo.
echo ============================================================
echo    IT MONITORING AGENT - WINDOWS INSTALLER v2.1
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
set VENV_DIR=%INSTALL_DIR%\venv

echo [1/11] Verificando Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python no esta instalado
    pause
    exit /b 1
)
python --version
echo.

echo [2/11] Limpiando instalacion anterior...
if exist "%INSTALL_DIR%" (
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1
)

echo [3/11] Creando directorio...
mkdir "%INSTALL_DIR%" 2>nul

echo [4/11] Copiando archivos...
cd /d "%~dp0\..\..\"
xcopy /E /I /Y /Q src "%INSTALL_DIR%\src\" >nul
xcopy /E /I /Y /Q config "%INSTALL_DIR%\config\" >nul
copy /Y requirements.txt "%INSTALL_DIR%\" >nul
mkdir "%INSTALL_DIR%\logs" 2>nul
mkdir "%INSTALL_DIR%\data\cache" 2>nul
mkdir "%INSTALL_DIR%\data\backup" 2>nul

echo [5/11] Configurando permisos...
icacls "%INSTALL_DIR%\logs" /grant Everyone:F /T >nul 2>&1
icacls "%INSTALL_DIR%\data" /grant Everyone:F /T >nul 2>&1

echo [6/11] Creando entorno virtual...
cd /d "%INSTALL_DIR%"
python -m venv venv --clear
if %errorLevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo [7/11] Instalando pip...
curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py 2>nul
if exist get-pip.py (
    "%VENV_DIR%\Scripts\python.exe" get-pip.py >nul
    del get-pip.py
)

echo [8/11] Instalando dependencias...
"%VENV_DIR%\Scripts\pip.exe" install --upgrade pip --quiet
"%VENV_DIR%\Scripts\pip.exe" install psutil requests APScheduler pyyaml --quiet

echo [9/11] Corrigiendo encoding...

REM Crear script Python simple
echo import sys, shutil > "%TEMP%\fix.py"
echo main = r"%INSTALL_DIR%\src\main.py" >> "%TEMP%\fix.py"
echo shutil.copy(main, main + ".bak") >> "%TEMP%\fix.py"
echo with open(main, "r", encoding="utf-8") as f: >> "%TEMP%\fix.py"
echo     lines = f.readlines() >> "%TEMP%\fix.py"
echo header = "# -*- coding: utf-8 -*-\nimport sys\nimport os\nif sys.platform=='win32':\n    import io\n    if hasattr(sys.stdout,'buffer'): sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')\n    if hasattr(sys.stderr,'buffer'): sys.stderr=io.TextIOWrapper(sys.stderr.buffer,encoding='utf-8',errors='replace')\n    try:\n        import ctypes;ctypes.windll.kernel32.SetConsoleOutputCP(65001)\n    except:pass\n\n" >> "%TEMP%\fix.py"
echo if "CONFIGURACION" not in "".join(lines): >> "%TEMP%\fix.py"
echo     lines.insert(0, header) >> "%TEMP%\fix.py"
echo content = "".join(lines) >> "%TEMP%\fix.py"
echo for old,new in [("\\u2554","+"),("\\u2557","+"),("\\u255A","+"),("\\u255D","+"),("\\u2550","="),("\\u2551","|"),("\\u2713","[OK]"),("\\u274C","[X]"),("\\u26A0","[!]")]: >> "%TEMP%\fix.py"
echo     content = content.replace(old, new) >> "%TEMP%\fix.py"
echo with open(main, "w", encoding="utf-8", newline="\r\n") as f: >> "%TEMP%\fix.py"
echo     f.write(content) >> "%TEMP%\fix.py"
echo print("   Encoding corregido") >> "%TEMP%\fix.py"

python "%TEMP%\fix.py"
if %errorLevel% equ 0 (
    echo    OK
) else (
    echo    ADVERTENCIA: No se pudo corregir encoding
)
del "%TEMP%\fix.py" 2>nul

echo [10/11] Creando log...
echo # IT Monitoring Agent > "%INSTALL_DIR%\logs\agent.log"

echo [11/11] Verificando...
echo.
chcp 65001 >nul
"%VENV_DIR%\Scripts\python.exe" src\main.py --test

if %errorLevel% equ 0 (
    echo.
    echo ============================================================
    echo    INSTALACION COMPLETADA
    echo ============================================================
    echo.
    echo Ubicacion: %INSTALL_DIR%
    echo.
    echo Siguiente paso:
    echo   powershell -ExecutionPolicy Bypass "%INSTALL_DIR%\scripts\windows\install_service.ps1"
    echo.
) else (
    echo.
    echo Hubo errores. Revisa arriba.
    echo.
)

pause