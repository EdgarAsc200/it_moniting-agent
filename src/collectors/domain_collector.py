"""
Domain Collector - Recopila información de dominio/Active Directory
Multiplataforma: Windows, macOS, Linux
"""

import platform
import subprocess
import os
from typing import Dict, Any, List

from .base_collector import BaseCollector


class DomainCollector(BaseCollector):
    """
    Recopila información sobre configuración de dominio
    """
    
    def __init__(self):
        super().__init__()
        self.system = platform.system()
    
    def collect(self) -> Dict[str, Any]:
        """
        Recopila información de dominio
        
        Returns:
            dict: Información de dominio del sistema
        """
        info = {
            'is_domain_joined': False,
            'domain_name': None,
            'domain_user': None,
            'workgroup': None,
            'domain_controller': None,
            'last_ad_sync': None,
            'applied_group_policies': []
        }
        
        if self.system == "Windows":
            info.update(self.get_windows_domain_info())
        elif self.system == "Linux":
            info.update(self.get_linux_domain_info())
        elif self.system == "Darwin":
            info.update(self.get_macos_domain_info())
        
        return info
    
    def get_windows_domain_info(self) -> Dict[str, Any]:
        """Obtiene información de dominio en Windows"""
        info = {}
        
        try:
            import wmi
            c = wmi.WMI()
            
            # Verificar si está en dominio
            for cs in c.Win32_ComputerSystem():
                if cs.PartOfDomain:
                    info['is_domain_joined'] = True
                    info['domain_name'] = cs.Domain
                    info['workgroup'] = None
                else:
                    info['is_domain_joined'] = False
                    info['domain_name'] = None
                    info['workgroup'] = cs.Workgroup
            
            # Obtener usuario actual
            info['domain_user'] = os.getenv('USERNAME')
            
            # Obtener controlador de dominio
            if info.get('is_domain_joined'):
                try:
                    logon_server = os.getenv('LOGONSERVER')
                    if logon_server:
                        info['domain_controller'] = logon_server.replace('\\\\', '')
                except Exception as e:
                    self.logger.debug(f"Error al obtener LOGONSERVER: {e}")
                
                # Obtener GPOs aplicadas
                info['applied_group_policies'] = self.get_applied_gpos()
            
        except ImportError:
            self.logger.warning("Librería WMI no disponible, usando métodos alternativos")
            info = self.get_windows_domain_info_fallback()
        except Exception as e:
            self.logger.error(f"Error al obtener info de dominio Windows: {e}")
        
        return info
    
    def get_windows_domain_info_fallback(self) -> Dict[str, Any]:
        """Método alternativo para obtener info de dominio en Windows"""
        info = {
            'is_domain_joined': False,
            'domain_name': None,
            'domain_user': os.getenv('USERNAME'),
            'workgroup': None,
            'domain_controller': None,
            'applied_group_policies': []
        }
        
        try:
            # Verificar si está en dominio usando systeminfo
            cmd = 'systeminfo | findstr /B /C:"Domain"'
            result = subprocess.check_output(cmd, shell=True, text=True, timeout=10)
            
            if result:
                domain = result.split(':')[1].strip()
                if domain.lower() != 'workgroup':
                    info['is_domain_joined'] = True
                    info['domain_name'] = domain
                else:
                    info['workgroup'] = domain
            
            # Obtener logon server
            logon_server = os.getenv('LOGONSERVER')
            if logon_server:
                info['domain_controller'] = logon_server.replace('\\\\', '')
                
        except subprocess.TimeoutExpired:
            self.logger.warning("Timeout al ejecutar systeminfo")
        except Exception as e:
            self.logger.error(f"Error en método fallback: {e}")
        
        return info
    
    def get_applied_gpos(self) -> List[str]:
        """Obtiene las GPOs aplicadas en Windows"""
        gpos = []
        
        try:
            cmd = 'gpresult /R /SCOPE:COMPUTER'
            result = subprocess.check_output(cmd, shell=True, text=True, 
                                            errors='ignore', timeout=30)
            
            # Parsear el resultado para extraer GPOs
            lines = result.split('\n')
            in_gpo_section = False
            
            for line in lines:
                if 'Applied Group Policy Objects' in line:
                    in_gpo_section = True
                    continue
                
                if in_gpo_section:
                    if line.strip() and not line.startswith('--'):
                        gpo_name = line.strip()
                        if gpo_name and gpo_name not in gpos:
                            gpos.append(gpo_name)
                    
                    # Salir si encontramos otra sección
                    if 'The following GPOs were not applied' in line:
                        break
                        
        except subprocess.TimeoutExpired:
            self.logger.warning("Timeout al ejecutar gpresult")
        except Exception as e:
            self.logger.warning(f"No se pudieron obtener GPOs: {e}")
        
        return gpos
    
    def get_linux_domain_info(self) -> Dict[str, Any]:
        """Obtiene información de dominio en Linux"""
        info = {
            'is_domain_joined': False,
            'domain_name': None,
            'domain_user': os.getenv('USER'),
            'workgroup': None,
            'domain_controller': None,
            'applied_group_policies': []
        }
        
        try:
            # Verificar si está unido a un dominio AD (usando realm o similar)
            # Verificar Samba/Winbind
            if os.path.exists('/etc/samba/smb.conf'):
                with open('/etc/samba/smb.conf', 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'workgroup' in line.lower() and '=' in line:
                            workgroup = line.split('=')[1].strip()
                            info['workgroup'] = workgroup
                            break
            
            # Verificar realm (FreeIPA, AD)
            try:
                cmd = 'realm list'
                result = subprocess.check_output(cmd, shell=True, text=True, 
                                                stderr=subprocess.DEVNULL, timeout=10)
                if result:
                    info['is_domain_joined'] = True
                    # Parsear salida de realm
                    for line in result.split('\n'):
                        if 'domain-name:' in line.lower():
                            info['domain_name'] = line.split(':')[1].strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Verificar sssd
            if os.path.exists('/etc/sssd/sssd.conf'):
                info['is_domain_joined'] = True
                try:
                    # Intentar leer la configuración de sssd (puede requerir permisos)
                    cmd = 'sudo cat /etc/sssd/sssd.conf 2>/dev/null || cat /etc/sssd/sssd.conf 2>/dev/null'
                    result = subprocess.check_output(cmd, shell=True, text=True, timeout=5)
                    # Buscar dominio en la configuración
                    for line in result.split('\n'):
                        if 'ldap_uri' in line or 'ad_domain' in line:
                            parts = line.split('=')
                            if len(parts) > 1:
                                info['domain_controller'] = parts[1].strip()
                                break
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error al obtener info de dominio Linux: {e}")
        
        return info
    
    def get_macos_domain_info(self) -> Dict[str, Any]:
        """Obtiene información de dominio en macOS"""
        info = {
            'is_domain_joined': False,
            'domain_name': None,
            'domain_user': os.getenv('USER'),
            'workgroup': None,
            'domain_controller': None,
            'applied_group_policies': []
        }
        
        try:
            # Verificar si está unido a Active Directory
            cmd = 'dsconfigad -show'
            result = subprocess.check_output(cmd, shell=True, text=True, 
                                            stderr=subprocess.DEVNULL, timeout=10)
            
            if result and 'Active Directory Domain' in result:
                info['is_domain_joined'] = True
                
                # Parsear información
                for line in result.split('\n'):
                    if 'Active Directory Domain' in line and '=' in line:
                        info['domain_name'] = line.split('=')[1].strip()
                    elif 'Active Directory Forest' in line and '=' in line:
                        # Podríamos agregar forest si es necesario
                        pass
            
            # Verificar Open Directory (alternativa de Apple a AD)
            try:
                cmd = 'dscl localhost -list /LDAPv3'
                result = subprocess.check_output(cmd, shell=True, text=True,
                                                stderr=subprocess.DEVNULL, timeout=10)
                if result.strip():
                    info['is_domain_joined'] = True
                    if not info['domain_name']:
                        info['domain_name'] = 'Open Directory'
            except subprocess.CalledProcessError:
                pass
                
        except subprocess.CalledProcessError:
            # No está en dominio
            info['is_domain_joined'] = False
        except Exception as e:
            self.logger.error(f"Error al obtener info de dominio macOS: {e}")
        
        return info