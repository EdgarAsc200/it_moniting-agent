#!/bin/bash
# IT Monitoring Agent - macOS Uninstaller
# ========================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - macOS UNINSTALLER"
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

echo "[1/4] Deteniendo daemon..."
if launchctl list | grep -q $LABEL; then
    launchctl unload $PLIST_FILE
    echo "Daemon detenido"
else
    echo "Daemon no esta corriendo"
fi

echo "[2/4] Eliminando configuracion de launchd..."
if [ -f "$PLIST_FILE" ]; then
    rm -f $PLIST_FILE
    echo "Configuracion eliminada"
fi

echo "[3/4] Eliminando archivos..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "Archivos eliminados"
fi

echo "[4/4] Limpiando..."
launchctl remove $LABEL 2>/dev/null || true

echo ""
echo "============================================================"
echo "   DESINSTALACION COMPLETADA"
echo "============================================================"
echo ""
