# 📦 Guía de Instalación

Esta guía describe cómo instalar el IT Monitoring Agent en diferentes plataformas.

---

## 📋 Requisitos Previos

### Requisitos Mínimos

- **Python**: 3.9 o superior
- **RAM**: 512 MB mínimo, 1 GB recomendado
- **Disco**: 200 MB de espacio libre
- **Red**: Conexión a Internet (para enviar datos al servidor)

### Dependencias del Sistema

#### Windows
- Python 3.9+ (https://www.python.org/downloads/)
- PowerShell 5.1+ (incluido en Windows 10/11)
- Privilegios de Administrador

#### Linux
```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# RHEL/CentOS/Fedora
sudo yum install python3 python3-pip
```

#### macOS
```bash
# Con Homebrew
brew install python3

# O descargar desde python.org
```

---

## 🪟 Instalación en Windows

### Opción 1: Instalación Básica

1. **Descargar o clonar el repositorio:**
```batch
   git clone https://github.com/tu-usuario/it-monitoring-agent.git
   cd it-monitoring-agent
```

2. **Ejecutar instalador:**
```batch
   cd scripts\windows
   .\install.bat
```
   > ⚠️ Ejecutar como **Administrador**

3. **Configurar:**
   Edita `C:\Program Files\ITMonitoringAgent\config\agent.ini`

### Opción 2: Como Servicio de Windows

1. **Instalar primero:**
```batch
   cd scripts\windows
   .\install.bat
```

2. **Instalar como servicio:**
```powershell
   .\install_service.ps1
```

3. **Gestionar el servicio:**
```batch
   # Iniciar
   net start ITMonitoringAgent
   
   # Detener
   net stop ITMonitoringAgent
   
   # Ver estado
   sc query ITMonitoringAgent
```

### Opción 3: Como Tarea Programada

1. **Instalar primero:**
```batch
   cd scripts\windows
   .\install.bat
```

2. **Crear tarea:**
```powershell
   .\create_task.ps1
```

---

## 🐧 Instalación en Linux

### Instalación Automática

1. **Descargar:**
```bash
   git clone https://github.com/tu-usuario/it-monitoring-agent.git
   cd it-monitoring-agent
```

2. **Ejecutar instalador:**
```bash
   cd scripts/linux
   sudo ./install.sh
```

3. **Configurar como servicio systemd:**
```bash
   sudo ./setup_systemd.sh
```

4. **Gestionar el servicio:**
```bash
   # Iniciar
   sudo systemctl start it-monitoring-agent
   
   # Detener
   sudo systemctl stop it-monitoring-agent
   
   # Estado
   sudo systemctl status it-monitoring-agent
   
   # Ver logs
   sudo journalctl -u it-monitoring-agent -f
   
   # Habilitar en arranque
   sudo systemctl enable it-monitoring-agent
```

### Instalación Manual

1. **Crear directorios:**
```bash
   sudo mkdir -p /opt/it-monitoring-agent
   sudo mkdir -p /opt/it-monitoring-agent/logs
```

2. **Copiar archivos:**
```bash
   sudo cp -r src /opt/it-monitoring-agent/
   sudo cp -r config /opt/it-monitoring-agent/
   sudo cp requirements.txt /opt/it-monitoring-agent/
```

3. **Crear entorno virtual:**
```bash
   sudo python3 -m venv /opt/it-monitoring-agent/venv
   sudo /opt/it-monitoring-agent/venv/bin/pip install -r /opt/it-monitoring-agent/requirements.txt
```

4. **Configurar permisos:**
```bash
   sudo useradd -r -s /bin/false itmonitor
   sudo chown -R itmonitor:itmonitor /opt/it-monitoring-agent
```

---

## 🍎 Instalación en macOS

### Instalación Automática

1. **Descargar:**
```bash
   git clone https://github.com/tu-usuario/it-monitoring-agent.git
   cd it-monitoring-agent
```

2. **Ejecutar instalador:**
```bash
   cd scripts/macos
   sudo ./install.sh
```

3. **Configurar como daemon:**
```bash
   sudo ./setup_launchd.sh
```

4. **Gestionar el daemon:**
```bash
   # Iniciar
   sudo launchctl start com.empresa.itmonitoringagent
   
   # Detener
   sudo launchctl stop com.empresa.itmonitoringagent
   
   # Estado
   sudo launchctl list | grep itmonitoringagent
   
   # Ver logs
   tail -f "/Library/Application Support/ITMonitoringAgent/logs/agent.log"
```

### Instalación Manual

1. **Crear directorios:**
```bash
   sudo mkdir -p "/Library/Application Support/ITMonitoringAgent"
   sudo mkdir -p "/Library/Application Support/ITMonitoringAgent/logs"
```

2. **Copiar archivos:**
```bash
   sudo cp -r src "/Library/Application Support/ITMonitoringAgent/"
   sudo cp -r config "/Library/Application Support/ITMonitoringAgent/"
   sudo cp requirements.txt "/Library/Application Support/ITMonitoringAgent/"
```

3. **Crear entorno virtual:**
```bash
   python3 -m venv "/Library/Application Support/ITMonitoringAgent/venv"
   "/Library/Application Support/ITMonitoringAgent/venv/bin/pip" install -r "/Library/Application Support/ITMonitoringAgent/requirements.txt"
```

---

## 🐳 Instalación con Docker
```bash
# Construir imagen
docker build -t it-monitoring-agent .

# Ejecutar contenedor
docker run -d \
  --name it-agent \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  it-monitoring-agent

# Ver logs
docker logs -f it-agent
```

---

## ✅ Verificación de Instalación

### Test Básico
```bash
# Windows
"C:\Program Files\ITMonitoringAgent\venv\Scripts\python.exe" "C:\Program Files\ITMonitoringAgent\src\main.py" --test

# Linux
/opt/it-monitoring-agent/venv/bin/python /opt/it-monitoring-agent/src/main.py --test

# macOS
"/Library/Application Support/ITMonitoringAgent/venv/bin/python" "/Library/Application Support/ITMonitoringAgent/src/main.py" --test
```

### Verificar Recolección
```bash
# Ejecutar una vez manualmente
python src/main.py --once

# Ver el archivo generado
cat inventory.json
```

---

## 🔧 Post-Instalación

1. **Editar configuración:**
   - Configura la URL del servidor API
   - Establece el ID del agente
   - Ajusta el intervalo de reporte

2. **Verificar logs:**
   - Windows: `C:\Program Files\ITMonitoringAgent\logs\agent.log`
   - Linux: `/opt/it-monitoring-agent/logs/agent.log`
   - macOS: `/Library/Application Support/ITMonitoringAgent/logs/agent.log`

3. **Probar conectividad:**
```bash
   python src/main.py --debug
```

---

## 🗑️ Desinstalación

### Windows
```batch
cd scripts\windows
.\uninstall.bat
```

### Linux
```bash
cd scripts/linux
sudo ./uninstall.sh
```

### macOS
```bash
cd scripts/macos
sudo ./uninstall.sh
```

---

## ⚠️ Solución de Problemas

Si tienes problemas durante la instalación, consulta [troubleshooting.md](troubleshooting.md).

---

## 📞 Soporte

- 📧 Email: support@tuempresa.com
- 💬 Issues: https://github.com/tu-usuario/it-monitoring-agent/issues
- 📚 Documentación: https://docs.tuempresa.com
