#!/bin/bash
# IT Monitoring Agent - macOS Installer
# ======================================

set -e

echo ""
echo "============================================================"
echo "   IT MONITORING AGENT - macOS INSTALLER"
echo "============================================================"
echo ""

# Detectar el directorio del script y el proyecto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "📂 Directorio del proyecto: $PROJECT_DIR"
echo ""

# Variables
INSTALL_DIR="/Library/Application Support/ITMonitoringAgent"
PYTHON_CMD="python3"

echo "[1/7] Verificando Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ ERROR: Python 3 no está instalado"
    echo "Instala con: brew install python3"
    echo "O descarga desde: https://www.python.org/downloads/mac-osx/"
    exit 1
fi
echo "✓ Python encontrado: $($PYTHON_CMD --version)"

echo ""
echo "[2/7] Verificando archivos del proyecto..."
# Verificar que existan los directorios necesarios
if [ ! -d "$PROJECT_DIR/src" ]; then
    echo "❌ ERROR: No se encuentra el directorio 'src'"
    echo "   Esperado en: $PROJECT_DIR/src"
    echo "   Asegúrate de ejecutar desde el directorio del proyecto"
    exit 1
fi

if [ ! -d "$PROJECT_DIR/config" ]; then
    echo "❌ ERROR: No se encuentra el directorio 'config'"
    echo "   Esperado en: $PROJECT_DIR/config"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "❌ ERROR: No se encuentra 'requirements.txt'"
    echo "   Esperado en: $PROJECT_DIR/requirements.txt"
    exit 1
fi
echo "✓ Archivos del proyecto verificados"

echo ""
echo "[3/7] Verificando permisos..."
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Se requieren permisos de administrador"
    echo "   Ejecuta con: sudo bash $0"
    exit 1
fi
echo "✓ Permisos de administrador confirmados"

echo ""
echo "[4/7] Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/data/cache"
mkdir -p "$INSTALL_DIR/data/backup"
echo "✓ Directorios creados en: $INSTALL_DIR"

echo ""
echo "[5/7] Copiando archivos..."
cp -r "$PROJECT_DIR/src" "$INSTALL_DIR/"
echo "  ✓ src/ copiado"

cp -r "$PROJECT_DIR/config" "$INSTALL_DIR/"
echo "  ✓ config/ copiado"

cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"
echo "  ✓ requirements.txt copiado"

# Copiar data si existe
if [ -d "$PROJECT_DIR/data" ]; then
    cp -r "$PROJECT_DIR/data" "$INSTALL_DIR/" 2>/dev/null || true
    echo "  ✓ data/ copiado"
fi

# Copiar README si existe
if [ -f "$PROJECT_DIR/README.md" ]; then
    cp "$PROJECT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true
    echo "  ✓ README.md copiado"
fi

echo ""
echo "[6/7] Creando entorno virtual..."
$PYTHON_CMD -m venv "$INSTALL_DIR/venv"
echo "✓ Entorno virtual creado"

echo ""
echo "[7/7] Instalando dependencias..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet
echo "✓ Dependencias instaladas"

echo ""
echo "[8/8] Configurando permisos..."
chown -R root:wheel "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod -R 777 "$INSTALL_DIR/logs"
chmod -R 777 "$INSTALL_DIR/data"
echo "✓ Permisos configurados"

echo ""
echo "============================================================"
echo "   ✅ INSTALACIÓN COMPLETADA"
echo "============================================================"
echo ""
echo "📂 Ubicación: $INSTALL_DIR"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "  1. Editar configuración:"
echo "     sudo nano \"$INSTALL_DIR/config/agent.ini\""
echo ""
echo "  2. Configurar API:"
echo "     - base_url = http://TU_SERVIDOR:8000/api/v1"
echo "     - api_key = sk_live_..."
echo ""
echo "  3. Registrar agente:"
echo "     sudo \"$INSTALL_DIR/venv/bin/python3\" \"$INSTALL_DIR/src/main.py\" --register"
echo ""
echo "  4. (Opcional) Instalar como servicio:"
echo "     sudo bash \"$PROJECT_DIR/installers/macos/setup_launchd.sh\""
echo ""
