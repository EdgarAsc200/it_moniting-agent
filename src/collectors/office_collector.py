# src/collectors/office_collector.py

import platform
import subprocess
import re
import logging
from typing import Dict, Optional, List
from datetime import datetime

class OfficeCollector:
    """
    Recopila información sobre Microsoft Office instalado.
    Funciona en Windows, macOS y Linux.
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self.logger = logging.getLogger('ITAgent.OfficeCollector')
    
    def safe_collect(self) -> Dict:
        """
        Método seguro de recopilación con manejo de errores
        
        Returns:
            dict: Datos de Office, o datos vacíos en caso de error
        """
        try:
            return self.collect()
        except Exception as e:
            self.logger.error(f"Error en recopilación de Office: {e}", exc_info=True)
            return self._get_empty_data()
    
    def collect(self) -> Dict:
        """Recopila toda la información de Microsoft Office"""
        
        self.logger.debug(f"Recopilando información de Office en {self.os_type}...")
        
        if self.os_type == "Windows":
            return self._collect_windows()
        elif self.os_type == "Darwin":  # macOS
            return self._collect_macos()
        elif self.os_type == "Linux":
            return self._collect_linux()
        else:
            return self._get_empty_data()
    
    def _collect_windows(self) -> Dict:
        """Recopila información de Office en Windows"""
        data = {
            'office_installed': False,
            'office_version': None,
            'office_edition': None,
            'office_build': None,
            'office_architecture': None,
            'license_type': None,
            'license_status': None,
            'product_key_last5': None,
            'installed_apps': []
        }
        
        try:
            # Método 1: Buscar en el registro de Windows
            office_info = self._detect_office_registry()
            if office_info:
                data.update(office_info)
                data['office_installed'] = True
            
            # Método 2: Buscar ejecutables de Office
            if not data['office_installed']:
                office_path_info = self._detect_office_by_path_windows()
                if office_path_info:
                    data.update(office_path_info)
                    data['office_installed'] = True
            
            # Obtener información de licencia
            if data['office_installed']:
                license_info = self._get_office_license_windows()
                if license_info:
                    data.update(license_info)
                
                # Detectar aplicaciones instaladas
                apps = self._detect_office_apps_windows()
                data['installed_apps'] = apps
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de Office Windows: {e}")
            data['error'] = str(e)
        
        return data
    
    def _detect_office_registry(self) -> Optional[Dict]:
        """Detecta Office leyendo el registro de Windows"""
        try:
            # PowerShell para leer el registro
            ps_command = """
            $officePaths = @(
                'HKLM:\\SOFTWARE\\Microsoft\\Office\\ClickToRun\\Configuration',
                'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Office\\ClickToRun\\Configuration',
                'HKLM:\\SOFTWARE\\Microsoft\\Office\\16.0\\Common\\InstallRoot',
                'HKLM:\\SOFTWARE\\Microsoft\\Office\\15.0\\Common\\InstallRoot',
                'HKLM:\\SOFTWARE\\Microsoft\\Office\\14.0\\Common\\InstallRoot'
            )
            
            foreach ($path in $officePaths) {
                if (Test-Path $path) {
                    $props = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
                    if ($props) {
                        [PSCustomObject]@{
                            VersionToReport = $props.VersionToReport
                            ProductReleaseIds = $props.ProductReleaseIds
                            Platform = $props.Platform
                            ClientFolder = $props.ClientFolder
                            UpdateChannel = $props.UpdateChannel
                            Path = $path
                        } | ConvertTo-Json
                        break
                    }
                }
            }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                office_data = json.loads(result.stdout)
                
                version = office_data.get('VersionToReport', '')
                product_ids = office_data.get('ProductReleaseIds', '')
                platform = office_data.get('Platform', '')
                
                # Determinar la versión de Office
                office_version = self._parse_office_version(version, product_ids)
                
                return {
                    'office_version': office_version,
                    'office_build': version,
                    'office_edition': self._parse_office_edition(product_ids),
                    'office_architecture': platform if platform else 'Unknown',
                    'update_channel': office_data.get('UpdateChannel', 'Unknown')
                }
        
        except Exception as e:
            self.logger.debug(f"Error detectando Office por registro: {e}")
        
        return None
    
    def _detect_office_by_path_windows(self) -> Optional[Dict]:
        """Detecta Office buscando ejecutables en rutas comunes"""
        common_paths = [
            r"C:\Program Files\Microsoft Office",
            r"C:\Program Files (x86)\Microsoft Office",
            r"C:\Program Files\Microsoft Office 16",
            r"C:\Program Files (x86)\Microsoft Office 16",
            r"C:\Program Files\Microsoft Office\root\Office16",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16"
        ]
        
        for path in common_paths:
            try:
                # Buscar WINWORD.EXE
                word_path = f"{path}\\WINWORD.EXE"
                result = subprocess.run(
                    ["powershell", "-Command", f"Test-Path '{word_path}'"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and 'True' in result.stdout:
                    # Obtener versión del ejecutable
                    version_cmd = f"(Get-Item '{word_path}').VersionInfo.FileVersion"
                    version_result = subprocess.run(
                        ["powershell", "-Command", version_cmd],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if version_result.returncode == 0:
                        version = version_result.stdout.strip()
                        return {
                            'office_version': self._parse_office_version(version, ''),
                            'office_build': version,
                            'installation_path': path
                        }
            
            except Exception:
                continue
        
        return None
    
    def _get_office_license_windows(self) -> Optional[Dict]:
        """Obtiene información de licencia de Office en Windows"""
        try:
            # Usar ospp.vbs para obtener info de licencia
            ps_command = """
            $officePath = 'C:\\Program Files\\Microsoft Office\\Office16'
            if (-not (Test-Path $officePath)) {
                $officePath = 'C:\\Program Files (x86)\\Microsoft Office\\Office16'
            }
            
            if (Test-Path $officePath) {
                $osppPath = Join-Path $officePath 'ospp.vbs'
                if (Test-Path $osppPath) {
                    cscript //Nologo $osppPath /dstatus
                }
            }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout:
                output = result.stdout
                
                # Parsear la salida
                license_type = 'Unknown'
                license_status = 'Unknown'
                product_key = None
                
                if 'RETAIL' in output.upper():
                    license_type = 'Retail'
                elif 'VOLUME' in output.upper() or 'VL_' in output.upper():
                    license_type = 'Volume'
                elif 'SUBSCRIPTION' in output.upper() or 'O365' in output.upper():
                    license_type = 'Subscription'
                
                if 'LICENSED' in output.upper():
                    license_status = 'Licensed'
                elif 'GRACE' in output.upper():
                    license_status = 'Grace Period'
                elif 'UNLICENSED' in output.upper():
                    license_status = 'Unlicensed'
                elif 'NOTIFICATION' in output.upper():
                    license_status = 'Notification'
                
                # Buscar últimos 5 dígitos del product key
                key_match = re.search(r'Last 5 characters of installed product key:\s*([A-Z0-9]{5})', output)
                if key_match:
                    product_key = key_match.group(1)
                
                return {
                    'license_type': license_type,
                    'license_status': license_status,
                    'product_key_last5': product_key
                }
        
        except Exception as e:
            self.logger.debug(f"Error obteniendo licencia de Office: {e}")
        
        return None
    
    def _detect_office_apps_windows(self) -> List[str]:
        """Detecta qué aplicaciones de Office están instaladas"""
        apps = []
        
        office_apps = {
            'WINWORD.EXE': 'Word',
            'EXCEL.EXE': 'Excel',
            'POWERPNT.EXE': 'PowerPoint',
            'OUTLOOK.EXE': 'Outlook',
            'MSACCESS.EXE': 'Access',
            'MSPUB.EXE': 'Publisher',
            'ONENOTE.EXE': 'OneNote',
            'TEAMS.EXE': 'Teams'
        }
        
        base_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16"
        ]
        
        for base_path in base_paths:
            for exe, app_name in office_apps.items():
                try:
                    full_path = f"{base_path}\\{exe}"
                    result = subprocess.run(
                        ["powershell", "-Command", f"Test-Path '{full_path}'"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    
                    if result.returncode == 0 and 'True' in result.stdout:
                        if app_name not in apps:
                            apps.append(app_name)
                
                except Exception:
                    continue
        
        return apps
    
    def _collect_macos(self) -> Dict:
        """Recopila información de Office en macOS"""
        data = {
            'office_installed': False,
            'office_version': None,
            'office_edition': None,
            'office_build': None,
            'license_type': None,
            'installed_apps': []
        }
        
        try:
            # Buscar Office en /Applications
            office_apps_paths = {
                'Word': '/Applications/Microsoft Word.app',
                'Excel': '/Applications/Microsoft Excel.app',
                'PowerPoint': '/Applications/Microsoft PowerPoint.app',
                'Outlook': '/Applications/Microsoft Outlook.app',
                'OneNote': '/Applications/Microsoft OneNote.app'
            }
            
            installed_apps = []
            office_version = None
            
            for app_name, app_path in office_apps_paths.items():
                try:
                    # Verificar si existe
                    result = subprocess.run(
                        ["test", "-d", app_path],
                        capture_output=True,
                        timeout=3
                    )
                    
                    if result.returncode == 0:
                        installed_apps.append(app_name)
                        
                        # Obtener versión de la primera app encontrada
                        if not office_version:
                            version_result = subprocess.run(
                                ["defaults", "read", f"{app_path}/Contents/Info.plist", "CFBundleShortVersionString"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            
                            if version_result.returncode == 0:
                                office_version = version_result.stdout.strip()
                
                except Exception:
                    continue
            
            if installed_apps:
                data['office_installed'] = True
                data['office_version'] = office_version
                data['installed_apps'] = installed_apps
                data['office_edition'] = 'Microsoft 365' if office_version and '16.' in office_version else 'Unknown'
                
                # Intentar detectar tipo de licencia
                license_type = self._detect_office_license_macos()
                if license_type:
                    data['license_type'] = license_type
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de Office macOS: {e}")
            data['error'] = str(e)
        
        return data
    
    def _detect_office_license_macos(self) -> Optional[str]:
        """Detecta el tipo de licencia de Office en macOS"""
        try:
            # Buscar archivos de licencia de Office
            license_paths = [
                '/Library/Preferences/com.microsoft.office.licensingV2.plist',
                '~/Library/Group Containers/UBF8T346G9.Office/com.microsoft.Office365.plist'
            ]
            
            for license_path in license_paths:
                try:
                    result = subprocess.run(
                        ["test", "-f", license_path],
                        capture_output=True,
                        timeout=3
                    )
                    
                    if result.returncode == 0:
                        # Si existe el archivo de Microsoft 365
                        if 'Office365' in license_path:
                            return 'Subscription'
                        else:
                            return 'Retail'
                
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.debug(f"Error detectando licencia macOS: {e}")
        
        return None
    
    def _collect_linux(self) -> Dict:
        """Recopila información de Office en Linux"""
        data = {
            'office_installed': False,
            'office_version': None,
            'office_type': None,
            'installed_apps': []
        }
        
        try:
            # En Linux, es más común LibreOffice u OnlyOffice
            # Pero verificamos si hay Office 365 web o alguna instalación especial
            
            # Verificar LibreOffice
            libreoffice_info = self._detect_libreoffice()
            if libreoffice_info:
                data.update(libreoffice_info)
                data['office_installed'] = True
                data['office_type'] = 'LibreOffice'
            
            # Verificar OnlyOffice
            if not data['office_installed']:
                onlyoffice_info = self._detect_onlyoffice()
                if onlyoffice_info:
                    data.update(onlyoffice_info)
                    data['office_installed'] = True
                    data['office_type'] = 'OnlyOffice'
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de Office Linux: {e}")
            data['error'] = str(e)
        
        return data
    
    def _detect_libreoffice(self) -> Optional[Dict]:
        """Detecta LibreOffice en Linux"""
        if self._command_exists('libreoffice'):
            try:
                result = subprocess.run(
                    ['libreoffice', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version_match = re.search(r'LibreOffice\s+([\d.]+)', result.stdout)
                    version = version_match.group(1) if version_match else 'Unknown'
                    
                    # Detectar componentes instalados
                    apps = []
                    components = ['writer', 'calc', 'impress', 'draw', 'base']
                    for comp in components:
                        if self._command_exists(f'lo{comp}') or self._command_exists(f'libreoffice --{comp}'):
                            apps.append(comp.capitalize())
                    
                    return {
                        'office_version': version,
                        'installed_apps': apps if apps else ['LibreOffice Suite']
                    }
            
            except Exception:
                pass
        
        return None
    
    def _detect_onlyoffice(self) -> Optional[Dict]:
        """Detecta OnlyOffice en Linux"""
        if self._command_exists('onlyoffice-desktopeditors'):
            try:
                result = subprocess.run(
                    ['onlyoffice-desktopeditors', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version_match = re.search(r'([\d.]+)', result.stdout)
                    version = version_match.group(1) if version_match else 'Unknown'
                    
                    return {
                        'office_version': version,
                        'installed_apps': ['OnlyOffice Suite']
                    }
            
            except Exception:
                pass
        
        return None
    
    def _parse_office_version(self, version_string: str, product_ids: str) -> str:
        """Determina la versión legible de Office"""
        if not version_string:
            return 'Unknown'
        
        # Determinar versión mayor
        if version_string.startswith('16.'):
            # Office 2016, 2019, 2021, o Microsoft 365
            if 'O365' in product_ids or 'M365' in product_ids:
                return 'Microsoft 365'
            elif '2021' in product_ids:
                return 'Office 2021'
            elif '2019' in product_ids:
                return 'Office 2019'
            else:
                return 'Office 2016'
        elif version_string.startswith('15.'):
            return 'Office 2013'
        elif version_string.startswith('14.'):
            return 'Office 2010'
        else:
            return f'Office (Build {version_string})'
    
    def _parse_office_edition(self, product_ids: str) -> str:
        """Determina la edición de Office"""
        if not product_ids:
            return 'Unknown'
        
        product_ids_upper = product_ids.upper()
        
        if 'PROPLUS' in product_ids_upper:
            return 'Professional Plus'
        elif 'STANDARD' in product_ids_upper:
            return 'Standard'
        elif 'PROFESSIONAL' in product_ids_upper:
            return 'Professional'
        elif 'HOMEANDSTUDENT' in product_ids_upper or 'HOMEBUSINESS' in product_ids_upper:
            return 'Home and Business'
        elif 'O365' in product_ids_upper or 'M365' in product_ids_upper:
            return 'Microsoft 365'
        else:
            return 'Unknown'
    
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
            'office_installed': False,
            'office_version': None,
            'office_edition': None,
            'installed_apps': [],
            'error': 'Collector failed'
        }