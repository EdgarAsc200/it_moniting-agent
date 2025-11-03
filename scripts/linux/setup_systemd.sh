#!/bin/bash
# IT Monitoring Agent - Systemd Setup
# ====================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - SYSTEMD SETUP"
echo "============================================================"
echo ""

# Verificar root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Este script debe ejecutarse como root"
    exit 1
fi

INSTALL_DIR="/opt/it-monitoring-agent"
SERVICE_FILE="/etc/systemd/system/it-monitoring-agent.service"

# Verificar instalacion
if [ ! -d "$INSTALL_DIR" ]; then
    echo "ERROR: El agente no esta instalado"
    echo "Ejecuta install.sh primero"
    exit 1
fi

echo "[1/3] Creando archivo de servicio..."
cp scripts/linux/agent.service $SERVICE_FILE

echo "[2/3] Recargando systemd..."
systemctl daemon-reload

echo "[3/3] Habilitando servicio..."
systemctl enable it-monitoring-agent.service

echo ""
echo "============================================================"
echo "   SERVICIO CONFIGURADO"
echo "============================================================"
echo ""
echo "Comandos utiles:"
echo "  Iniciar:  sudo systemctl start it-monitoring-agent"
echo "  Detener:  sudo systemctl stop it-monitoring-agent"
echo "  Estado:   sudo systemctl status it-monitoring-agent"
echo "  Logs:     sudo journalctl -u it-monitoring-agent -f"
echo ""
read -p "Iniciar servicio ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    systemctl start it-monitoring-agent
    echo "Servicio iniciado"
    systemctl status it-monitoring-agent
fi
echo ""
