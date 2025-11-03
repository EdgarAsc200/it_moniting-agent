#!/bin/bash
# IT Monitoring Agent - Linux Installer
# ======================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - LINUX INSTALLER"
echo "============================================================"
echo ""

# Verificar root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Este script debe ejecutarse como root"
    echo "Usa: sudo ./install.sh"
    exit 1
fi

# Variables
INSTALL_DIR="/opt/it-monitoring-agent"
SERVICE_USER="itmonitor"
PYTHON_CMD="python3"
MIN_PYTHON_VERSION="3.9"

echo "[1/8] Verificando Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "ERROR: Python 3 no esta instalado"
    echo "Instala con: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

echo "[2/8] Instalando dependencias del sistema..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3-pip python3-venv
elif command -v yum &> /dev/null; then
    yum install -y python3-pip python3-virtualenv
elif command -v dnf &> /dev/null; then
    dnf install -y python3-pip python3-virtualenv
fi

echo "[3/8] Creando usuario del sistema..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d $INSTALL_DIR $SERVICE_USER
    echo "Usuario $SERVICE_USER creado"
else
    echo "Usuario $SERVICE_USER ya existe"
fi

echo "[4/8] Creando directorio de instalacion..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/data/cache
mkdir -p $INSTALL_DIR/data/backup

echo "[5/8] Copiando archivos..."
cp -r src $INSTALL_DIR/
cp -r config $INSTALL_DIR/
cp -r data $INSTALL_DIR/ 2>/dev/null || true
cp requirements.txt $INSTALL_DIR/
cp README.md $INSTALL_DIR/ 2>/dev/null || true

echo "[6/8] Creando entorno virtual..."
$PYTHON_CMD -m venv $INSTALL_DIR/venv

echo "[7/8] Instalando dependencias Python..."
$INSTALL_DIR/venv/bin/pip install --upgrade pip
$INSTALL_DIR/venv/bin/pip install -r $INSTALL_DIR/requirements.txt

echo "[8/8] Configurando permisos..."
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod -R 775 $INSTALL_DIR/logs
chmod -R 775 $INSTALL_DIR/data

# Crear link simbolico
ln -sf $INSTALL_DIR/venv/bin/python /usr/local/bin/itmonitor-python

echo ""
echo "============================================================"
echo "   INSTALACION COMPLETADA"
echo "============================================================"
echo ""
echo "Ubicacion: $INSTALL_DIR"
echo "Usuario: $SERVICE_USER"
echo ""
echo "Proximos pasos:"
echo "  1. Edita la configuracion: $INSTALL_DIR/config/agent.ini"
echo "  2. Ejecuta: sudo ./scripts/linux/setup_systemd.sh"
echo ""
