#!/bin/bash
# IT Monitoring Agent - macOS Installer
# ======================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - macOS INSTALLER"
echo "============================================================"
echo ""

# Variables
INSTALL_DIR="/Library/Application Support/ITMonitoringAgent"
PYTHON_CMD="python3"

echo "[1/7] Verificando Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "ERROR: Python 3 no esta instalado"
    echo "Instala con: brew install python3"
    echo "O descarga desde: https://www.python.org/downloads/mac-osx/"
    exit 1
fi

echo "[2/7] Verificando permisos..."
if [ "$EUID" -ne 0 ]; then 
    echo "Solicitando permisos de administrador..."
    sudo "$0" "$@"
    exit $?
fi

echo "[3/7] Creando directorio de instalacion..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/data/cache"
mkdir -p "$INSTALL_DIR/data/backup"

echo "[4/7] Copiando archivos..."
cp -r src "$INSTALL_DIR/"
cp -r config "$INSTALL_DIR/"
cp -r data "$INSTALL_DIR/" 2>/dev/null || true
cp requirements.txt "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/" 2>/dev/null || true

echo "[5/7] Creando entorno virtual..."
$PYTHON_CMD -m venv "$INSTALL_DIR/venv"

echo "[6/7] Instalando dependencias..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo "[7/7] Configurando permisos..."
chown -R root:wheel "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod -R 777 "$INSTALL_DIR/logs"
chmod -R 777 "$INSTALL_DIR/data"

echo ""
echo "============================================================"
echo "   INSTALACION COMPLETADA"
echo "============================================================"
echo ""
echo "Ubicacion: $INSTALL_DIR"
echo ""
echo "Proximos pasos:"
echo "  1. Edita la configuracion: $INSTALL_DIR/config/agent.ini"
echo "  2. Ejecuta: sudo ./scripts/macos/setup_launchd.sh"
echo ""
