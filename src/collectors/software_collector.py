# src/collectors/software_collector.py

import platform
import subprocess
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Importar modelos
from models import Software, SoftwareType


class SoftwareCollector:
    """
    Recopila información sobre el software instalado.
    Soporta Windows, macOS y Linux.
    """
    
    def __init__(self):
        self.os_type = platform.system()
    
    def collect(self) -> Dict[str, Any]:
        """
        Recopila información de software instalado
        """
        software_list = []
        
        if self.os_type == "Windows":
            software_list = self._collect_windows()
        elif self.os_type == "Darwin":
            software_list = self._collect_macos()
        elif self.os_type == "Linux":
            software_list = self._collect_linux()
        
        return {
            'report_date': datetime.now().isoformat(),
            'total_software': len(software_list),
            'installed_software': software_list
        }
    
    def _collect_windows(self) -> List[Dict[str, Any]]:
        """Recopila software instalado en Windows"""
        software_list = []
        
        try:
            # PowerShell script para obtener software del registro
            ps_script = """
            $software = @()
            
            $paths = @(
                'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
                'HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
                'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'
            )
            
            foreach ($path in $paths) {
                Get-ItemProperty $path -ErrorAction SilentlyContinue | 
                Where-Object { $_.DisplayName } | 
                ForEach-Object {
                    $software += [PSCustomObject]@{
                        Name = $_.DisplayName
                        Version = $_.DisplayVersion
                        Publisher = $_.Publisher
                        InstallDate = $_.InstallDate
                        InstallLocation = $_.InstallLocation
                        EstimatedSize = $_.EstimatedSize
                    }
                }
            }
            
            $software | ConvertTo-Json -Depth 3
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                software_data = json.loads(result.stdout)
                
                # Si es un solo elemento, convertirlo a lista
                if isinstance(software_data, dict):
                    software_data = [software_data]
                
                for sw in software_data:
                    software_list.append({
                        'software_name': sw.get('Name', ''),
                        'version': sw.get('Version', ''),
                        'vendor': sw.get('Publisher', ''),
                        'install_date': sw.get('InstallDate', ''),
                        'install_location': sw.get('InstallLocation', ''),
                        'size_mb': sw.get('EstimatedSize', 0),
                        'source': 'registry'
                    })
        
        except Exception as e:
            print(f"Error collecting Windows software: {e}")
        
        return software_list
    
    def _collect_macos(self) -> List[Dict[str, Any]]:
        """Recopila software instalado en macOS"""
        software_list = []
        
        try:
            # Aplicaciones del directorio /Applications
            result = subprocess.run(
                ["ls", "-1", "/Applications"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                apps = result.stdout.strip().split('\n')
                for app in apps:
                    if app.endswith('.app'):
                        app_name = app.replace('.app', '')
                        
                        # Intentar obtener versión
                        version = self._get_macos_app_version(f"/Applications/{app}")
                        
                        software_list.append({
                            'software_name': app_name,
                            'version': version or 'Unknown',
                            'vendor': 'Unknown',
                            'install_date': '',
                            'install_location': f'/Applications/{app}',
                            'size_mb': 0,
                            'source': 'applications'
                        })
            
            # Homebrew packages
            if self._command_exists('brew'):
                result = subprocess.run(
                    ["brew", "list", "--versions"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split()
                            if len(parts) >= 2:
                                software_list.append({
                                    'software_name': parts[0],
                                    'version': parts[1] if len(parts) > 1 else 'Unknown',
                                    'vendor': 'Homebrew',
                                    'install_date': '',
                                    'install_location': '/usr/local/Cellar/' + parts[0],
                                    'size_mb': 0,
                                    'source': 'homebrew'
                                })
        
        except Exception as e:
            print(f"Error collecting macOS software: {e}")
        
        return software_list
    
    def _get_macos_app_version(self, app_path: str) -> Optional[str]:
        """Obtiene la versión de una aplicación macOS"""
        try:
            plist_path = f"{app_path}/Contents/Info.plist"
            result = subprocess.run(
                ["defaults", "read", plist_path, "CFBundleShortVersionString"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def _collect_linux(self) -> List[Dict[str, Any]]:
        """Recopila software instalado en Linux"""
        software_list = []
        
        try:
            # Detectar gestor de paquetes
            if self._command_exists('dpkg'):
                software_list.extend(self._collect_dpkg())
            elif self._command_exists('rpm'):
                software_list.extend(self._collect_rpm())
            elif self._command_exists('pacman'):
                software_list.extend(self._collect_pacman())
            
            # Snap packages
            if self._command_exists('snap'):
                software_list.extend(self._collect_snap())
            
            # Flatpak packages
            if self._command_exists('flatpak'):
                software_list.extend(self._collect_flatpak())
        
        except Exception as e:
            print(f"Error collecting Linux software: {e}")
        
        return software_list
    
    def _collect_dpkg(self) -> List[Dict[str, Any]]:
        """Recopila paquetes dpkg (Debian/Ubuntu)"""
        software_list = []
        
        try:
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n')[5:]:  # Skip header
                    if line.startswith('ii'):
                        parts = line.split()
                        if len(parts) >= 3:
                            software_list.append({
                                'software_name': parts[1],
                                'version': parts[2],
                                'vendor': 'dpkg',
                                'install_date': '',
                                'install_location': '',
                                'size_mb': 0,
                                'source': 'dpkg'
                            })
        except Exception as e:
            print(f"Error collecting dpkg packages: {e}")
        
        return software_list
    
    def _collect_rpm(self) -> List[Dict[str, Any]]:
        """Recopila paquetes RPM (RedHat/CentOS/Fedora)"""
        software_list = []
        
        try:
            result = subprocess.run(
                ["rpm", "-qa", "--queryformat", "%{NAME}|%{VERSION}|%{RELEASE}\n"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('|')
                    if len(parts) >= 2:
                        software_list.append({
                            'software_name': parts[0],
                            'version': f"{parts[1]}-{parts[2]}" if len(parts) > 2 else parts[1],
                            'vendor': 'rpm',
                            'install_date': '',
                            'install_location': '',
                            'size_mb': 0,
                            'source': 'rpm'
                        })
        except Exception as e:
            print(f"Error collecting RPM packages: {e}")
        
        return software_list
    
    def _collect_pacman(self) -> List[Dict[str, Any]]:
        """Recopila paquetes Pacman (Arch Linux)"""
        software_list = []
        
        try:
            result = subprocess.run(
                ["pacman", "-Q"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        software_list.append({
                            'software_name': parts[0],
                            'version': parts[1],
                            'vendor': 'pacman',
                            'install_date': '',
                            'install_location': '',
                            'size_mb': 0,
                            'source': 'pacman'
                        })
        except Exception as e:
            print(f"Error collecting Pacman packages: {e}")
        
        return software_list
    
    def _collect_snap(self) -> List[Dict[str, Any]]:
        """Recopila paquetes Snap"""
        software_list = []
        
        try:
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        software_list.append({
                            'software_name': parts[0],
                            'version': parts[1],
                            'vendor': 'snap',
                            'install_date': '',
                            'install_location': f'/snap/{parts[0]}',
                            'size_mb': 0,
                            'source': 'snap'
                        })
        except Exception as e:
            print(f"Error collecting Snap packages: {e}")
        
        return software_list
    
    def _collect_flatpak(self) -> List[Dict[str, Any]]:
        """Recopila paquetes Flatpak"""
        software_list = []
        
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=name,version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 1:
                        software_list.append({
                            'software_name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'Unknown',
                            'vendor': 'flatpak',
                            'install_date': '',
                            'install_location': '',
                            'size_mb': 0,
                            'source': 'flatpak'
                        })
        except Exception as e:
            print(f"Error collecting Flatpak packages: {e}")
        
        return software_list
    
    def _command_exists(self, command: str) -> bool:
        """Verifica si un comando existe"""
        try:
            subprocess.run(
                ["which" if self.os_type != "Windows" else "where", command],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS PARA MODELOS
    # ═══════════════════════════════════════════════════════════
    
    def collect_as_models(self, asset_id: str) -> List[Software]:
        """
        Recopila información de software y retorna lista de modelos Software
        
        Args:
            asset_id: ID del asset asociado
            
        Returns:
            List[Software]: Lista de instancias del modelo Software validadas
        """
        # Recolectar datos usando el método original
        data = self.collect()
        
        software_list = []
        installed_software = data.get('installed_software', [])
        
        for sw_data in installed_software:
            try:
                software = self._create_software_model(sw_data, asset_id)
                software_list.append(software)
            except Exception as e:
                # Log error pero continuar con el resto
                print(f"⚠️  Error al mapear software {sw_data.get('software_name', 'Unknown')}: {e}")
                continue
        
        return software_list
    
    def _create_software_model(self, sw_data: Dict[str, Any], asset_id: str) -> Software:
        """Crea un modelo Software desde datos raw"""
        # Generar ID único
        software_id = str(uuid.uuid4())
        
        # Extraer datos básicos
        name = sw_data.get('software_name') or sw_data.get('name', 'Unknown')
        version = sw_data.get('version')
        vendor = sw_data.get('vendor') or sw_data.get('publisher')
        
        # Detectar tipo de software
        software_type = self._detect_software_type(name, vendor)
        
        # Parsear fecha de instalación
        install_date_str = sw_data.get('install_date')
        install_date = self._parse_install_date(install_date_str) if install_date_str else None
        
        # Extraer tamaño
        install_size = sw_data.get('size_mb') or sw_data.get('estimated_size')
        if install_size and isinstance(install_size, (int, float)):
            if install_size < 100:
                install_size_mb = None
            else:
                install_size_mb = int(install_size)
        else:
            install_size_mb = None
        
        # Crear modelo Software
        software = Software(
            id=software_id,
            asset_id=asset_id,
            name=name,
            version=version,
            vendor=vendor,
            software_type=software_type,
            install_date=install_date,
            install_path=sw_data.get('install_location') or sw_data.get('install_path'),
            install_size_mb=install_size_mb,
            architecture=sw_data.get('architecture'),
            is_active=True,
            custom_fields={
                'uninstall_string': sw_data.get('uninstall_string'),
                'registry_key': sw_data.get('registry_key'),
                'source': sw_data.get('source', 'system_registry')
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Validar
        software.validate()
        
        return software
    
    def _detect_software_type(self, software_name: str, vendor: str = None) -> SoftwareType:
        """Detecta el tipo de software basándose en el nombre y vendor"""
        name_lower = software_name.lower()
        vendor_lower = (vendor or '').lower()
        
        # Seguridad
        if any(keyword in name_lower for keyword in ['antivirus', 'security', 'defender', 'firewall', 'malware']):
            return SoftwareType.SECURITY
        
        # Desarrollo
        elif any(keyword in name_lower for keyword in ['visual studio', 'python', 'java', 'node', 'git', 'sdk', 'compiler']):
            return SoftwareType.DEVELOPMENT
        
        # Productividad
        elif any(keyword in name_lower for keyword in ['office', 'word', 'excel', 'powerpoint', 'outlook', 'adobe']):
            return SoftwareType.PRODUCTIVITY
        
        # Sistema
        elif any(keyword in name_lower for keyword in ['driver', 'runtime', 'redistributable', 'framework', '.net']):
            return SoftwareType.SYSTEM
        
        # Utilidades
        elif any(keyword in name_lower for keyword in ['utility', 'tool', 'cleaner', 'optimizer']):
            return SoftwareType.UTILITY
        
        # Por defecto
        else:
            return SoftwareType.APPLICATION
    
    def _parse_install_date(self, date_str: str) -> Optional[datetime]:
        """Parsea la fecha de instalación desde diferentes formatos"""
        if not date_str:
            return None
        
        # Formato: YYYYMMDD (común en Windows)
        if len(date_str) == 8 and date_str.isdigit():
            try:
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                return datetime(year, month, day)
            except:
                return None
        
        # Formato ISO
        try:
            return datetime.fromisoformat(date_str)
        except:
            pass
        
        return None