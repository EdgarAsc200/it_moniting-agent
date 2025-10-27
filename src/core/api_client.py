# src/core/api_client.py

"""
Cliente HTTP para comunicación con la API del servidor
Maneja el envío de datos del agente al servidor central
"""

import json
import logging
import urllib.request
import urllib.error
import urllib.parse
import ssl
from typing import Dict, Optional, Tuple, Any
from datetime import datetime


class APIClient:
    """
    Cliente HTTP para comunicarse con la API del servidor.
    Maneja autenticación, envío de datos y manejo de errores.
    """
    
    def __init__(self, config):
        """
        Inicializa el cliente API
        
        Args:
            config: Instancia de Config con la configuración del agente
        """
        self.config = config
        self.logger = logging.getLogger('ITAgent.APIClient')
        
        # Configuración de API
        self.base_url = config.get('api', 'base_url', '').rstrip('/')
        self.timeout = config.getint('api', 'timeout', 30)
        self.verify_ssl = config.getboolean('api', 'verify_ssl', True)
        self.api_key = config.get('api', 'api_key', '')
        
        # ID del agente
        self.agent_id = config.getint('agent', 'id', 0)
        
        # Configurar contexto SSL
        self.ssl_context = self._setup_ssl_context()
        
        self.logger.info(f"APIClient inicializado (base_url: {self.base_url})")
    
    def _setup_ssl_context(self) -> ssl.SSLContext:
        """
        Configura el contexto SSL para las peticiones
        
        Returns:
            ssl.SSLContext: Contexto SSL configurado
        """
        if self.verify_ssl:
            # Usar certificados del sistema
            context = ssl.create_default_context()
        else:
            # No verificar certificados (solo desarrollo/testing)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.logger.warning("⚠️  Verificación SSL deshabilitada")
        
        return context
    
    def _build_headers(self, content_type: str = 'application/json') -> Dict[str, str]:
        """
        Construye los headers HTTP para las peticiones
        
        Args:
            content_type: Tipo de contenido
            
        Returns:
            dict: Headers HTTP
        """
        headers = {
            'Content-Type': content_type,
            'User-Agent': f'IT-Agent/{self.config.get("agent", "version", "1.0.0")}',
            'Accept': 'application/json'
        }
        
        # Agregar API key si está configurada
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            # O usar header personalizado si tu API lo requiere
            # headers['X-API-Key'] = self.api_key
        
        return headers
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Realiza una petición HTTP a la API
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API (ej: '/agents/register')
            data: Datos a enviar en el body (para POST/PUT)
            params: Parámetros de query string (para GET)
            
        Returns:
            tuple: (success, response_data, error_message)
        """
        try:
            # Construir URL completa
            url = f"{self.base_url}{endpoint}"
            
            # Agregar parámetros de query si existen
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}"
            
            self.logger.debug(f"{method} {url}")
            
            # Preparar datos
            request_body = None
            if data:
                request_body = json.dumps(data).encode('utf-8')
            
            # Crear request
            headers = self._build_headers()
            request = urllib.request.Request(
                url,
                data=request_body,
                headers=headers,
                method=method
            )
            
            # Realizar petición
            with urllib.request.urlopen(
                request, 
                timeout=self.timeout,
                context=self.ssl_context
            ) as response:
                # Leer respuesta
                response_data = response.read().decode('utf-8')
                
                # Parsear JSON si hay contenido
                if response_data:
                    try:
                        response_json = json.loads(response_data)
                    except json.JSONDecodeError:
                        response_json = {'raw_response': response_data}
                else:
                    response_json = {}
                
                self.logger.debug(f"Respuesta {response.status}: {response_json}")
                
                return True, response_json, None
        
        except urllib.error.HTTPError as e:
            # Error HTTP (4xx, 5xx)
            error_msg = f"HTTP {e.code}: {e.reason}"
            
            try:
                error_body = e.read().decode('utf-8')
                error_data = json.loads(error_body)
                error_msg = f"{error_msg} - {error_data.get('message', error_body)}"
            except:
                pass
            
            self.logger.error(f"Error HTTP: {error_msg}")
            return False, None, error_msg
        
        except urllib.error.URLError as e:
            # Error de conexión
            error_msg = f"Error de conexión: {e.reason}"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        except TimeoutError:
            error_msg = f"Timeout después de {self.timeout}s"
            self.logger.error(error_msg)
            return False, None, error_msg
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, None, error_msg
    
    def register_agent(self) -> Tuple[bool, Optional[int]]:
        """
        Registra el agente en el servidor
        
        Returns:
            tuple: (success, agent_id)
        """
        self.logger.info("Registrando agente en el servidor...")
        
        # Datos de registro
        registration_data = {
            'name': self.config.get('agent', 'name', 'IT-Agent'),
            'version': self.config.get('agent', 'version', '1.0.0'),
            'os_type': self._get_os_info(),
            'registration_date': datetime.now().isoformat()
        }
        
        # Hacer petición
        success, response, error = self._make_request(
            'POST',
            '/agents/register',
            data=registration_data
        )
        
        if success and response:
            agent_id = response.get('agent_id') or response.get('id')
            if agent_id:
                self.logger.info(f"✓ Agente registrado exitosamente (ID: {agent_id})")
                return True, agent_id
            else:
                self.logger.error("Respuesta del servidor no contiene agent_id")
                return False, None
        else:
            self.logger.error(f"Error al registrar agente: {error}")
            return False, None
    
    def send_inventory_data(self, inventory_data: Dict) -> bool:
        """
        Envía los datos de inventario al servidor
        
        Args:
            inventory_data: Diccionario con todos los datos recopilados
            
        Returns:
            bool: True si el envío fue exitoso
        """
        self.logger.info("Enviando datos de inventario al servidor...")
        
        # Verificar que el agente esté registrado
        if self.agent_id == 0:
            self.logger.error("Agente no registrado. No se pueden enviar datos.")
            return False
        
        # Agregar metadata
        payload = {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'data': inventory_data
        }
        
        # Hacer petición
        success, response, error = self._make_request(
            'POST',
            f'/agents/{self.agent_id}/inventory',
            data=payload
        )
        
        if success:
            self.logger.info("✓ Datos de inventario enviados exitosamente")
            return True
        else:
            self.logger.error(f"Error al enviar datos: {error}")
            return False
    
    def send_heartbeat(self) -> bool:
        """
        Envía un heartbeat al servidor para indicar que el agente está activo
        
        Returns:
            bool: True si el heartbeat fue exitoso
        """
        self.logger.debug("Enviando heartbeat...")
        
        if self.agent_id == 0:
            self.logger.warning("Agente no registrado. Saltando heartbeat.")
            return False
        
        heartbeat_data = {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        success, response, error = self._make_request(
            'POST',
            f'/agents/{self.agent_id}/heartbeat',
            data=heartbeat_data
        )
        
        if success:
            self.logger.debug("✓ Heartbeat enviado")
            return True
        else:
            self.logger.debug(f"Error en heartbeat: {error}")
            return False
    
    def get_configuration(self) -> Optional[Dict]:
        """
        Obtiene la configuración del agente desde el servidor
        
        Returns:
            dict: Configuración del servidor, o None si falla
        """
        self.logger.info("Obteniendo configuración del servidor...")
        
        if self.agent_id == 0:
            self.logger.error("Agente no registrado")
            return None
        
        success, response, error = self._make_request(
            'GET',
            f'/agents/{self.agent_id}/config'
        )
        
        if success and response:
            self.logger.info("✓ Configuración obtenida del servidor")
            return response.get('config', response)
        else:
            self.logger.error(f"Error al obtener configuración: {error}")
            return None
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        Verifica si hay actualizaciones disponibles para el agente
        
        Returns:
            dict: Información de actualización, o None si no hay actualizaciones
        """
        self.logger.debug("Verificando actualizaciones...")
        
        current_version = self.config.get('agent', 'version', '1.0.0')
        
        success, response, error = self._make_request(
            'GET',
            '/agents/updates',
            params={'current_version': current_version}
        )
        
        if success and response:
            if response.get('update_available'):
                self.logger.info(
                    f"✓ Actualización disponible: {response.get('latest_version')}"
                )
                return response
            else:
                self.logger.debug("No hay actualizaciones disponibles")
                return None
        else:
            self.logger.debug(f"Error al verificar actualizaciones: {error}")
            return None
    
    def send_logs(self, log_entries: list) -> bool:
        """
        Envía logs al servidor para monitoreo centralizado
        
        Args:
            log_entries: Lista de entradas de log
            
        Returns:
            bool: True si el envío fue exitoso
        """
        if not log_entries:
            return True
        
        self.logger.debug(f"Enviando {len(log_entries)} entradas de log...")
        
        payload = {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'logs': log_entries
        }
        
        success, response, error = self._make_request(
            'POST',
            f'/agents/{self.agent_id}/logs',
            data=payload
        )
        
        if success:
            self.logger.debug("✓ Logs enviados")
            return True
        else:
            self.logger.debug(f"Error al enviar logs: {error}")
            return False
    
    def report_error(self, error_data: Dict) -> bool:
        """
        Reporta un error al servidor
        
        Args:
            error_data: Información del error
            
        Returns:
            bool: True si el reporte fue exitoso
        """
        self.logger.info("Reportando error al servidor...")
        
        payload = {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'error': error_data
        }
        
        success, response, error = self._make_request(
            'POST',
            f'/agents/{self.agent_id}/errors',
            data=payload
        )
        
        if success:
            self.logger.info("✓ Error reportado")
            return True
        else:
            self.logger.warning(f"No se pudo reportar error: {error}")
            return False
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con el servidor
        
        Returns:
            bool: True si la conexión es exitosa
        """
        self.logger.info("Probando conexión con el servidor...")
        
        success, response, error = self._make_request(
            'GET',
            '/health'
        )
        
        if success:
            self.logger.info("✓ Conexión exitosa con el servidor")
            return True
        else:
            self.logger.error(f"✗ Error de conexión: {error}")
            return False
    
    def _get_os_info(self) -> Dict:
        """
        Obtiene información básica del sistema operativo
        
        Returns:
            dict: Información del OS
        """
        import platform
        
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    
    def get_server_time(self) -> Optional[str]:
        """
        Obtiene la hora del servidor (útil para sincronización)
        
        Returns:
            str: Timestamp del servidor en formato ISO, o None si falla
        """
        success, response, error = self._make_request(
            'GET',
            '/time'
        )
        
        if success and response:
            return response.get('timestamp')
        
        return None
    
    def unregister_agent(self) -> bool:
        """
        Desregistra el agente del servidor
        
        Returns:
            bool: True si el desregistro fue exitoso
        """
        self.logger.info("Desregistrando agente del servidor...")
        
        if self.agent_id == 0:
            self.logger.warning("Agente no registrado")
            return True
        
        success, response, error = self._make_request(
            'DELETE',
            f'/agents/{self.agent_id}'
        )
        
        if success:
            self.logger.info("✓ Agente desregistrado exitosamente")
            return True
        else:
            self.logger.error(f"Error al desregistrar agente: {error}")
            return False
    
    def __str__(self) -> str:
        return f"APIClient(base_url={self.base_url}, agent_id={self.agent_id})"
    
    def __repr__(self) -> str:
        return self.__str__()


class MockAPIClient(APIClient):
    """
    Cliente API simulado para pruebas y desarrollo sin servidor real.
    Simula respuestas exitosas sin hacer peticiones HTTP reales.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.logger.info("⚠️  Usando MockAPIClient (modo simulación)")
        self.simulated_agent_id = 999
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Simula una petición HTTP exitosa"""
        self.logger.debug(f"[MOCK] {method} {endpoint}")
        
        # Simular respuestas según el endpoint
        if 'register' in endpoint:
            return True, {'agent_id': self.simulated_agent_id, 'status': 'registered'}, None
        elif 'inventory' in endpoint:
            return True, {'status': 'received', 'message': 'Data stored successfully'}, None
        elif 'heartbeat' in endpoint:
            return True, {'status': 'alive'}, None
        elif 'health' in endpoint:
            return True, {'status': 'healthy', 'version': '1.0.0'}, None
        elif 'config' in endpoint:
            return True, {'config': {'report_interval': 300}}, None
        elif 'updates' in endpoint:
            return True, {'update_available': False}, None
        else:
            return True, {'status': 'ok'}, None
    
    def test_connection(self) -> bool:
        """Simula una conexión exitosa"""
        self.logger.info("[MOCK] ✓ Conexión simulada exitosa")
        return True