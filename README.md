# 🖥️ IT Monitoring Agent

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/tu-usuario/it-monitoring-agent)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/tu-usuario/it-monitoring-agent)

**Agente multiplataforma de monitoreo y recolección de datos de activos TI**

[Características](#-características) •
[Instalación](#-instalación) •
[Configuración](#-configuración) •
[Uso](#-uso) •
[Documentación](#-documentación)

</div>

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Collectors](#-collectors)
- [Scheduler](#-scheduler)
- [API Client](#-api-client)
- [Modos de Ejecución](#-modos-de-ejecución)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## 📖 Descripción

**IT Monitoring Agent** es un agente ligero y multiplataforma diseñado para recopilar información detallada de activos de TI (hardware, software, seguridad, red, etc.) y enviarla a un servidor central para su monitoreo y análisis.

### ¿Por qué usar este agente?

- ✅ **Multiplataforma**: Funciona en Windows, Linux y macOS
- ✅ **Ligero**: Consumo mínimo de recursos del sistema
- ✅ **Modular**: Arquitectura basada en collectors extensibles
- ✅ **Automatizado**: Scheduler integrado para tareas programadas
- ✅ **Configurable**: Amplia configuración sin modificar código
- ✅ **Sin dependencias externas**: Usa solo bibliotecas estándar de Python

---

## ✨ Características

### 🔍 Recolección de Datos

- **Hardware**: CPU, RAM, disco, BIOS, placas base
- **Software**: Lista completa de aplicaciones instaladas
- **Dominio**: Información de Active Directory (Windows)
- **Antivirus**: Estado de protección y seguridad
- **Microsoft Office**: Versiones y licencias
- **Red**: Interfaces, IPs, DNS, gateway

### ⚙️ Funcionalidades

- **Scheduler integrado**: Tareas programadas automáticas
- **Múltiples modos de ejecución**: Debug, Test, Once, Continuo
- **API Client**: Comunicación con servidor central (Mock y Real)
- **Logging avanzado**: Registros detallados configurables
- **Auto-registro**: Registro automático en el servidor
- **Health checks**: Monitoreo del estado del agente
- **Limpieza automática**: Mantenimiento de logs antiguos

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    IT Monitoring Agent                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Scheduler   │      │  API Client  │                │
│  │  (Tareas)     │◄────►│  (HTTP)      │                │
│  └──────────────┘      └──────────────┘                │
│         │                      │                         │
│         ▼                      ▼                         │
│  ┌─────────────────────────────────────────────┐        │
│  │              Agent Core                      │        │
│  │         (Coordinación y Control)             │        │
│  └─────────────────────────────────────────────┘        │
│         │                                                │
│         ▼                                                │
│  ┌─────────────────────────────────────────────┐        │
│  │              Collectors                      │        │
│  ├─────────────────────────────────────────────┤        │
│  │ • HardwareCollector                         │        │
│  │ • SoftwareCollector                         │        │
│  │ • DomainCollector                           │        │
│  │ • AntivirusCollector                        │        │
│  │ • OfficeCollector                           │        │
│  │ • NetworkCollector                          │        │
│  └─────────────────────────────────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Requisitos

### Software

- **Python 3.8+** (3.9+ recomendado)
- Sistema operativo: Windows 10+, Linux (cualquier distribución moderna), macOS 10.15+

### Permisos

- **Windows**: Usuario estándar (administrador para algunas funciones de dominio)
- **Linux/macOS**: Usuario estándar (sudo para algunos comandos del sistema)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/it-monitoring-agent.git
cd it-monitoring-agent
```

### 2. Crear estructura de directorios

```bash
mkdir -p logs data config
```

### 3. Configurar el agente

```bash
# Copiar archivo de configuración de ejemplo
cp config/agent.ini.example config/agent.ini

# Editar según tus necesidades
nano config/agent.ini
```

### 4. (Opcional) Crear entorno virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 5. Verificar instalación

```bash
python src/main.py --debug
```

---

## ⚙️ Configuración

### Archivo de configuración: `config/agent.ini`

```ini
[agent]
# Configuración del agente
version = 1.0.0
id = 0                    # 0 = no registrado (se asigna automáticamente)
name = IT-Agent
report_interval = 300     # Intervalo de reporte en segundos (5 minutos)

[api]
# Configuración de API
base_url = http://localhost:5000/api
use_mock = true           # true = modo simulación, false = servidor real
api_key =                 # API key (opcional)
timeout = 30              # Timeout en segundos
verify_ssl = true         # Verificar certificados SSL

[collectors]
# Habilitar/deshabilitar collectors
hardware = true
domain = true
software = true
antivirus = true
office = true
network = true

[scheduler]
# Tareas programadas
enable_log_cleanup = true
cleanup_logs_hour = 2           # Hora para limpieza de logs (2 AM)
enable_auto_update = false      # Auto-actualización
check_updates_hour = 3          # Hora para verificar updates (3 AM)
enable_health_check = true
health_check_interval = 3600    # Health check cada hora
enable_weekly_report = false

[logging]
# Configuración de logging
level = INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
file = logs/agent.log
console = true
days_to_keep = 30              # Retención de logs en días
```

---

## 🎮 Uso

### Comandos Principales

```bash
# Modo debug - Solo validar configuración (sin ejecutar)
python src/main.py --debug

# Registrar agente en el servidor
python src/main.py --register

# Modo test - Recolectar datos sin enviar al servidor
python src/main.py --test

# Ejecutar una sola vez
python src/main.py --once

# Modo continuo (servicio) - Default
python src/main.py

# Ayuda
python src/main.py --help
```

### Opciones Disponibles

| Opción | Descripción |
|--------|-------------|
| `--config PATH` | Usar archivo de configuración personalizado |
| `--debug` | Modo debug: validar configuración sin ejecutar |
| `--register` | Registrar agente en el servidor |
| `--test` | Recolectar datos sin enviar al servidor |
| `--once` | Ejecutar una sola recolección |
| `--version` | Mostrar versión del agente |
| `--no-banner` | No mostrar banner de inicio |

---

## 🔍 Collectors

### HardwareCollector

Recopila información de hardware del sistema:

- Información del CPU (modelo, cores, frecuencia)
- Memoria RAM (total, disponible, uso)
- Discos (capacidad, uso, tipo)
- Información del sistema (fabricante, modelo, serial)
- BIOS/UEFI
- Placa base

### SoftwareCollector

Recopila lista de software instalado:

- Nombre de la aplicación
- Versión
- Fabricante
- Fecha de instalación
- Tamaño

### DomainCollector

Información de dominio de Active Directory (Windows):

- Nombre del dominio
- Controlador de dominio
- Usuario actual
- Grupo de trabajo
- Estado de unión al dominio

### AntivirusCollector

Estado de seguridad del sistema:

- Antivirus instalado (nombre, versión)
- Estado de protección en tiempo real
- Última actualización de definiciones
- Último escaneo realizado
- Estado del firewall
- Windows Defender / XProtect / ClamAV

### OfficeCollector

Información de Microsoft Office:

- Versión de Office instalada
- Build number
- Tipo de licencia
- Estado de licencia
- Aplicaciones instaladas (Word, Excel, PowerPoint, etc.)
- Arquitectura (32/64 bits)

### NetworkCollector

Configuración de red:

- Interfaces de red activas
- Direcciones IP (IPv4/IPv6)
- Máscaras de red
- Gateway predeterminado
- Servidores DNS
- Dirección MAC
- Estado de conexión

---

## ⏰ Scheduler

El agente incluye un scheduler integrado que ejecuta tareas automáticamente en segundo plano.

### Tareas Programadas

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `collect_and_send_data` | Cada 5 min | Recolección y envío de datos |
| `cleanup_old_logs` | Diario 2 AM | Limpieza de logs antiguos |
| `system_health_check` | Cada hora | Verificación del estado del agente |
| `check_for_updates` | Diario 3 AM | Verificar actualizaciones (opcional) |

### Configurar Tareas

Las tareas se configuran en `config/agent.ini`:

```ini
[scheduler]
enable_log_cleanup = true
cleanup_logs_hour = 2
enable_health_check = true
health_check_interval = 3600
```

---

## 🌐 API Client

El agente se comunica con un servidor central mediante HTTP/HTTPS.

### Modos de Operación

#### MockAPIClient (Desarrollo)

```ini
[api]
use_mock = true
```

- No requiere servidor real
- Simula respuestas exitosas
- Ideal para desarrollo y testing
- ID de agente simulado: 999

#### APIClient (Producción)

```ini
[api]
use_mock = false
base_url = https://tu-servidor.com/api
api_key = tu-api-key-aqui
verify_ssl = true
```

### Endpoints Utilizados

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/agents/register` | Registrar nuevo agente |
| POST | `/agents/{id}/inventory` | Enviar datos de inventario |
| POST | `/agents/{id}/heartbeat` | Enviar heartbeat |
| GET | `/agents/{id}/config` | Obtener configuración |
| GET | `/agents/updates` | Verificar actualizaciones |

---

## 🎯 Modos de Ejecución

### 1. Modo Debug (`--debug`)

**Propósito**: Validar configuración sin ejecutar tareas

```bash
python src/main.py --debug
```

**Qué hace**:
- ✅ Valida configuración
- ✅ Muestra información del sistema
- ✅ Lista collectors habilitados
- ✅ Muestra tareas programadas
- ❌ NO ejecuta tareas
- ❌ NO recolecta datos

**Cuándo usar**: Verificar configuración antes de desplegar

---

### 2. Modo Register (`--register`)

**Propósito**: Registrar agente en el servidor

```bash
python src/main.py --register
```

**Qué hace**:
- ✅ Se conecta al servidor
- ✅ Envía información de registro
- ✅ Obtiene agent_id
- ✅ Guarda configuración
- ❌ NO ejecuta recolección

**Cuándo usar**: Primera instalación o después de reinstalar

---

### 3. Modo Test (`--test`)

**Propósito**: Probar recolección sin enviar datos

```bash
python src/main.py --test
```

**Qué hace**:
- ✅ Recolecta datos de todos los collectors
- ✅ Muestra datos en pantalla (JSON)
- ❌ NO envía datos al servidor

**Cuándo usar**: Verificar que los collectors funcionan correctamente

---

### 4. Modo Once (`--once`)

**Propósito**: Ejecutar una sola recolección completa

```bash
python src/main.py --once
```

**Qué hace**:
- ✅ Recolecta datos
- ✅ Envía datos al servidor
- ✅ Sale del programa
- ❌ NO inicia scheduler

**Cuándo usar**: Ejecución manual o cron jobs

---

### 5. Modo Continuo (Default)

**Propósito**: Servicio en segundo plano con tareas programadas

```bash
python src/main.py
```

**Qué hace**:
- ✅ Inicia scheduler
- ✅ Configura tareas programadas
- ✅ Recolecta datos periódicamente
- ✅ Envía datos al servidor
- ✅ Ejecuta mantenimiento automático
- ✅ Se mantiene ejecutando hasta Ctrl+C

**Cuándo usar**: Producción, monitoreo continuo

---

## 📁 Estructura del Proyecto

```
it-monitoring-agent/
│
├── 📂 config/                    # Archivos de configuración
│   ├── agent.ini                 # Configuración principal
│   └── agent.ini.example         # Plantilla de configuración
│
├── 📂 src/                       # Código fuente
│   ├── 📂 core/                  # Módulos principales
│   │   ├── __init__.py
│   │   ├── agent.py              # Agente principal
│   │   ├── api_client.py         # Cliente HTTP
│   │   ├── config.py             # Gestión de configuración
│   │   ├── logger.py             # Sistema de logging
│   │   └── scheduler.py          # Programador de tareas
│   │
│   ├── 📂 collectors/            # Recolectores de datos
│   │   ├── __init__.py
│   │   ├── base_collector.py    # Clase base abstracta
│   │   ├── hardware_collector.py
│   │   ├── software_collector.py
│   │   ├── domain_collector.py
│   │   ├── antivirus_collector.py
│   │   ├── office_collector.py
│   │   └── network_collector.py
│   │
│   └── main.py                   # Punto de entrada
│
├── 📂 logs/                      # Archivos de log
│   └── agent.log
│
├── 📂 data/                      # Datos persistentes
│
├── 📂 docs/                      # Documentación
│   ├── MODOS_EJECUCION.md
│   ├── GUIA_SCHEDULER.md
│   └── CAMBIOS_Y_USO.md
│
├── 📄 README.md                  # Este archivo
├── 📄 LICENSE                    # Licencia
└── 📄 .gitignore                 # Archivos ignorados por Git
```

---

## 🐛 Troubleshooting

### El agente no inicia

**Problema**: Error al iniciar el agente

**Solución**:
```bash
# Verificar configuración
python src/main.py --debug

# Verificar logs
cat logs/agent.log

# Verificar permisos
chmod +x src/main.py
```

---

### No se recolectan datos

**Problema**: Los collectors no funcionan

**Solución**:
```bash
# Probar en modo test
python src/main.py --test

# Verificar collectors habilitados en config/agent.ini
[collectors]
hardware = true
software = true
...
```

---

### Error de conexión al servidor

**Problema**: Cannot connect to server

**Solución**:
```bash
# Usar modo mock para testing
[api]
use_mock = true

# Verificar URL del servidor
[api]
base_url = http://tu-servidor.com/api

# Verificar conectividad
curl http://tu-servidor.com/api/health
```

---

### Logs muy grandes

**Problema**: Los archivos de log ocupan mucho espacio

**Solución**:
```ini
# Configurar retención de logs
[logging]
days_to_keep = 7  # Mantener solo 7 días

# Habilitar limpieza automática
[scheduler]
enable_log_cleanup = true
cleanup_logs_hour = 2
```

---

## 🗺️ Roadmap

### v1.1.0 (Próximo Release)
- [ ] Soporte para base de datos local (SQLite)
- [ ] Dashboard web local
- [ ] Exportación a CSV/JSON
- [ ] Notificaciones por email

### v1.2.0
- [ ] Soporte para plugins personalizados
- [ ] Recolección de métricas de rendimiento
- [ ] Alertas configurables
- [ ] API REST local

### v2.0.0
- [ ] Interfaz gráfica (GUI)
- [ ] Instalador para Windows/macOS
- [ ] Paquetes .deb/.rpm para Linux
- [ ] Modo servidor (recibir datos de otros agentes)

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Si quieres contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución

- Sigue las convenciones de código de Python (PEP 8)
- Documenta nuevas funcionalidades
- Agrega tests para nuevo código
- Actualiza el README si es necesario

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 Autor

**Edgar Miranda**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- Email: tu-email@ejemplo.com

---

## 🙏 Agradecimientos

- Gracias a la comunidad de Python
- Inspirado en herramientas de monitoreo enterprise
- Desarrollado con ❤️ para la comunidad IT

---

## 📞 Soporte

¿Necesitas ayuda? Aquí hay algunas opciones:

- 📖 [Documentación completa](docs/)
- 🐛 [Reportar un bug](https://github.com/tu-usuario/it-monitoring-agent/issues)
- 💡 [Solicitar una feature](https://github.com/tu-usuario/it-monitoring-agent/issues)
- 💬 [Discusiones](https://github.com/tu-usuario/it-monitoring-agent/discussions)

---

<div align="center">

**[⬆ Volver arriba](#-it-monitoring-agent)**

Hecho con ❤️ por la comunidad

</div>