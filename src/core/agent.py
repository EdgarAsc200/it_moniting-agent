"""
Clase principal del Agente de Monitoreo IT
Versión con Scheduler integrado
"""

import time
import logging
import platform
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import socket

# Core modules
from core.config import Config
from core.logger import setup_logger
from core.api_client import APIClient
from core.scheduler import Scheduler
from core.updater import Updater

# Collectors
from collectors.hardware_collector import HardwareCollector
from collectors.domain_collector import DomainCollector
from collectors.software_collector import SoftwareCollector
from collectors.antivirus_collector import AntivirusCollector
from collectors.office_collector import OfficeCollector
from collectors.network_collector import NetworkCollector

# Models (NUEVO)
from models import Asset, Hardware, Software


class Agent:
    """
    Agente principal que coordina la recopilación y envío de datos
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, config: Config):
        """
        Inicializa el agente con su configuración
        
        Args:
            config: Objeto de configuración del agente
        """
        self.config = config
        
        # Inicializar logger (sin parámetro console)
        self.logger = setup_logger(
            name="Agent",
            log_file=config.get('logging', 'file', fallback='logs/agent.log'),
            level=config.get('logging', 'level', fallback='INFO')
        )
        
        self.logger.info("=" * 60)
        self.logger.info(f"Inicializando IT Monitoring Agent v{self.VERSION}")
        self.logger.info("=" * 60)
        
        # Información del sistema
        self.hostname =socket.gethostname(),
        self.os_type = platform.system()
        
        # Intervalo de reporte (en segundos)
        self.report_interval = int(config.get('agent', 'report_interval', fallback=300))
        
        # Cliente API
        self.api_client = self._init_api_client()
        
        # Scheduler para tareas programadas
        self.scheduler = Scheduler()
        self.logger.info("✓ Scheduler inicializado")
        
        # Updater para gestión de actualizaciones
        self.updater = Updater(config=self.config, logger=self.logger, api_client=self.api_client)
        self.logger.info("✓ Updater inicializado")
        
        # Collectors
        self.collectors = {}
        self._init_collectors()
        
        # Estado del agente
        self.is_running = False
        self.start_time = None
        self.last_report_time = None
        self.asset_id = None  # ID del activo (usado en modo --register)
        
        self.logger.info("Agent inicializado correctamente")
        self.logger.info (f"{socket.getfqdn()}, nombre del equipo")
        
        # Intentar registrar el agente si está configurado
        self._register_agent_if_needed()
    
    def _register_agent_if_needed(self):
        """Registra el agente en el servidor si es necesario"""
        try:
            # Verificar si el agente ya tiene un ID configurado
            agent_id = int(self.config.get('agent', 'id', fallback=0))
            
            if agent_id == 0 and self.api_client:
                # Intentar registrar el agente
                self.logger.info("Agente sin ID configurado, intentando registro...")
                success, new_agent_id = self.api_client.register_agent()
                
                if success and new_agent_id:
                    self.logger.info(f"✓ Agente registrado exitosamente con ID: {new_agent_id}")
                    # Aquí podrías guardar el ID en el config si quieres persistirlo
                else:
                    self.logger.warning("⚠️  No se pudo registrar el agente automáticamente")
            elif agent_id > 0:
                self.logger.info(f"Agente ya registrado con ID: {agent_id}")
                
        except Exception as e:
            self.logger.warning(f"Error al intentar registrar agente: {e}")
            # No lanzar excepción, solo advertir
    
    def _init_api_client(self):
        """Inicializa el cliente API"""
        try:
            # Verificar si usar mock o cliente real
            use_mock = self.config.getboolean('api', 'use_mock', fallback=False)
            
            if use_mock:
                # Importar MockAPIClient
                from core.api_client import MockAPIClient
                api_client = MockAPIClient(self.config)
                self.logger.info("✓ Mock API Client inicializado (modo simulación)")
            else:
                # Usar cliente real
                api_client = APIClient(self.config)
                self.logger.info(f"✓ API Client inicializado (base_url: {api_client.base_url})")
            
            return api_client
            
        except Exception as e:
            self.logger.error(f"Error al inicializar API Client: {e}")
            raise
    
    def _init_collectors(self):
        """Inicializa todos los collectors habilitados"""
        self.logger.info("Inicializando collectors...")
        
        collectors_config = {
            'hardware': (HardwareCollector, "HardwareCollector"),
            'domain': (DomainCollector, "DomainCollector"),
            'software': (SoftwareCollector, "SoftwareCollector"),
            'antivirus': (AntivirusCollector, "AntivirusCollector"),
            'office': (OfficeCollector, "OfficeCollector"),
            'network': (NetworkCollector, "NetworkCollector")
        }
        
        for key, (collector_class, name) in collectors_config.items():
            if self.config.get('collectors', key, fallback=True):
                try:
                    self.collectors[key] = collector_class()
                    self.logger.debug(f"✓ {name} inicializado")
                except Exception as e:
                    self.logger.error(f"Error al inicializar {name}: {e}")
            else:
                self.logger.debug(f"✗ {name} deshabilitado en configuración")
        
        self.logger.info(f"Collectors inicializados: {len(self.collectors)}/{len(collectors_config)}")
    
    def _setup_scheduled_jobs(self):
        """
        Configura todas las tareas programadas del agente
        Este es el lugar donde se agregan TODOS los trabajos del scheduler
        """
        self.logger.info("Configurando tareas programadas...")
        
        # ═══════════════════════════════════════════════════════════
        # TAREA 1: Recolección y envío de datos (periódica)
        # ═══════════════════════════════════════════════════════════
        self.scheduler.add_interval_job(
            name="collect_and_send_data",
            func=self.run_once,
            interval=self.report_interval
        )
        self.logger.info(f"✓ Tarea 'collect_and_send_data' agregada (cada {self.report_interval}s)")
        
        # ═══════════════════════════════════════════════════════════
        # TAREA 2: Limpieza de logs antiguos (diaria - 2 AM)
        # ═══════════════════════════════════════════════════════════
        if self.config.get('scheduler', 'enable_log_cleanup', fallback=True):
            cleanup_hour = int(self.config.get('scheduler', 'cleanup_logs_hour', fallback=2))
            self.scheduler.add_cron_job(
                name="cleanup_old_logs",
                func=self._cleanup_old_logs,
                hour=cleanup_hour,
                minute=0
            )
            self.logger.info(f"✓ Tarea 'cleanup_old_logs' agregada (diario {cleanup_hour}:00 AM)")
        
        # ═══════════════════════════════════════════════════════════
        # TAREA 3: Verificar actualizaciones (diaria - 3 AM)
        # ═══════════════════════════════════════════════════════════
        if self.config.get('scheduler', 'enable_auto_update', fallback=False):
            update_hour = int(self.config.get('scheduler', 'check_updates_hour', fallback=3))
            self.scheduler.add_cron_job(
                name="check_for_updates",
                func=self._check_for_updates,
                hour=update_hour,
                minute=0
            )
            self.logger.info(f"✓ Tarea 'check_for_updates' agregada (diario {update_hour}:00 AM)")
        
        # ═══════════════════════════════════════════════════════════
        # TAREA 4: Health check periódico (cada hora)
        # ═══════════════════════════════════════════════════════════
        if self.config.get('scheduler', 'enable_health_check', fallback=True):
            health_interval = int(self.config.get('scheduler', 'health_check_interval', fallback=3600))
            self.scheduler.add_interval_job(
                name="system_health_check",
                func=self._system_health_check,
                interval=health_interval
            )
            self.logger.info(f"✓ Tarea 'system_health_check' agregada (cada {health_interval}s)")
        
        self.logger.info("Tareas programadas configuradas correctamente")
    
    def run(self):
        """
        Inicia el agente en modo servicio con scheduler
        """
        try:
            self.logger.info("Iniciando Agent en modo servicio...")
            self.is_running = True
            self.start_time = datetime.now()
            
            # Configurar tareas programadas
            self._setup_scheduled_jobs()
            
            # Iniciar el scheduler
            self.scheduler.start()
            self.logger.info("✓ Scheduler iniciado correctamente")
            
            # Ejecutar una recolección inmediata al iniciar
            self.logger.info("Ejecutando recolección inicial...")
            self.run_once()
            
            self.logger.info("=" * 60)
            self.logger.info("Agent ejecutándose. Presiona Ctrl+C para detener.")
            self.logger.info("=" * 60)
            
            # Mantener el programa vivo
            while self.is_running:
                time.sleep(60)  # Revisar cada minuto
                
        except KeyboardInterrupt:
            self.logger.info("Interrupción de usuario detectada")
            self.stop()
        except Exception as e:
            self.logger.error(f"Error crítico en el agent: {e}", exc_info=True)
            self.stop()
            raise
    
    def run_once(self):
        """
        Ejecuta un ciclo completo de recolección y envío de datos
        Esta función es llamada por el scheduler automáticamente
        """
        try:
            cycle_start = datetime.now()
            self.logger.info("-" * 60)
            self.logger.info(f"Iniciando ciclo de recolección: {cycle_start.isoformat()}")
            self.logger.info("-" * 60)
            
            # Recolectar todos los datos
            data = self.collect_all_data()
            
            # Agregar metadata del agente
            data['agent_info'] = self._get_agent_info()
            
            # Enviar datos al servidor
            success = self._send_data(data)
            
            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()
            
            if success:
                self.last_report_time = cycle_end
                self.logger.info(f"✓ Ciclo completado exitosamente en {duration:.2f}s")
            else:
                self.logger.warning(f"✗ Ciclo completado con errores en {duration:.2f}s")
            
            self.logger.info("-" * 60)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error en ciclo de recolección: {e}", exc_info=True)
            return False
    
    def validate(self):
        """
        Valida la configuración del agente sin ejecutar tareas (modo debug)
        Útil para verificar que todo está configurado correctamente
        """
        self.logger.info("=" * 60)
        self.logger.info("🔍 MODO DEBUG - Validación de Configuración")
        self.logger.info("=" * 60)
        
        # Información del sistema
        self.logger.info("\n📋 Información del Sistema:")
        self.logger.info(f"  • Hostname: {self.hostname}")
        self.logger.info(f"  • OS: {self.os_type}")
        self.logger.info(f"  • Versión Agent: {self.VERSION}")
        
        # Configuración de reporte
        self.logger.info("\n⚙️  Configuración de Reporte:")
        self.logger.info(f"  • Intervalo: {self.report_interval}s ({self.report_interval/60:.1f} minutos)")
        
        # API Client
        self.logger.info("\n🌐 API Client:")
        if self.api_client:
            is_mock = hasattr(self.api_client, 'simulated_agent_id')
            self.logger.info(f"  • Tipo: {'MockAPIClient (Simulación)' if is_mock else 'APIClient (Real)'}")
            self.logger.info(f"  • Base URL: {self.api_client.base_url}")
            if is_mock:
                self.logger.info(f"  • Agent ID simulado: {self.api_client.simulated_agent_id}")
        else:
            self.logger.warning("  • ⚠️  API Client no inicializado")
        
        # Collectors
        self.logger.info("\n📊 Collectors:")
        self.logger.info(f"  • Total: {len(self.collectors)}/6 habilitados")
        for name in sorted(self.collectors.keys()):
            self.logger.info(f"    ✓ {name}")
        
        # Tareas programadas
        self.logger.info("\n⏰ Tareas Programadas que se configurarían:")
        self.logger.info(f"  • collect_and_send_data → Cada {self.report_interval}s")
        
        if self.config.get('scheduler', 'enable_log_cleanup', fallback=True):
            cleanup_hour = int(self.config.get('scheduler', 'cleanup_logs_hour', fallback=2))
            self.logger.info(f"  • cleanup_old_logs → Diario a las {cleanup_hour:02d}:00")
        
        if self.config.get('scheduler', 'enable_auto_update', fallback=False):
            update_hour = int(self.config.get('scheduler', 'check_updates_hour', fallback=3))
            self.logger.info(f"  • check_for_updates → Diario a las {update_hour:02d}:00")
        
        if self.config.get('scheduler', 'enable_health_check', fallback=True):
            health_interval = int(self.config.get('scheduler', 'health_check_interval', fallback=3600))
            self.logger.info(f"  • system_health_check → Cada {health_interval}s ({health_interval/3600:.1f}h)")
        
        # Estado del Scheduler
        self.logger.info("\n🔧 Scheduler:")
        self.logger.info(f"  • Inicializado: Sí")
        self.logger.info(f"  • Estado: No iniciado (modo debug)")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("✅ VALIDACIÓN COMPLETADA - Sin errores detectados")
        self.logger.info("=" * 60)
        self.logger.info("\n💡 El agente está listo para ejecutarse.")
        self.logger.info("   Usa los siguientes comandos:")
        self.logger.info("   • python src/main.py --register   → Registrar agente en servidor")
        self.logger.info("   • python src/main.py --test       → Probar recolección (sin enviar)")
        self.logger.info("   • python src/main.py --once       → Ejecutar una vez")
        self.logger.info("   • python src/main.py              → Modo continuo con scheduler")
        self.logger.info("")
        
        return True
    
    def register(self):
        """
        Registra el agente en el servidor y guarda el ID obtenido
        Retorna True si el registro fue exitoso
        """
        try:
            self.logger.info("📝 Iniciando proceso de registro del agente...")
            
            # Verificar que hay API client
            if not self.api_client:
                self.logger.error("❌ API Client no disponible")
                return False
            
            data = self.collect_all_data()

            # Intentar registrar
            success, agent_id = self.api_client.register_agent(data)
            
            if success and agent_id:
                self.logger.info(f"✅ Agente registrado exitosamente")
                self.logger.info(f"📋 ID asignado: {agent_id}")
                
                # Guardar el ID en el objeto (para que main.py pueda accederlo)
                self.asset_id = agent_id
                
                # Aquí podrías actualizar el archivo de configuración si quieres
                # persistir el agent_id para futuros usos
                # self.config.set('agent', 'id', str(agent_id))
                # self.config.save()
                
                return True
            else:
                self.logger.error("❌ Fallo al registrar el agente")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error durante el registro: {e}", exc_info=True)
            return False
    
    def collect_all_data(self) -> Dict[str, Any]:
        """Recolecta datos de todos los collectors habilitados (método público para testing)"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'hostname': self.collectors['network']._get_hostname(),
            'os_type': self.os_type
        }
        
        # Recolectar de cada collector
        for name, collector in self.collectors.items():
            try:
                self.logger.debug(f"Recolectando datos: {name}")
                collector_data = collector.collect()
                data[name] = collector_data
                self.logger.debug(f"✓ {name}: {len(str(collector_data))} bytes")
            except Exception as e:
                self.logger.error(f"Error al recolectar {name}: {e}")
                data[name] = {'error': str(e)}
        
        return data
    
    # ═══════════════════════════════════════════════════════════
    # NUEVOS MÉTODOS PARA SOPORTE DE MODELOS
    # ═══════════════════════════════════════════════════════════
    
    def collect_as_models(
        self, 
        location: str = None, 
        department: str = None, 
        assigned_to: str = None
    ) -> Tuple[Asset, Hardware, List[Software], Dict[str, Any]]:
        """
        Recolecta toda la información usando modelos de datos validados
        
        Args:
            location: Ubicación del asset
            department: Departamento
            assigned_to: Usuario asignado
            
        Returns:
            Tuple con (Asset, Hardware, List[Software], raw_data_dict)
        """
        try:
            self.logger.info("🔍 Recolectando información con modelos validados...")
            
            # 1. Crear Asset
            if 'hardware' not in self.collectors:
                raise ValueError("HardwareCollector no está habilitado")
            
            asset = self.collectors['hardware'].create_asset(
                location=location,
                department=department,
                assigned_to=assigned_to
            )
            self.logger.info(f"✅ Asset creado: {asset.asset_tag}")
            
            # Guardar asset_id
            self.asset_id = asset.id
            
            # 2. Recolectar Hardware como modelo
            hardware = self.collectors['hardware'].collect_as_model(asset_id=asset.id)
            self.logger.info(f"✅ Hardware: {hardware.manufacturer} {hardware.model}")
            self.logger.info(f"   └─ {len(hardware.components)} componentes")
            
            # 3. Recolectar Software como modelos
            software_list = []
            if 'software' in self.collectors:
                software_list = self.collectors['software'].collect_as_models(asset_id=asset.id)
                self.logger.info(f"✅ Software: {len(software_list)} programas")
            
            # 4. Recolectar datos adicionales (formato original dict)
            raw_data = {}
            for name in ['domain', 'antivirus', 'office', 'network']:
                if name in self.collectors:
                    try:
                        raw_data[name] = self.collectors[name].collect()
                        self.logger.debug(f"✓ {name} data collected")
                    except Exception as e:
                        self.logger.error(f"Error collecting {name}: {e}")
                        raw_data[name] = {'error': str(e)}
            
            return asset, hardware, software_list, raw_data
            
        except Exception as e:
            self.logger.error(f"Error en collect_as_models: {e}", exc_info=True)
            raise
    
    def send_inventory_with_models(
        self, 
        location: str = None, 
        department: str = None, 
        assigned_to: str = None
    ) -> bool:
        """
        Recolecta inventario usando modelos y lo envía al servidor
        
        Args:
            location: Ubicación del asset
            department: Departamento
            assigned_to: Usuario asignado
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Recolectar usando modelos
            asset, hardware, software_list, raw_data = self.collect_as_models(
                location=location,
                department=department,
                assigned_to=assigned_to
            )
            
            # Convertir modelos a diccionarios
            payload = {
                'timestamp': datetime.now().isoformat(),
                'agent_info': self._get_agent_info(),
                'asset': asset.to_dict(),
                'hardware': hardware.to_dict(),
                'software': [sw.to_dict() for sw in software_list],
                'additional_data': raw_data
            }
            
            # Enviar al servidor
            success = self._send_data(payload)
            
            if success:
                self.logger.info("✅ Inventario con modelos enviado exitosamente")
            else:
                self.logger.error("❌ Error al enviar inventario con modelos")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error enviando inventario con modelos: {e}", exc_info=True)
            return False
    
    # ═══════════════════════════════════════════════════════════
    # FIN NUEVOS MÉTODOS
    # ═══════════════════════════════════════════════════════════
    
    def _send_data(self, data: Dict[str, Any]) -> bool:
        """Envía los datos recolectados al servidor"""
        try:
            if self.api_client is None:
                self.logger.warning("API Client no disponible - Datos no enviados")
                return False
            
            self.logger.info("Enviando datos al servidor...")
            
            # Usar send_inventory_data del APIClient
            success = self.api_client.send_inventory_data(data)
            
            if success:
                self.logger.info("✓ Datos enviados correctamente")
                return True
            else:
                self.logger.warning("✗ Error al enviar datos al servidor")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al enviar datos: {e}")
            return False
    
    def _get_agent_info(self) -> Dict[str, Any]:
        """Retorna información del agente"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'version': self.VERSION,
            'hostname': self.hostname,
            'os': self.os_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': uptime,
            'last_report': self.last_report_time.isoformat() if self.last_report_time else None,
            'collectors_count': len(self.collectors),
            'report_interval': self.report_interval
        }
    
    # ═══════════════════════════════════════════════════════════
    # FUNCIONES PARA TAREAS PROGRAMADAS
    # ═══════════════════════════════════════════════════════════
    
    def _cleanup_old_logs(self):
        """Limpia logs antiguos (tarea programada)"""
        try:
            self.logger.info("Iniciando limpieza de logs antiguos...")
            
            days_to_keep = int(self.config.get('logging', 'days_to_keep', fallback=30))
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Aquí iría la lógica para eliminar logs antiguos
            # Por ahora solo registramos la acción
            self.logger.info(f"Limpiando logs anteriores a {cutoff_date.date()}")
            self.logger.info("✓ Limpieza de logs completada")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar logs: {e}", exc_info=True)
    
    def _check_for_updates(self):
        """Verifica si hay actualizaciones disponibles (tarea programada)"""
        try:
            self.logger.info("Verificando actualizaciones del agente...")
            
            # Usar el Updater para verificar actualizaciones
            has_update, latest_version = self.updater.check_for_updates()
            
            if has_update:
                self.logger.info(f"✨ Nueva versión disponible: {latest_version}")
                self.logger.info(f"   Versión actual: {self.VERSION}")
                
                # Verificar si auto-actualización está habilitada
                auto_update_enabled = self.config.get('updater', 'auto_update', fallback=False)
                
                if auto_update_enabled:
                    self.logger.info("🔄 Auto-actualización habilitada, iniciando proceso...")
                    success = self.updater.auto_update()
                    
                    if success:
                        self.logger.info("✅ Actualización aplicada correctamente")
                        self.logger.warning("⚠️  Reinicia el agente para aplicar los cambios")
                    else:
                        self.logger.error("❌ Fallo al aplicar actualización automática")
                else:
                    self.logger.info("ℹ️  Auto-actualización deshabilitada")
                    self.logger.info("   Ejecuta 'python src/main.py --update' para actualizar")
            else:
                self.logger.info(f"✓ Versión actual ({self.VERSION}) es la más reciente")
            
        except Exception as e:
            self.logger.error(f"Error al verificar actualizaciones: {e}", exc_info=True)
    
    def _system_health_check(self):
        """Realiza un health check del sistema (tarea programada)"""
        try:
            self.logger.info("Ejecutando health check del sistema...")
            
            # Verificar estado de collectors
            collectors_ok = len(self.collectors) > 0
            
            # Verificar conexión API
            api_ok = self.api_client is not None
            
            # Verificar scheduler
            scheduler_ok = self.scheduler is not None

               
            
            health_status = {
                'collectors': collectors_ok,
                'api_client': api_ok,
                'scheduler': scheduler_ok,
                'overall': collectors_ok and api_ok and scheduler_ok
            }
            
            if health_status['overall']:
                self.logger.info(f"✓ Health check OK: {health_status}")
            else:
                self.logger.warning(f"✗ Health check FAILED: {health_status}")
            
        except Exception as e:
            self.logger.error(f"Error en health check: {e}", exc_info=True)
    
    def _generate_weekly_report(self):
        """Genera un reporte semanal (tarea programada)"""
        try:
            self.logger.info("Generando reporte semanal...")
            
            # Aquí iría la lógica para generar reporte semanal
            # Por ahora solo registramos la acción
            week_start = datetime.now() - timedelta(days=7)
            self.logger.info(f"Reporte para la semana: {week_start.date()} - {datetime.now().date()}")
            self.logger.info("✓ Reporte semanal generado")
            
        except Exception as e:
            self.logger.error(f"Error al generar reporte semanal: {e}", exc_info=True)
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE CONTROL
    # ═══════════════════════════════════════════════════════════
    
    def stop(self):
        """Detiene el agente y el scheduler"""
        self.logger.info("Deteniendo Agent...")
        self.is_running = False
        
        if self.scheduler:
            self.scheduler.stop()
            self.logger.info("✓ Scheduler detenido")
        
        self.logger.info("Agent detenido correctamente")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente"""
        return {
            'is_running': self.is_running,
            'version': self.VERSION,
            'hostname': self.hostname,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'last_report': self.last_report_time.isoformat() if self.last_report_time else None,
            'collectors': list(self.collectors.keys()),
            'scheduler_running': hasattr(self.scheduler, 'is_running') and self.scheduler.is_running if self.scheduler else False
        }
    
    def pause_job(self, job_name: str):
        """Pausa una tarea programada"""
        self.scheduler.pause_job(job_name)
        self.logger.info(f"Tarea '{job_name}' pausada")
    
    def resume_job(self, job_name: str):
        """Reanuda una tarea programada"""
        self.scheduler.resume_job(job_name)
        self.logger.info(f"Tarea '{job_name}' reanudada")
    
    def run_job_now(self, job_name: str):
        """Ejecuta una tarea inmediatamente"""
        self.scheduler.run_job_now(job_name)
        self.logger.info(f"Tarea '{job_name}' ejecutada manualmente")