#!/bin/bash
# IT Monitoring Agent - LaunchD Setup
# ====================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - LAUNCHD SETUP"
echo "============================================================"
echo ""

INSTALL_DIR="/Library/Application Support/ITMonitoringAgent"
PLIST_FILE="/Library/LaunchDaemons/com.empresa.itmonitoringagent.plist"
LABEL="com.empresa.itmonitoringagent"

# Verificar permisos
if [ "$EUID" -ne 0 ]; then 
    echo "Solicitando permisos de administrador..."
    sudo "$0" "$@"
    exit $?
fi

# Verificar instalacion
if [ ! -d "$INSTALL_DIR" ]; then
    echo "ERROR: El agente no esta instalado"
    echo "Ejecuta install.sh primero"
    exit 1
fi

echo "[1/3] Copiando archivo plist..."
cp scripts/macos/com.empresa.agent.plist $PLIST_FILE
chmod 644 $PLIST_FILE
chown root:wheel $PLIST_FILE

echo "[2/3] Cargando daemon..."
launchctl load $PLIST_FILE

echo "[3/3] Iniciando daemon..."
launchctl start $LABEL

echo ""
echo "============================================================"
echo "   DAEMON CONFIGURADO"
echo "============================================================"
echo ""
echo "Comandos utiles:"
echo "  Detener:  sudo launchctl stop $LABEL"
echo "  Iniciar:  sudo launchctl start $LABEL"
echo "  Estado:   sudo launchctl list | grep $LABEL"
echo "  Logs:     tail -f $INSTALL_DIR/logs/agent.log"
echo ""
