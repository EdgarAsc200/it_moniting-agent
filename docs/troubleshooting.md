# 🔧 Guía de Solución de Problemas

Soluciones a problemas comunes del IT Monitoring Agent.

## 📋 Índice

- [Problemas de Instalación](#problemas-de-instalación)
- [Problemas de Configuración](#problemas-de-configuración)
- [Problemas de Ejecución](#problemas-de-ejecución)
- [Problemas de Red/API](#problemas-de-redapi)
- [Problemas de Collectors](#problemas-de-collectors)
- [Problemas de Servicio](#problemas-de-servicio)
- [Logs y Diagnóstico](#logs-y-diagnóstico)

---

## 🚨 Problemas de Instalación

### Python no encontrado

**Síntoma:**
```
'python' is not recognized as an internal or external command
```

**Solución:**

**Windows:**
1. Descargar Python desde https://www.python.org/downloads/
2. Durante instalación, marcar "Add Python to PATH"
3. Verificar: `python --version`

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip
```

**macOS:**
```bash
# Usando Homebrew
brew install python@3.11
```

---

### Error de permisos durante instalación

**Síntoma:**
```
PermissionError: [Errno 13] Permission denied
```

**Solución:**

**Windows:**
- Ejecutar el instalador como Administrador
- Click derecho → "Ejecutar como administrador"

**Linux/macOS:**
```bash
sudo ./install.sh
```

---

### Dependencias no se instalan

**Síntoma:**
```
ERROR: Could not install packages due to an OSError
```

**Solución:**

1. **Actualizar pip:**
```bash
   # Windows
   python -m pip install --upgrade pip
   
   # Linux/macOS
   python3 -m pip install --upgrade pip
```

2. **Instalar con opción break-system-packages (Linux):**
```bash
   pip install -r requirements.txt --break-system-packages
```

3. **Verificar conexión a internet:**
```bash
   ping pypi.org
```

4. **Usar mirror alternativo:**
```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## ⚙️ Problemas de Configuración

### Archivo agent.ini no encontrado

**Síntoma:**
```
FileNotFoundError: config/agent.ini not found
```

**Solución:**

1. **Verificar ubicación del archivo:**
```bash
   # Windows
   dir "C:\Program Files\ITMonitoringAgent\config\agent.ini"
   
   # Linux
   ls -l /opt/it-monitoring-agent/config/agent.ini
   
   # macOS
   ls -l "/Library/Application Support/ITMonitoringAgent/config/agent.ini"
```

2. **Crear desde plantilla:**
```bash
   cp config/agent.ini.example config/agent.ini
```

3. **Verificar permisos:**
```bash
   # Linux/macOS
   sudo chmod 644 config/agent.ini
   
   # Windows (PowerShell)
   icacls config\agent.ini /grant Users:R
```

---

### Error al parsear configuración

**Síntoma:**
```
ConfigParser.ParsingError: Source contains parsing errors
```

**Solución:**

1. **Verificar sintaxis INI:**
   - Cada sección debe tener `[NombreSeccion]`
   - Sin espacios extra en nombres de claves
   - Sin comillas en valores (a menos que sean necesarias)

2. **Ejemplo correcto:**
```ini
   [Agent]
   agent_name = Mi-Agente
   interval = 3600
   
   [API]
   base_url = https://api.ejemplo.com
```

3. **Validar archivo:**
```bash
   python -c "import configparser; c = configparser.ConfigParser(); c.read('config/agent.ini'); print('OK')"
```

---

## 🔄 Problemas de Ejecución

### El agente no inicia

**Síntoma:**
```
El agente se cierra inmediatamente después de iniciar
```

**Solución:**

1. **Ejecutar en modo debug:**
```bash
   python src/main.py --debug
```

2. **Verificar logs:**
```bash
   # Ver últimas líneas del log
   tail -f logs/agent.log
```

3. **Probar en modo test:**
```bash
   python src/main.py --test
```

4. **Verificar dependencias:**
```bash
   pip list | grep -i psutil
   pip list | grep -i requests
```

---

### Error de importación de módulos

**Síntoma:**
```
ModuleNotFoundError: No module named 'psutil'
```

**Solución:**

1. **Reinstalar dependencias:**
```bash
   pip install -r requirements.txt --force-reinstall
```

2. **Verificar entorno virtual:**
```bash
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
```

3. **Instalar módulo específico:**
```bash
   pip install psutil
```

---

### El agente se ejecuta pero no recolecta datos

**Síntoma:**
```
INFO - Collection cycle starting...
INFO - Collection cycle completed
(Pero no hay datos)
```

**Solución:**

1. **Verificar collectors habilitados:**
```ini
   [Collectors]
   hardware = true
   software = true
   network = true
```

2. **Ejecutar collector individual:**
```python
   from collectors.hardware_collector import HardwareCollector
   
   collector = HardwareCollector()
   data = collector.collect()
   print(data)
```

3. **Verificar permisos:**
   - El agente necesita permisos para acceder a información del sistema
   - En Linux, algunos datos requieren root

---

## 🌐 Problemas de Red/API

### No puede conectar con el servidor API

**Síntoma:**
```
ConnectionError: Failed to establish connection to API server
```

**Solución:**

1. **Verificar URL del API:**
```bash
   curl https://api.ejemplo.com/health
```

2. **Verificar conectividad:**
```bash
   ping api.ejemplo.com
```

3. **Verificar firewall:**
```bash
   # Windows (PowerShell)
   Test-NetConnection -ComputerName api.ejemplo.com -Port 443
   
   # Linux
   telnet api.ejemplo.com 443
```

4. **Revisar configuración del proxy (si aplica):**
```bash
   # Establecer proxy
   export HTTP_PROXY=http://proxy.empresa.com:8080
   export HTTPS_PROXY=http://proxy.empresa.com:8080
```

5. **Deshabilitar verificación SSL temporalmente (solo para testing):**
```ini
   [API]
   verify_ssl = false
```

---

### Error de autenticación API

**Síntoma:**
```
401 Unauthorized: Invalid API key
```

**Solución:**

1. **Verificar API key en configuración:**
```ini
   [API]
   api_key = sk_live_abc123xyz789
```

2. **Re-registrar el agente:**
```bash
   # Eliminar agent_id actual
   nano config/agent.ini
   # Borrar la línea agent_id
   
   # Ejecutar de nuevo
   python src/main.py
```

3. **Verificar que el API key es válido en el servidor**

---

### Timeout al enviar datos

**Síntoma:**
```
TimeoutError: Request timed out after 30 seconds
```

**Solución:**

1. **Aumentar timeout:**
```ini
   [API]
   timeout = 60
```

2. **Verificar tamaño de datos:**
   - Deshabilitar collectors no necesarios
   - Reducir cantidad de software a reportar

3. **Verificar ancho de banda:**
```bash
   # Test de velocidad
   curl -o /dev/null https://api.ejemplo.com/test-file
```

---

## 🔍 Problemas de Collectors

### HardwareCollector falla

**Síntoma:**
```
ERROR - HardwareCollector failed: Access denied
```

**Solución:**

1. **Windows:** Ejecutar como Administrador
2. **Linux:** Ejecutar con sudo o como root
3. **Verificar permisos de WMI (Windows):**
```powershell
   Get-WmiObject Win32_ComputerSystem
```

---

### SoftwareCollector no detecta software

**Síntoma:**
```
INFO - Software installed: 0 packages
```

**Solución:**

**Windows:**
```powershell
# Verificar registro
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*
```

**Linux:**
```bash
# Verificar gestor de paquetes
dpkg -l  # Debian/Ubuntu
rpm -qa  # CentOS/RHEL
```

**macOS:**
```bash
# Verificar Homebrew
brew list
```

---

### NetworkCollector muestra interfaces vacías

**Síntoma:**
```
INFO - Network interfaces: []
```

**Solución:**

1. **Verificar psutil:**
```python
   import psutil
   print(psutil.net_if_addrs())
```

2. **Reinstalar psutil:**
```bash
   pip uninstall psutil
   pip install psutil
```

---

## 🔧 Problemas de Servicio

### Servicio no inicia (Windows)

**Síntoma:**
```
Error 1053: The service did not respond to the start or control request in a timely fashion
```

**Solución:**

1. **Verificar logs de Windows:**
   - Visor de eventos → Logs de Windows → Application

2. **Verificar wrapper de servicio:**
```powershell
   python "C:\Program Files\ITMonitoringAgent\service_wrapper.py" debug
```

3. **Reinstalar servicio:**
```powershell
   python service_wrapper.py remove
   python service_wrapper.py install
```

---

### Servicio no inicia (Linux - systemd)

**Síntoma:**
```
systemd[1]: it-monitoring-agent.service: Failed with result 'exit-code'
```

**Solución:**

1. **Ver logs de systemd:**
```bash
   sudo journalctl -u it-monitoring-agent -n 50 --no-pager
```

2. **Verificar permisos:**
```bash
   ls -l /opt/it-monitoring-agent/src/main.py
   sudo chown -R itmonitor:itmonitor /opt/it-monitoring-agent
```

3. **Probar manualmente:**
```bash
   sudo -u itmonitor /opt/it-monitoring-agent/venv/bin/python /opt/it-monitoring-agent/src/main.py --test
```

4. **Verificar archivo de servicio:**
```bash
   sudo systemctl cat it-monitoring-agent
```

---

### Daemon no inicia (macOS - launchd)

**Síntoma:**
```
launchctl error: Domain does not support specified action
```

**Solución:**

1. **Ver logs:**
```bash
   tail -f "/Library/Application Support/ITMonitoringAgent/logs/agent.log"
   tail -f "/Library/Application Support/ITMonitoringAgent/logs/stderr.log"
```

2. **Verificar plist:**
```bash
   plutil -lint /Library/LaunchDaemons/com.empresa.itmonitoringagent.plist
```

3. **Recargar daemon:**
```bash
   sudo launchctl unload /Library/LaunchDaemons/com.empresa.itmonitoringagent.plist
   sudo launchctl load /Library/LaunchDaemons/com.empresa.itmonitoringagent.plist
```

---

## 📊 Logs y Diagnóstico

### Ubicación de Logs

**Windows:**
```
C:\Program Files\ITMonitoringAgent\logs\agent.log
C:\Program Files\ITMonitoringAgent\logs\agent_error.log
```

**Linux:**
```
/opt/it-monitoring-agent/logs/agent.log
/opt/it-monitoring-agent/logs/agent_error.log
/var/log/syslog (mensajes de systemd)
```

**macOS:**
```
/Library/Application Support/ITMonitoringAgent/logs/agent.log
/Library/Application Support/ITMonitoringAgent/logs/stderr.log
/var/log/system.log (mensajes de launchd)
```

---

### Habilitar Debug Logging
```ini
[Logging]
level = DEBUG

[Agent]
debug = true
```

**Reiniciar el servicio después de cambiar configuración**

---

### Comandos de Diagnóstico

**Información del Sistema:**
```bash
python src/main.py --test
python src/main.py --debug
```

**Ver configuración actual:**
```bash
cat config/agent.ini
```

**Verificar conectividad API:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.ejemplo.com/health
```

**Verificar procesos:**
```bash
# Windows
tasklist | findstr python

# Linux/macOS
ps aux | grep python
```

---

## 🆘 Recolección de Información para Soporte

Si necesitas reportar un problema, incluye:

1. **Versión del agente:**
```bash
   python src/main.py --version
```

2. **Sistema operativo:**
```bash
   # Windows
   systeminfo | findstr OS
   
   # Linux
   cat /etc/os-release
   
   # macOS
   sw_vers
```

3. **Versión de Python:**
```bash
   python --version
```

4. **Logs recientes:**
```bash
   # Últimas 50 líneas
   tail -n 50 logs/agent.log
```

5. **Configuración (sin API keys):**
```bash
   cat config/agent.ini | grep -v api_key
```

---

## 🔄 Resetear el Agente

Si todo falla, resetear completamente:

1. **Detener el servicio**
2. **Eliminar cache y datos temporales:**
```bash
   rm -rf data/cache/*
   rm -rf logs/*
```
3. **Borrar agent_id para re-registro:**
```ini
   [Agent]
   agent_id = 
```
4. **Reiniciar el servicio**

---

## ✅ Checklist de Verificación

- [ ] Python 3.9+ instalado
- [ ] Todas las dependencias instaladas
- [ ] Archivo agent.ini existe y es válido
- [ ] API URL configurada correctamente
- [ ] API key válida (si ya está registrado)
- [ ] Collectors habilitados en configuración
- [ ] Permisos correctos en archivos
- [ ] Red/firewall permite conexión al API
- [ ] Logs no muestran errores críticos
- [ ] Modo test funciona correctamente

---

## 📞 Contactar Soporte

Si el problema persiste:

- **GitHub Issues:** https://github.com/tu-usuario/it-monitoring-agent/issues
- **Email:** soporte@tu-empresa.com
- **Documentación:** Ver otros archivos en `/docs`

**Al reportar incluye:**
- Descripción del problema
- Pasos para reproducir
- Logs relevantes
- Información del sistema
- Configuración (sin API keys)
