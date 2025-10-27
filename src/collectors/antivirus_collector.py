# src/collectors/antivirus_collector.py

import platform
import subprocess
import re
import logging
from datetime import datetime
from typing import Dict, Optional, List

class AntivirusCollector:
    """
    Recopila información sobre el antivirus y seguridad del sistema.
    Funciona en Windows, macOS y Linux.
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self.logger = logging.getLogger('ITAgent.AntivirusCollector')
    
    def safe_collect(self) -> Dict:
        """
        Método seguro de recopilación con manejo de errores
        
        Returns:
            dict: Datos de antivirus, o datos vacíos en caso de error
        """
        try:
            return self.collect()
        except Exception as e:
            self.logger.error(f"Error en recopilación de antivirus: {e}", exc_info=True)
            return self._get_empty_data()
    
    def collect(self) -> Dict:
        """Recopila toda la información de antivirus y seguridad"""
        
        self.logger.debug(f"Recopilando información de antivirus en {self.os_type}...")
        
        if self.os_type == "Windows":
            return self._collect_windows()
        elif self.os_type == "Darwin":  # macOS
            return self._collect_macos()
        elif self.os_type == "Linux":
            return self._collect_linux()
        else:
            return self._get_empty_data()
    
    def _collect_windows(self) -> Dict:
        """Recopila información de antivirus en Windows"""
        data = {
            'antivirus_name': None,
            'antivirus_version': None,
            'protection_status': 'Unknown',
            'last_update': None,
            'last_scan': None,
            'firewall_status': 'Unknown',
            'real_time_protection': False,
            'definitions_up_to_date': False
        }
        
        try:
            # Obtener información de Windows Security usando PowerShell
            antivirus_info = self._get_windows_defender_info()
            if antivirus_info:
                data.update(antivirus_info)
            
            # Verificar otros antivirus instalados
            third_party_av = self._detect_third_party_antivirus_windows()
            if third_party_av:
                data['third_party_antivirus'] = third_party_av
            
            # Estado del firewall
            firewall_status = self._get_windows_firewall_status()
            data['firewall_status'] = firewall_status
            
        except Exception as e:
            self.logger.error(f"Error en recopilación de Windows: {e}")
            data['error'] = str(e)
        
        return data
    
    def _get_windows_defender_info(self) -> Optional[Dict]:
        """Obtiene información de Windows Defender usando PowerShell"""
        try:
            # Comando PowerShell para obtener estado de Windows Defender
            ps_command = """
            $status = Get-MpComputerStatus
            $prefs = Get-MpPreference
            
            [PSCustomObject]@{
                AntivirusEnabled = $status.AntivirusEnabled
                RealTimeProtectionEnabled = $status.RealTimeProtectionEnabled
                AntivirusSignatureLastUpdated = $status.AntivirusSignatureLastUpdated
                FullScanAge = $status.FullScanAge
                QuickScanAge = $status.QuickScanAge
                AntivirusSignatureVersion = $status.AntivirusSignatureVersion
                EngineVersion = $status.AMEngineVersion
            } | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                import json
                defender_data = json.loads(result.stdout)
                
                return {
                    'antivirus_name': 'Windows Defender',
                    'antivirus_version': defender_data.get('AntivirusSignatureVersion', 'Unknown'),
                    'protection_status': 'Active' if defender_data.get('AntivirusEnabled') else 'Inactive',
                    'real_time_protection': defender_data.get('RealTimeProtectionEnabled', False),
                    'last_update': defender_data.get('AntivirusSignatureLastUpdated'),
                    'last_scan': self._calculate_last_scan(
                        defender_data.get('QuickScanAge'),
                        defender_data.get('FullScanAge')
                    ),
                    'engine_version': defender_data.get('EngineVersion'),
                    'definitions_up_to_date': defender_data.get('AntivirusEnabled', False)
                }
        except Exception as e:
            self.logger.debug(f"Error obteniendo info de Windows Defender: {e}")
            return None
    
    def _detect_third_party_antivirus_windows(self) -> List[str]:
        """Detecta antivirus de terceros instalados en Windows"""
        known_antivirus = []
        
        try:
            # Buscar en WMI por productos de seguridad
            ps_command = """
            Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | 
            Select-Object displayName, productState | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                import json
                av_products = json.loads(result.stdout)
                
                # Puede ser una lista o un solo objeto
                if isinstance(av_products, dict):
                    av_products = [av_products]
                
                for av in av_products:
                    av_name = av.get('displayName', '')
                    if av_name and 'Windows Defender' not in av_name:
                        known_antivirus.append(av_name)
        
        except Exception as e:
            self.logger.debug(f"Error detectando antivirus de terceros: {e}")
        
        return known_antivirus
    
    def _get_windows_firewall_status(self) -> str:
        """Obtiene el estado del firewall de Windows"""
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'on' in output or 'activ' in output:
                    return 'Active'
                elif 'off' in output or 'inactiv' in output:
                    return 'Inactive'
        except Exception as e:
            self.logger.debug(f"Error obteniendo estado del firewall: {e}")
        
        return 'Unknown'
    
    def _collect_macos(self) -> Dict:
        """Recopila información de seguridad en macOS"""
        data = {
            'antivirus_name': 'XProtect (Built-in)',
            'antivirus_version': None,
            'protection_status': 'Active',
            'firewall_status': 'Unknown',
            'gatekeeper_status': 'Unknown',
            'system_integrity_protection': 'Unknown'
        }
        
        try:
            # Estado del Firewall
            firewall_result = subprocess.run(
                ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if firewall_result.returncode == 0:
                if 'enabled' in firewall_result.stdout.lower():
                    data['firewall_status'] = 'Active'
                else:
                    data['firewall_status'] = 'Inactive'
            
            # Estado de Gatekeeper
            gatekeeper_result = subprocess.run(
                ["spctl", "--status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if gatekeeper_result.returncode == 0:
                if 'enabled' in gatekeeper_result.stdout.lower():
                    data['gatekeeper_status'] = 'Active'
                else:
                    data['gatekeeper_status'] = 'Inactive'
            
            # System Integrity Protection (SIP)
            sip_result = subprocess.run(
                ["csrutil", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if sip_result.returncode == 0:
                if 'enabled' in sip_result.stdout.lower():
                    data['system_integrity_protection'] = 'Active'
                else:
                    data['system_integrity_protection'] = 'Inactive'
            
            # Detectar antivirus de terceros
            third_party = self._detect_third_party_antivirus_macos()
            if third_party:
                data['third_party_antivirus'] = third_party
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de macOS: {e}")
            data['error'] = str(e)
        
        return data
    
    def _detect_third_party_antivirus_macos(self) -> List[str]:
        """Detecta antivirus de terceros en macOS"""
        known_av_paths = [
            '/Applications/Avast.app',
            '/Applications/AVG AntiVirus.app',
            '/Applications/Bitdefender Antivirus.app',
            '/Applications/Norton Security.app',
            '/Applications/Kaspersky Internet Security.app',
            '/Applications/ESET Cyber Security.app',
            '/Applications/Sophos Home.app',
            '/Applications/Malwarebytes.app',
            '/Applications/McAfee Security.app'
        ]
        
        detected = []
        for path in known_av_paths:
            try:
                result = subprocess.run(
                    ["test", "-d", path],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    av_name = path.split('/')[-1].replace('.app', '')
                    detected.append(av_name)
            except Exception:
                continue
        
        return detected
    
    def _collect_linux(self) -> Dict:
        """Recopila información de seguridad en Linux"""
        data = {
            'antivirus_name': None,
            'antivirus_version': None,
            'protection_status': 'Unknown',
            'firewall_status': 'Unknown',
            'selinux_status': 'Unknown',
            'apparmor_status': 'Unknown'
        }
        
        try:
            # Detectar antivirus
            av_info = self._detect_linux_antivirus()
            if av_info:
                data.update(av_info)
            
            # Estado del firewall (ufw o firewalld)
            firewall_status = self._get_linux_firewall_status()
            data['firewall_status'] = firewall_status
            
            # SELinux
            selinux_status = self._get_selinux_status()
            data['selinux_status'] = selinux_status
            
            # AppArmor
            apparmor_status = self._get_apparmor_status()
            data['apparmor_status'] = apparmor_status
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de Linux: {e}")
            data['error'] = str(e)
        
        return data
    
    def _detect_linux_antivirus(self) -> Optional[Dict]:
        """Detecta antivirus en Linux"""
        # ClamAV
        if self._command_exists('clamscan'):
            try:
                result = subprocess.run(
                    ['clamscan', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version_match = re.search(r'ClamAV\s+([\d.]+)', result.stdout)
                    version = version_match.group(1) if version_match else 'Unknown'
                    
                    return {
                        'antivirus_name': 'ClamAV',
                        'antivirus_version': version,
                        'protection_status': 'Installed'
                    }
            except Exception:
                pass
        
        # Otros antivirus comunes en Linux
        linux_av_commands = {
            'sophos': 'Sophos',
            'f-prot': 'F-PROT',
            'avast': 'Avast',
            'avg': 'AVG'
        }
        
        for cmd, name in linux_av_commands.items():
            if self._command_exists(cmd):
                return {
                    'antivirus_name': name,
                    'protection_status': 'Installed'
                }
        
        return None
    
    def _get_linux_firewall_status(self) -> str:
        """Obtiene el estado del firewall en Linux"""
        # Verificar UFW
        if self._command_exists('ufw'):
            try:
                result = subprocess.run(
                    ['ufw', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if 'active' in result.stdout.lower():
                    return 'Active (UFW)'
                elif 'inactive' in result.stdout.lower():
                    return 'Inactive (UFW)'
            except Exception:
                pass
        
        # Verificar firewalld
        if self._command_exists('firewall-cmd'):
            try:
                result = subprocess.run(
                    ['firewall-cmd', '--state'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if 'running' in result.stdout.lower():
                    return 'Active (firewalld)'
                else:
                    return 'Inactive (firewalld)'
            except Exception:
                pass
        
        # Verificar iptables
        if self._command_exists('iptables'):
            try:
                result = subprocess.run(
                    ['iptables', '-L', '-n'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout:
                    return 'Active (iptables)'
            except Exception:
                pass
        
        return 'Unknown'
    
    def _get_selinux_status(self) -> str:
        """Obtiene el estado de SELinux"""
        if self._command_exists('getenforce'):
            try:
                result = subprocess.run(
                    ['getenforce'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                return result.stdout.strip() if result.returncode == 0 else 'Unknown'
            except Exception:
                pass
        
        return 'Not installed'
    
    def _get_apparmor_status(self) -> str:
        """Obtiene el estado de AppArmor"""
        if self._command_exists('aa-status'):
            try:
                result = subprocess.run(
                    ['aa-status', '--enabled'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    return 'Active'
                else:
                    return 'Inactive'
            except Exception:
                pass
        
        return 'Not installed'
    
    def _calculate_last_scan(self, quick_scan_age: Optional[int], full_scan_age: Optional[int]) -> Optional[str]:
        """Calcula la fecha del último escaneo"""
        try:
            if quick_scan_age is not None or full_scan_age is not None:
                # Usar el escaneo más reciente
                scan_age = min(filter(None, [quick_scan_age, full_scan_age]))
                
                from datetime import timedelta
                last_scan_date = datetime.now() - timedelta(days=scan_age)
                return last_scan_date.isoformat()
        except Exception:
            pass
        
        return None
    
    def _command_exists(self, command: str) -> bool:
        """Verifica si un comando existe en el sistema"""
        try:
            subprocess.run(
                ["which" if self.os_type != "Windows" else "where", command],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False
    
    def _get_empty_data(self) -> Dict:
        """Retorna estructura de datos vacía"""
        return {
            'antivirus_name': None,
            'antivirus_version': None,
            'protection_status': 'Unknown',
            'firewall_status': 'Unknown',
            'error': 'Collector failed'
        }