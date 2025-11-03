#!/bin/bash
# IT Monitoring Agent - Linux Uninstaller
# ========================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - LINUX UNINSTALLER"
echo "============================================================"
echo ""

# Verificar root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Este script debe ejecutarse como root"
    exit 1
fi

INSTALL_DIR="/opt/it-monitoring-agent"
SERVICE_NAME="it-monitoring-agent"
SERVICE_USER="itmonitor"

echo "[1/5] Deteniendo servicio..."
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl stop $SERVICE_NAME
    echo "Servicio detenido"
fi

echo "[2/5] Deshabilitando servicio..."
if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    systemctl disable $SERVICE_NAME
    echo "Servicio deshabilitado"
fi

echo "[3/5] Eliminando archivos del servicio..."
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload

echo "[4/5] Eliminando archivos de instalacion..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf $INSTALL_DIR
    echo "Archivos eliminados"
fi

echo "[5/5] Eliminando usuario del sistema..."
if id "$SERVICE_USER" &>/dev/null; then
    userdel $SERVICE_USER
    echo "Usuario eliminado"
fi

# Eliminar link simbolico
rm -f /usr/local/bin/itmonitor-python

echo ""
echo "============================================================"
echo "   DESINSTALACION COMPLETADA"
echo "============================================================"
echo ""
