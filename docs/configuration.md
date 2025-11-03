# ⚙️ Guía de Configuración

Esta guía describe todas las opciones de configuración disponibles.

---

## 📄 Archivo Principal: `agent.ini`

### Ubicación del Archivo

- **Windows**: `C:\Program Files\ITMonitoringAgent\config\agent.ini`
- **Linux**: `/opt/it-monitoring-agent/config/agent.ini`
- **macOS**: `/Library/Application Support/ITMonitoringAgent/config/agent.ini`

### Estructura del Archivo
```ini
[agent]
id = 0
name = IT-Agent-001
report_interval = 300

[api]
use_mock = false
base_url = http://your-server:8000/api
timeout = 30
retry_attempts = 3

[collectors]
hardware = true
domain = true
software = true
antivirus = true
office = true
network = true

[logging]
level = INFO
file = logs/agent.log
days_to_keep = 30

[scheduler]
enable_log_cleanup = true
cleanup_logs_hour = 2
enable_auto_update = false
check_updates_hour = 3
enable_health_check = true
health_check_interval = 3600

[updater]
enabled = true
auto_update = false
check_interval = 86400
update_url = http://your-server:8000/api/updates
```

---

## 🔧 Secciones de Configuración

### [agent]

Configuración general del agente.

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `id` | int | ID único del agente (0 = auto-registro) | 0 |
| `name` | string | Nombre descriptivo del agente | IT-Agent-001 |
| `report_interval` | int | Intervalo entre reportes (segundos) | 300 |

**Ejemplos:**
```ini
# Auto-registro (obtiene ID del servidor)
id = 0
name = Laptop-Marketing-01
report_interval = 600  # 10 minutos

# ID manual
id = 123
name = Server-Production-DB
report_interval = 300  # 5 minutos
```

---

### [api]

Configuración de la conexión con el servidor.

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `use_mock` | bool | Usar API simulada (desarrollo) | false |
| `base_url` | string | URL del servidor API | http://localhost:8000/api |
| `timeout` | int | Timeout de conexión (segundos) | 30 |
| `retry_attempts` | int | Intentos de reintento | 3 |

**Ejemplos:**
```ini
# Producción
use_mock = false
base_url = https://api.tuempresa.com/monitoring
timeout = 60
retry_attempts = 5

# Desarrollo/Testing
use_mock = true
base_url = http://localhost:8000/api
timeout = 30
retry_attempts = 3
```

---

### [collectors]

Habilitar/deshabilitar collectors individuales.

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `hardware` | bool | Recolectar información de hardware | true |
| `domain` | bool | Recolectar información de dominio | true |
| `software` | bool | Recolectar software instalado | true |
| `antivirus` | bool | Recolectar estado de antivirus | true |
| `office` | bool | Recolectar información de Office | true |
| `network` | bool | Recolectar configuración de red | true |

**Ejemplos:**
```ini
# Recolección completa
hardware = true
domain = true
software = true
antivirus = true
office = true
network = true

# Solo información básica
hardware = true
domain = true
software = false
antivirus = false
office = false
network = false
```

---

### [logging]

Configuración del sistema de logs.

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `level` | string | Nivel de log (DEBUG, INFO, WARNING, ERROR) | INFO |
| `file` | string | Ruta del archivo de log | logs/agent.log |
| `days_to_keep` | int | Días de retención de logs | 30 |

**Ejemplos:**
```ini
# Producción
level = INFO
file = logs/agent.log
days_to_keep = 30

# Debug
level = DEBUG
file = logs/agent_debug.log
days_to_keep = 7
```

---

### [scheduler]

Configuración de tareas programadas.

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `enable_log_cleanup` | bool | Limpiar logs antiguos | true |
| `cleanup_logs_hour` | int | Hora de limpieza (0-23) | 2 |
| `enable_auto_update` | bool | Habilitar actualizaciones automáticas | false |
| `check_updates_hour` | int | Hora de verificación (0-23) | 3 |
| `enable_health_check` | bool | Verificación de salud | true |
| `health_check_interval` | int | Intervalo de verificación (segundos) | 3600 |

---

### [updater]

Configuración del sistema de actualizaciones.

| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `enabled` | bool | Habilitar actualizador | true |
| `auto_update` | bool | Actualizar automáticamente | false |
| `check_interval` | int | Intervalo de verificación (segundos) | 86400 |
| `update_url` | string | URL del servidor de actualizaciones | - |

---

## 📝 Configuración Avanzada: `logging.yaml`

### Ubicación
- Mismo directorio que `agent.ini`

### Estructura Básica
```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
  
  file_info:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: standard
    filename: logs/agent.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  Agent:
    level: INFO
    handlers: [console, file_info]
    propagate: false

root:
  level: INFO
  handlers: [console, file_info]
```

---

## 🎯 Software Monitoreado: `monitored_software.json`

Define qué software es crítico monitorear.

### Estructura
```json
{
  "security": {
    "required": true,
    "software": [
      {
        "name": "Windows Defender",
        "vendor": "Microsoft",
        "min_version": null,
        "platforms": ["Windows"],
        "alert_if_missing": true
      }
    ]
  }
}
```

### Propiedades

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | string | Nombre del software |
| `vendor` | string | Fabricante |
| `min_version` | string | Versión mínima requerida |
| `platforms` | array | Plataformas soportadas |
| `alert_if_missing` | bool | Alertar si no está instalado |

---

## 🔐 Variables de Entorno

El agente también soporta configuración vía variables de entorno:
```bash
# Linux/macOS
export ITMONITOR_API_URL="https://api.example.com"
export ITMONITOR_AGENT_ID="123"
export ITMONITOR_LOG_LEVEL="DEBUG"

# Windows PowerShell
$env:ITMONITOR_API_URL = "https://api.example.com"
$env:ITMONITOR_AGENT_ID = "123"
$env:ITMONITOR_LOG_LEVEL = "DEBUG"
```

---

## 📊 Ejemplos de Configuración

### Servidor de Producción
```ini
[agent]
id = 0
name = PROD-SERVER-01
report_interval = 300

[api]
use_mock = false
base_url = https://api.company.com/monitoring
timeout = 60
retry_attempts = 5

[collectors]
hardware = true
domain = true
software = true
antivirus = true
office = false
network = true

[logging]
level = WARNING
file = logs/agent.log
days_to_keep = 90
```

### Laptop de Usuario
```ini
[agent]
id = 0
name = LAPTOP-USER-NAME
report_interval = 600

[api]
use_mock = false
base_url = https://api.company.com/monitoring
timeout = 30
retry_attempts = 3

[collectors]
hardware = true
domain = true
software = true
antivirus = true
office = true
network = false

[logging]
level = INFO
file = logs/agent.log
days_to_keep = 30
```

### Ambiente de Desarrollo
```ini
[agent]
id = 999
name = DEV-TEST-AGENT
report_interval = 60

[api]
use_mock = true
base_url = http://localhost:8000/api
timeout = 10
retry_attempts = 1

[collectors]
hardware = true
domain = false
software = true
antivirus = false
office = false
network = false

[logging]
level = DEBUG
file = logs/agent_debug.log
days_to_keep = 7
```

---

## ✅ Validación de Configuración

Verificar que la configuración sea correcta:
```bash
python src/main.py --debug
```

---

## 🔄 Recargar Configuración

Después de cambiar la configuración:

### Windows (Servicio)
```batch
net stop ITMonitoringAgent
net start ITMonitoringAgent
```

### Linux (Systemd)
```bash
sudo systemctl restart it-monitoring-agent
```

### macOS (LaunchD)
```bash
sudo launchctl stop com.empresa.itmonitoringagent
sudo launchctl start com.empresa.itmonitoringagent
```

---

## 📞 Soporte

Si tienes dudas sobre la configuración:
- 📧 Email: support@tuempresa.com
- 📚 Docs: https://docs.tuempresa.com
