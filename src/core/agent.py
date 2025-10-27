"""
Clase principal del Agente de Monitoreo
"""

import time
import logging
from datetime import datetime


class Agent:
    """
    Agente principal que coordina la recopilación y envío de datos
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config):
        """
        Inicializa el agente
        
        Args:
            config: Instancia de Config con la configuración
        """
        self.config = config
        self.logger = logging.getLogger('ITAgent')
        self.asset_id = config.getint('agent', 'id', fallback=0)
        self.report_interval = config.getint('agent', 'report_interval', fallback=300)
        
        # Inicializar collectors (los crearemos después)
        self.collectors = {}
        self._init_collectors()
        
        self.logger.info(f"Agente inicializado (ID: {self.asset_id})")
    
    def _init_collectors(self):
        """
        Inicializa los collectors de datos
        """
        self.logger.debug("Inicializando collectors...")
        
        # Importar y crear collectors
        try:
            from src.collectors.hardware_collector import HardwareCollector
            self.collectors['hardware'] = HardwareCollector()
            self.logger.debug("✓ HardwareCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar HardwareCollector: {e}")
        
        try:
            from src.collectors.domain_collector import DomainCollector
            self.collectors['domain'] = DomainCollector()
            self.logger.debug("✓ DomainCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar DomainCollector: {e}")

        try:
            from src.collectors.software_collector import SoftwareCollector
            self.collectors['software'] = SoftwareCollector()
            self.logger.debug("✓ SoftwareCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar SoftwareCollector: {e}")

        try:
            from src.collectors.antivirus_collector import AntivirusCollector
            self.collectors['antivirus'] = AntivirusCollector()
            self.logger.debug("✓ AntivirusCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar AntivirusCollector: {e}")

        try:
            from src.collectors.office_collector import OfficeCollector
            self.collectors['office'] = OfficeCollector()
            self.logger.debug("✓ OfficeCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar OfficeCollector: {e}")
        
        try:
            from src.collectors.network_collector import NetworkCollector
            self.collectors['network'] = NetworkCollector()
            self.logger.debug("✓ NetworkCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar NetworkCollector: {e}")

        try:
            from src.collectors.network_collector import NetworkCollector
            self.collectors['network'] = NetworkCollector()
            self.logger.debug("✓ NetworkCollector inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar NetworkCollector: {e}")
        
        self.logger.debug("Collectors inicializados")
    
    def register(self):
        """
        Registra el agente en el servidor
        
        Returns:
            bool: True si el registro fue exitoso
        """
        self.logger.info("Registrando agente en el servidor...")
        
        try:
            # TODO: Implementar registro real cuando tengamos API client
            # Por ahora solo simulamos
            self.logger.info("⚠️  Registro simulado - Implementar API client")
            
            # Simular que obtuvimos un ID
            if self.asset_id == 0:
                self.asset_id = 999  # ID simulado
                self.config.set('agent', 'id', str(self.asset_id))
                self.config.save()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al registrar agente: {e}")
            return False
    
    def collect_all_data(self):
        """
        Recopila todos los datos de los collectors
        
        Returns:
            dict: Datos recopilados de todos los collectors
        """
        self.logger.info("Recopilando datos de todos los collectors...")
        
        data = {
            'asset_id': self.asset_id,
            'version_agent': self.VERSION,
            'report_date': datetime.now().isoformat(),
        }
        
        # Recopilar datos reales de los collectors
        data['hardware'] = self._collect_hardware()
        data['domain'] = self._collect_domain()
        data['software'] = self._collect_software()
        data['antivirus'] = self._collect_antivirus()
        data['office'] = self._collect_office()
        data['network'] = self._collect_network()
        data['network'] = self._collect_network()
        
        self.logger.info("✓ Datos recopilados exitosamente")
        return data
    
    def _collect_hardware(self):
        """Recopila información de hardware"""
        self.logger.debug("Recopilando hardware...")
        
        if 'hardware' in self.collectors:
            return self.collectors['hardware'].safe_collect()
        
        # Fallback si no hay collector
        return {
            'operating_system': 'Collector no disponible',
            'processor': 'Collector no disponible',
            'total_ram_gb': 0
        }
    
    def _collect_domain(self):
        """Recopila información de dominio"""
        self.logger.debug("Recopilando dominio...")
        
        if 'domain' in self.collectors:
            return self.collectors['domain'].safe_collect()
        
        # Fallback si no hay collector
        return {
            'is_domain_joined': False,
            'domain_name': None
        }
    
    def _collect_software(self):
        """Recopila software instalado"""
        self.logger.debug("Recopilando software...")

        if 'software' in self.collectors:
            return self.collectors['software'].safe_collect()

        # Fallback si no hay collector
        return {
            'installed_software': [],
            'total_installed': 0
        }
    
    def _collect_antivirus(self):
        """Recopila información de antivirus"""
        self.logger.debug("Recopilando antivirus...")
        
        if 'antivirus' in self.collectors:
            try:
                data = self.collectors['antivirus'].collect()
                
                # Adaptar al formato esperado por la base de datos
                return {
                    'antivirus_installed': bool(data.get('antivirus_name')),
                    'antivirus_name': data.get('antivirus_name'),
                    'antivirus_version': data.get('antivirus_version'),
                    'protection_status': data.get('protection_status'),
                    'last_update': data.get('last_update'),
                    'last_scan': data.get('last_scan'),
                    'firewall_status': data.get('firewall_status'),
                    'real_time_protection': data.get('real_time_protection', False),
                    'definitions_up_to_date': data.get('definitions_up_to_date', False),
                    'third_party_antivirus': data.get('third_party_antivirus', []),
                    # Datos específicos de macOS
                    'gatekeeper_status': data.get('gatekeeper_status'),
                    'system_integrity_protection': data.get('system_integrity_protection'),
                    # Datos específicos de Linux
                    'selinux_status': data.get('selinux_status'),
                    'apparmor_status': data.get('apparmor_status')
                }
            except Exception as e:
                self.logger.error(f"Error al recopilar antivirus: {e}")
                return {
                    'antivirus_installed': False,
                    'antivirus_name': None,
                    'error': str(e)
                }
        
        # Fallback si no hay collector
        return {
            'antivirus_installed': False,
            'antivirus_name': None
        }
    
    def _collect_office(self):
        """Recopila información de Office"""
        self.logger.debug("Recopilando Office...")
        
        if 'office' in self.collectors:
            try:
                data = self.collectors['office'].collect()
                
                # Adaptar al formato esperado por la base de datos
                return {
                    'office_installed': data.get('office_installed', False),
                    'office_version': data.get('office_version'),
                    'office_edition': data.get('office_edition'),
                    'office_build': data.get('office_build'),
                    'office_architecture': data.get('office_architecture'),
                    'license_type': data.get('license_type'),
                    'license_status': data.get('license_status'),
                    'product_key_last5': data.get('product_key_last5'),
                    'installed_apps': data.get('installed_apps', []),
                    'installation_path': data.get('installation_path'),
                    'update_channel': data.get('update_channel'),
                    # Para Linux
                    'office_type': data.get('office_type')
                }
            except Exception as e:
                self.logger.error(f"Error al recopilar Office: {e}")
                return {
                    'office_installed': False,
                    'office_version': None,
                    'error': str(e)
                }
        
        # Fallback si no hay collector
        return {
            'office_installed': False,
            'office_version': None
        }
    
    def _collect_network(self):
        """Recopila información de red"""
        self.logger.debug("Recopilando red...")
        
        if 'network' in self.collectors:
            try:
                data = self.collectors['network'].collect()
                
                # Los datos ya vienen en el formato correcto
                return data
            except Exception as e:
                self.logger.error(f"Error al recopilar red: {e}")
                return {
                    'hostname': 'Unknown',
                    'interfaces': [],
                    'default_gateway': None,
                    'dns_servers': [],
                    'error': str(e)
                }
        
        # Fallback si no hay collector
        return {
            'hostname': 'Unknown',
            'interfaces': [],
            'default_gateway': None,
            'dns_servers': []
        }
    
    def _collect_network(self):
        """Recopila información de red"""
        self.logger.debug("Recopilando red...")
        
        if 'network' in self.collectors:
            try:
                data = self.collectors['network'].collect()
                
                # Adaptar al formato esperado por la base de datos
                return {
                    'hostname': data.get('hostname', 'Unknown'),
                    'interfaces': data.get('interfaces', []),
                    'default_gateway': data.get('default_gateway'),
                    'dns_servers': data.get('dns_servers', []),
                    'mac_addresses': data.get('mac_addresses', []),
                    'active_connections': data.get('active_connections', 0)
                }
            except Exception as e:
                self.logger.error(f"Error al recopilar red: {e}")
                return {
                    'hostname': 'Unknown',
                    'interfaces': [],
                    'error': str(e)
                }
        
        # Fallback si no hay collector
        return {
            'hostname': 'Unknown',
            'interfaces': []
        }
    
    def send_data(self, data):
        """
        Envía los datos al servidor
        
        Args:
            data: Datos a enviar
            
        Returns:
            bool: True si el envío fue exitoso
        """
        self.logger.info("Enviando datos al servidor...")
        
        try:
            # TODO: Implementar envío real cuando tengamos API client
            self.logger.info("⚠️  Envío simulado - Implementar API client")
            self.logger.debug(f"Datos a enviar: {data}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al enviar datos: {e}")
            return False
    
    def run_once(self):
        """
        Ejecuta el agente una sola vez
        """
        self.logger.info("Ejecutando ciclo único...")
        
        try:
            # Verificar si el agente está registrado
            if self.asset_id == 0:
                self.logger.warning("Agente no registrado. Ejecuta con --register primero")
                return False
            
            # Recopilar datos
            data = self.collect_all_data()
            
            # Enviar datos
            success = self.send_data(data)
            
            if success:
                self.logger.info("✓ Ciclo completado exitosamente")
            else:
                self.logger.error("✗ Error al completar el ciclo")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error en ciclo único: {e}", exc_info=True)
            return False
    
    def run(self):
        """
        Ejecuta el agente en modo continuo
        """
        self.logger.info(f"Iniciando modo continuo (intervalo: {self.report_interval}s)")
        
        # Verificar si el agente está registrado
        if self.asset_id == 0:
            self.logger.error("Agente no registrado. Ejecuta con --register primero")
            return
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"─── Ciclo #{cycle_count} ───")
                
                start_time = time.time()
                
                # Ejecutar ciclo
                self.run_once()
                
                # Calcular tiempo de espera
                elapsed_time = time.time() - start_time
                wait_time = max(0, self.report_interval - elapsed_time)
                
                if wait_time > 0:
                    self.logger.info(f"⏳ Próximo reporte en {wait_time:.0f} segundos...")
                    time.sleep(wait_time)
                else:
                    self.logger.warning(
                        f"⚠️  El ciclo tardó {elapsed_time:.0f}s "
                        f"(más que el intervalo de {self.report_interval}s)"
                    )
                
            except KeyboardInterrupt:
                self.logger.info("Deteniendo por solicitud del usuario...")
                break
            except Exception as e:
                self.logger.error(f"Error en el ciclo: {e}", exc_info=True)
                self.logger.info("Reintentando en 60 segundos...")
                time.sleep(60)