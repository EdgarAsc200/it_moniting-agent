"""
Antivirus Collector - Detección multiplataforma de software antivirus
Soporta: Windows, macOS, Linux
"""

import os
import platform
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

# Para Windows
try:
    import winreg
except ImportError:
    winreg = None  # No disponible en macOS/Linux


class AntivirusCollector:
    """Recolector de información de antivirus multiplataforma"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.logger = None  # Si tienes logging, asigna aquí
    def collect(self) -> Dict:
        """
        Método de interfaz unificada para compatibilidad con otros collectors
        Llama internamente a collect_antivirus_info()
        """
        
        try:
            result = self.collect_antivirus_info()
            return result
        except Exception as e:
            print(f"❌ Error en collect(): {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'antivirus_name': 'Error',
                'antivirus_version': None,
                'protection_status': 'unknown',
                'last_update': None,
                'last_scan': None,
                'firewall_status': 'unknown',
                'real_time_protection': False,
                'definitions_up_to_date': False,
                'engine_version': None,
                'third_party_antivirus': [],
                'error': str(e),
                'os_type': self.os_type
            }
    def collect_antivirus_info(self) -> Dict:
        """
        Recopila información del antivirus según el sistema operativo
        
        Returns:
            dict: Información del antivirus detectado
        """
        
        antivirus_info = {
            'antivirus_name': 'Unknown',
            'antivirus_version': None,
            'protection_status': 'unknown',
            'last_update': None,
            'last_scan': None,
            'firewall_status': 'unknown',
            'real_time_protection': False,
            'definitions_up_to_date': False,
            'engine_version': None,
            'third_party_antivirus': [],
            'detection_method': None,
            'os_type': self.os_type
        }
        
        try:
            if self.os_type == "Windows":
                return self._collect_windows_antivirus(antivirus_info)
            
            elif self.os_type == "Darwin":  # macOS
                return self._collect_macos_antivirus(antivirus_info)
            
            elif self.os_type == "Linux":
                return self._collect_linux_antivirus(antivirus_info)
            
            else:
                antivirus_info['antivirus_name'] = f'Unsupported OS: {self.os_type}'
                return antivirus_info
        
        except Exception as e:
            print(f"❌ Error recopilando info de antivirus: {e}")
            import traceback
            traceback.print_exc()
            antivirus_info['antivirus_name'] = 'Error during detection'
            antivirus_info['error'] = str(e)
            return antivirus_info
    
    # ═══════════════════════════════════════════════════════════
    # WINDOWS - WMI SecurityCenter2
    # ═══════════════════════════════════════════════════════════
    
    def _collect_windows_antivirus(self, antivirus_info: Dict) -> Dict:
        """Recopila información de antivirus en Windows usando WMI"""
        
        try:
            import wmi
        except ImportError:
            print("⚠️  Librería WMI no disponible")
            antivirus_info['antivirus_name'] = 'WMI not available'
            antivirus_info['detection_method'] = 'WMI (not installed)'
            return antivirus_info
        
        try:
            c = wmi.WMI(namespace="root/SecurityCenter2")
            antivirus_info['detection_method'] = 'WMI SecurityCenter2'
            
            antivirus_products = []
            
            # Obtener todos los productos antivirus instalados
            for av in c.AntiVirusProduct():
                product_info = {
                    'name': av.displayName,
                    'state': av.productState,
                    'path': av.pathToSignedProductExe if hasattr(av, 'pathToSignedProductExe') else None,
                    'guid': av.instanceGuid
                }
                antivirus_products.append(product_info)
            
            print(f"\n🛡️  Antivirus detectados: {len(antivirus_products)}")
            for av in antivirus_products:
                print(f"   - {av['name']}")
            
            # Separar Windows Defender de antivirus de terceros
            windows_defender = None
            third_party_list = []
            primary_antivirus = None
            
            for av_product in antivirus_products:
                name = av_product['name']
                
                if 'Windows Defender' in name or 'Microsoft Defender' in name:
                    windows_defender = av_product
                else:
                    third_party_list.append(name)
                    if primary_antivirus is None:  # El primero que encontremos
                        primary_antivirus = av_product
            
            # PRIORIDAD: Si hay antivirus de terceros, usar ese
            if primary_antivirus:
                print(f"✅ Usando antivirus principal: {primary_antivirus['name']}")
                active_antivirus = primary_antivirus
                antivirus_info['third_party_antivirus'] = third_party_list
            elif windows_defender:
                print(f"✅ Usando Windows Defender (no hay terceros)")
                active_antivirus = windows_defender
                antivirus_info['third_party_antivirus'] = []
            else:
                print(f"⚠️  No se detectaron productos antivirus")
                active_antivirus = None
                        
            # Extraer información del antivirus activo
            if active_antivirus:
                antivirus_info['antivirus_name'] = active_antivirus['name']
                
                # Decodificar productState
                product_state = active_antivirus['state']
                state_info = self._decode_antivirus_state(product_state)
                
                antivirus_info['protection_status'] = state_info['protection_status']
                antivirus_info['real_time_protection'] = state_info['real_time_protection']
                antivirus_info['definitions_up_to_date'] = state_info['definitions_up_to_date']
                
                print(f"   Estado: {antivirus_info['protection_status']}")
                print(f"   Protección en tiempo real: {antivirus_info['real_time_protection']}")
                print(f"   Definiciones actualizadas: {antivirus_info['definitions_up_to_date']}")
                
                # ✅ NUEVO: Obtener last_scan y last_update según el tipo de antivirus
                av_name = active_antivirus['name']
                
                # Intentar obtener información específica por antivirus
                scan_info = None
                
                if 'Windows Defender' in av_name or 'Microsoft Defender' in av_name:
                    scan_info = self._get_windows_defender_scan_info()
                
                elif 'ESET' in av_name:
                    scan_info = self._get_eset_scan_info()
                
                elif 'Norton' in av_name or 'Symantec' in av_name:
                    scan_info = self._get_norton_scan_info()
                
                elif 'Avast' in av_name:
                    scan_info = self._get_avast_scan_info()
                
                elif 'AVG' in av_name:
                    scan_info = self._get_avg_scan_info()
                
                elif 'Kaspersky' in av_name:
                    scan_info = self._get_kaspersky_scan_info()
                
                elif 'McAfee' in av_name:
                    scan_info = self._get_mcafee_scan_info()
                
                elif 'Bitdefender' in av_name:
                    scan_info = self._get_bitdefender_scan_info()
                
                else:
                    # Método genérico para otros antivirus
                    scan_info = self._get_generic_antivirus_scan_info(active_antivirus)
                
                if scan_info:
                    if scan_info.get('last_scan'):
                        antivirus_info['last_scan'] = scan_info['last_scan']
                    if scan_info.get('last_update'):
                        antivirus_info['last_update'] = scan_info['last_update']
            
            # Obtener información de firewall
            try:
                firewall_detected = False
                for fw in c.FirewallProduct():
                    if fw.displayName:
                        antivirus_info['firewall_status'] = 'active'
                        firewall_detected = True
                        break
                
                if not firewall_detected:
                    antivirus_info['firewall_status'] = 'inactive'
            except:
                antivirus_info['firewall_status'] = 'unknown'
            
            # Intentar obtener versión desde Win32_Product
            try:
                c2 = wmi.WMI()
                for product in c2.Win32_Product():
                    if antivirus_info['antivirus_name'] in product.Name:
                        antivirus_info['antivirus_version'] = product.Version
                        print(f"   Versión: {antivirus_info['antivirus_version']}")
                        break
            except:
                pass
        
        except Exception as e:
            print(f"❌ Error en detección Windows: {e}")
            antivirus_info['error'] = str(e)
        
        return antivirus_info
    def _get_windows_defender_scan_info(self) -> Optional[Dict]:
        """
        Obtiene información de escaneo de Windows Defender usando PowerShell
        
        Returns:
            dict: Información de último escaneo y actualización, o None si falla
        """
        try:
            # Ejecutar PowerShell para obtener información de Windows Defender
            powershell_cmd = [
                'powershell',
                '-NoProfile',
                '-Command',
                'Get-MpComputerStatus | Select-Object AntivirusSignatureLastUpdated, FullScanEndTime, QuickScanEndTime | ConvertTo-Json'
            ]
            
            result = subprocess.run(
                powershell_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                import json
                data = json.loads(result.stdout)
                
                scan_info = {}
                
                # Última actualización de definiciones
                if data.get('AntivirusSignatureLastUpdated'):
                    scan_info['last_update'] = data['AntivirusSignatureLastUpdated']
                    print(f"   Última actualización: {scan_info['last_update']}")
                
                # Último escaneo (usar el más reciente entre completo y rápido)
                full_scan = data.get('FullScanEndTime')
                quick_scan = data.get('QuickScanEndTime')
                
                if full_scan and quick_scan:
                    # Comparar y usar el más reciente
                    scan_info['last_scan'] = max(full_scan, quick_scan)
                elif full_scan:
                    scan_info['last_scan'] = full_scan
                elif quick_scan:
                    scan_info['last_scan'] = quick_scan
                
                if scan_info.get('last_scan'):
                    print(f"   Último escaneo: {scan_info['last_scan']}")
                
                return scan_info
        
        except Exception as e:
            print(f"   ⚠️  No se pudo obtener info de escaneo de Defender: {e}")
            return None
    

# ═══════════════════════════════════════════════════════════
# MÉTODOS ESPECÍFICOS POR ANTIVIRUS - WINDOWS
# ═══════════════════════════════════════════════════════════

    def _get_eset_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de ESET"""
        try:
            scan_info = {}
            
            # ESET guarda información en el registro
            import winreg
            
            try:
                # Intentar leer del registro de ESET
                key_path = r"SOFTWARE\ESET\ESET Security\CurrentVersion\Info"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
                
                try:
                    # Última actualización de definiciones
                    scan_date, _ = winreg.QueryValueEx(key, "ScannerVersion")
                    scan_info['last_update'] = scan_date
                    print(f"   Última actualización ESET: {scan_date}")
                except:
                    pass
                
                winreg.CloseKey(key)
            except:
                pass
            
            # Intentar leer archivos de log de ESET
            log_paths = [
                r"C:\ProgramData\ESET\ESET Security\Logs\virlog.dat",
                r"C:\ProgramData\ESET\ESET NOD32 Antivirus\Logs\virlog.dat"
            ]
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    try:
                        # Obtener fecha de modificación del archivo de log
                        mod_time = os.path.getmtime(log_path)
                        last_scan = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_scan'] = last_scan
                        print(f"   Último escaneo ESET: {last_scan}")
                        break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de ESET: {e}")
            return None


    def _get_norton_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de Norton"""
        try:
            scan_info = {}
            
            # Norton guarda logs en ProgramData
            log_paths = [
                r"C:\ProgramData\Norton\{0C55C096-0F1D-4F28-AAA2-85EF591126E7}\NIS_22.0.0.110\Logs",
                r"C:\ProgramData\Symantec\Symantec Endpoint Protection\CurrentVersion\Data\Logs"
            ]
            
            for log_dir in log_paths:
                if os.path.exists(log_dir):
                    try:
                        # Buscar el archivo de log más reciente
                        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
                        if log_files:
                            latest_log = max([os.path.join(log_dir, f) for f in log_files], 
                                        key=os.path.getmtime)
                            mod_time = os.path.getmtime(latest_log)
                            last_scan = datetime.fromtimestamp(mod_time).isoformat()
                            scan_info['last_scan'] = last_scan
                            print(f"   Último escaneo Norton: {last_scan}")
                            break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Norton: {e}")
            return None


    def _get_avast_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de Avast"""
        try:
            scan_info = {}
            
            # Avast guarda información en ProgramData
            log_path = r"C:\ProgramData\AVAST Software\Avast\report\FileSystemShield.txt"
            
            if os.path.exists(log_path):
                try:
                    mod_time = os.path.getmtime(log_path)
                    last_update = datetime.fromtimestamp(mod_time).isoformat()
                    scan_info['last_update'] = last_update
                    print(f"   Última actualización Avast: {last_update}")
                except:
                    pass
            
            # Buscar archivo de base de datos de virus
            db_path = r"C:\ProgramData\AVAST Software\Avast\defs"
            if os.path.exists(db_path):
                try:
                    mod_time = os.path.getmtime(db_path)
                    last_update = datetime.fromtimestamp(mod_time).isoformat()
                    scan_info['last_update'] = last_update
                except:
                    pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Avast: {e}")
            return None


    def _get_avg_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de AVG"""
        try:
            scan_info = {}
            
            # AVG es similar a Avast
            db_path = r"C:\ProgramData\AVG\Antivirus\defs"
            
            if os.path.exists(db_path):
                try:
                    mod_time = os.path.getmtime(db_path)
                    last_update = datetime.fromtimestamp(mod_time).isoformat()
                    scan_info['last_update'] = last_update
                    print(f"   Última actualización AVG: {last_update}")
                except:
                    pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de AVG: {e}")
            return None


    def _get_kaspersky_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de Kaspersky"""
        try:
            scan_info = {}
            
            # Kaspersky guarda información en ProgramData
            log_paths = [
                r"C:\ProgramData\Kaspersky Lab\AVP21.3\Data\Updater\UpdateInfo.txt",
                r"C:\ProgramData\Kaspersky Lab\KES\Data\Bases"
            ]
            
            for path in log_paths:
                if os.path.exists(path):
                    try:
                        mod_time = os.path.getmtime(path)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = last_update
                        print(f"   Última actualización Kaspersky: {last_update}")
                        break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Kaspersky: {e}")
            return None


    def _get_mcafee_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de McAfee"""
        try:
            scan_info = {}
            
            # McAfee guarda logs en ProgramData
            log_path = r"C:\ProgramData\McAfee\DesktopProtection"
            
            if os.path.exists(log_path):
                try:
                    mod_time = os.path.getmtime(log_path)
                    last_update = datetime.fromtimestamp(mod_time).isoformat()
                    scan_info['last_update'] = last_update
                    print(f"   Última actualización McAfee: {last_update}")
                except:
                    pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de McAfee: {e}")
            return None


    def _get_bitdefender_scan_info(self) -> Optional[Dict]:
        """Obtiene información de escaneo de Bitdefender"""
        try:
            scan_info = {}
            
            # Bitdefender guarda información en ProgramData
            log_paths = [
                r"C:\ProgramData\Bitdefender\Desktop\Profiles\Logs",
                r"C:\Program Files\Bitdefender\Bitdefender Security\Antivirus_##########\Profiles\Logs"
            ]
            
            for log_dir in log_paths:
                if os.path.exists(log_dir):
                    try:
                        mod_time = os.path.getmtime(log_dir)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = last_update
                        print(f"   Última actualización Bitdefender: {last_update}")
                        break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Bitdefender: {e}")
            return None


    def _get_generic_antivirus_scan_info(self, av_product: Dict) -> Optional[Dict]:
        """
        Método genérico para obtener información de antivirus desconocidos
        Usa la ruta del ejecutable para buscar archivos relacionados
        """
        try:
            scan_info = {}
            
            if not av_product.get('path'):
                return None
            
            # Obtener el directorio del antivirus
            av_dir = os.path.dirname(av_product['path'])
            
            # Buscar carpetas comunes de logs/datos
            search_dirs = []
            
            # Buscar en el directorio del programa
            if os.path.exists(av_dir):
                search_dirs.append(av_dir)
                parent_dir = os.path.dirname(av_dir)
                search_dirs.append(parent_dir)
            
            # Buscar en ProgramData
            av_name = av_product['name'].split()[0]  # Primera palabra del nombre
            programdata_path = os.path.join(r"C:\ProgramData", av_name)
            if os.path.exists(programdata_path):
                search_dirs.append(programdata_path)
            
            # Buscar archivos de definiciones o logs
            for search_dir in search_dirs:
                try:
                    for root, dirs, files in os.walk(search_dir):
                        # Buscar carpetas con nombres como: defs, definitions, signatures, updates
                        for dirname in dirs:
                            if any(keyword in dirname.lower() for keyword in ['def', 'sig', 'update', 'virus']):
                                def_path = os.path.join(root, dirname)
                                try:
                                    mod_time = os.path.getmtime(def_path)
                                    last_update = datetime.fromtimestamp(mod_time).isoformat()
                                    scan_info['last_update'] = last_update
                                    print(f"   Última actualización (genérico): {last_update}")
                                    return scan_info
                                except:
                                    pass
                        
                        # Limitar la profundidad de búsqueda
                        if root.count(os.sep) - search_dir.count(os.sep) > 2:
                            break
                except:
                    pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error en detección genérica: {e}")
            return None





    
    # ═══════════════════════════════════════════════════════════
    # macOS - Procesos y Aplicaciones
    # ═══════════════════════════════════════════════════════════
    
    def _collect_macos_antivirus(self, antivirus_info: Dict) -> Dict:
        """Recopila información de antivirus en macOS"""
        
        antivirus_info['detection_method'] = 'Process and Application scanning'
        
        # ← AQUÍ SE INICIALIZA LA LISTA
        detected = []
        
        # ═══════════════════════════════════════════════════════════
        # MÉTODO 1: VERIFICAR APLICACIONES INSTALADAS (MÁS CONFIABLE)
        # ═══════════════════════════════════════════════════════════
        
        # Lista de aplicaciones específicas de antivirus
        known_apps = {
            'ESET Cyber Security.app': ('ESET Cyber Security', 'ESET'),
            'ESET Endpoint Antivirus.app': ('ESET Endpoint Antivirus', 'ESET'),
            'Malwarebytes.app': ('Malwarebytes', 'Malwarebytes'),
            'Avast Security.app': ('Avast Security', 'Avast Software'),
            'AVG AntiVirus.app': ('AVG Antivirus', 'AVG Technologies'),
            'Bitdefender Antivirus.app': ('Bitdefender Antivirus', 'Bitdefender'),
            'Sophos Home.app': ('Sophos Home', 'Sophos'),
            'Kaspersky Internet Security.app': ('Kaspersky Internet Security', 'Kaspersky'),
            'Norton 360.app': ('Norton 360', 'NortonLifeLock'),
            'F-Secure SAFE.app': ('F-Secure', 'F-Secure'),
            'Intego Mac Internet Security.app': ('Intego VirusBarrier', 'Intego'),
            'VirusBarrier X9.app': ('Intego VirusBarrier', 'Intego'),
            'Webroot SecureAnywhere.app': ('Webroot SecureAnywhere', 'Webroot'),
        }
        
        app_paths = ['/Applications', os.path.expanduser('~/Applications')]
    
        
        for app_path in app_paths:
            if os.path.exists(app_path):
                try:
                    apps = os.listdir(app_path)
                    
                    for app_name, (full_name, vendor) in known_apps.items():
                        if app_name in apps:
                            full_path = os.path.join(app_path, app_name)
                            
                            # Verificar que sea una aplicación real (no solo una carpeta)
                            if os.path.isdir(full_path) and full_path.endswith('.app'):
                                detected.append({
                                    'name': full_name,
                                    'vendor': vendor,
                                    'detection_method': 'Installed application',
                                    'app_path': full_path,
                                    'is_builtin': False
                                })
                                print(f"   ✅ Aplicación encontrada: {app_name}")
                except Exception as e:
                    print(f"⚠️  Error verificando {app_path}: {e}")
        
        # ═══════════════════════════════════════════════════════════
        # MÉTODO 2: VERIFICAR PROCESOS (SOLO SI LA APP EXISTE)
        # ═══════════════════════════════════════════════════════════
        
        # Solo verificar procesos si ya detectamos alguna aplicación
        if detected:
            print("\n🔍 Verificando procesos en ejecución...")
            
            process_patterns = {
                'esets_daemon': 'ESET Cyber Security',
                'esets_gui': 'ESET Cyber Security',
                'MalwarebytesDaemon': 'Malwarebytes',
                'AvastSecurityAgent': 'Avast Security',
                'com.avast.daemon': 'Avast Security',
                'AVGAgent': 'AVG Antivirus',
                'SophosScanD': 'Sophos Home',
                'sophossxld': 'Sophos Home',
                'KasperskyAV': 'Kaspersky Internet Security',
            }
            
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                processes = result.stdout
                
                # Marcar qué antivirus están corriendo
                for av in detected:
                    for process_pattern, av_name in process_patterns.items():
                        if av['name'] == av_name and process_pattern in processes:
                            av['is_running'] = True
                            print(f"   ✅ Proceso activo detectado: {process_pattern} → {av_name}")
                            break
            except Exception as e:
                print(f"⚠️  Error verificando procesos: {e}")
        
        # ═══════════════════════════════════════════════════════════
        # XPROTECT (NATIVO DE macOS) - MEJORADO
        # ═══════════════════════════════════════════════════════════
        
        
        
        xprotect_detected = False
        xprotect_path = None
        
        # Posibles ubicaciones de XProtect según versión de macOS
        xprotect_locations = [
            '/System/Library/CoreServices/XProtect.bundle',
            '/Library/Apple/System/Library/CoreServices/XProtect.bundle',
            '/System/Library/CoreServices/XProtect.app',
        ]
        
        for location in xprotect_locations:
            if os.path.exists(location):
                xprotect_detected = True
                xprotect_path = location
                break
        
        # Si no encontramos XProtect por path, verificar si existe el proceso
        if not xprotect_detected:
            try:
                # XProtect siempre está integrado en macOS, verificar con system_profiler
                result = subprocess.run(
                    ['system_profiler', 'SPSoftwareDataType'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if 'System Integrity Protection' in result.stdout or 'macOS' in result.stdout:
                    # Si el sistema responde, XProtect está presente (está integrado en macOS 10.6+)
                    xprotect_detected = True
                    xprotect_path = '/System/Library/CoreServices/XProtect.bundle'  # Path por defecto
                    
            except:
                pass
        
        # XProtect está presente en todas las versiones modernas de macOS
        # Si llegamos aquí y no lo detectamos, asumimos que existe de todas formas
        if not xprotect_detected:
            # En macOS 10.6 y superior, XProtect está siempre presente
            import platform as plat
            macos_version = plat.mac_ver()[0]
            
            try:
                major_version = int(macos_version.split('.')[0]) if macos_version else 0
                
                # macOS 10.6+ (Snow Leopard) tiene XProtect
                if major_version >= 10 or macos_version.startswith('11') or macos_version.startswith('12') or macos_version.startswith('13') or macos_version.startswith('14') or macos_version.startswith('15'):
                    xprotect_detected = True
                    xprotect_path = '/System/Library/CoreServices/XProtect.bundle'
                    print(f"   ✅ XProtect asumido (macOS {macos_version} incluye XProtect por defecto)")
            except:
                pass
        
        if xprotect_detected:
            detected.append({
                'name': 'XProtect',
                'vendor': 'Apple',
                'detection_method': 'Built-in macOS protection',
                'app_path': xprotect_path,
                'is_builtin': True
            })
        else:
            print(f"   ⚠️  XProtect no detectado (inusual en macOS moderno)")
        
        # ═══════════════════════════════════════════════════════════
        # RESUMEN DE DETECCIÓN
        # ═══════════════════════════════════════════════════════════
        
        print(f"\n{'='*70}")
        print(f"🛡️  ANTIVIRUS DETECTADOS EN macOS: {len(detected)}")
        print(f"{'='*70}")
        
        if detected:
            for av in detected:
                builtin_tag = " [NATIVO]" if av.get('is_builtin') else " [TERCEROS]"
                running_tag = " 🟢 ACTIVO" if av.get('is_running') else ""
                print(f"   - {av['name']} ({av.get('vendor', 'Unknown')}){builtin_tag}{running_tag}")
        else:
            print(f"   ⚠️  No se detectaron productos antivirus")
        
        print(f"{'='*70}\n")
        
        # ═══════════════════════════════════════════════════════════
        # DETERMINAR ANTIVIRUS PRINCIPAL
        # ═══════════════════════════════════════════════════════════
        
        third_party = [av for av in detected if not av.get('is_builtin', False)]
        
        if third_party:
            # Usar el primer antivirus de terceros
            primary_av = third_party[0]
            antivirus_info['antivirus_name'] = primary_av['name']
            antivirus_info['antivirus_version'] = primary_av.get('version', None)
            antivirus_info['third_party_antivirus'] = [av['name'] for av in third_party]
            
            # Estado basado en si está corriendo
            if primary_av.get('is_running'):
                antivirus_info['protection_status'] = 'active'
                antivirus_info['real_time_protection'] = True
            else:
                # Está instalado pero no sabemos si está corriendo
                antivirus_info['protection_status'] = 'installed'
                antivirus_info['real_time_protection'] = False
            
            print(f"✅ Usando antivirus principal: {primary_av['name']}")
            print(f"   Estado: {antivirus_info['protection_status']}")
            print(f"   Protección en tiempo real: {antivirus_info['real_time_protection']}")
            
            # Obtener información de escaneo según el antivirus
            av_name = primary_av['name']
            scan_info = None
            
            if 'ESET' in av_name:
                scan_info = self._get_eset_macos_info()
            elif 'Malwarebytes' in av_name:
                scan_info = self._get_malwarebytes_macos_info()
            elif 'Sophos' in av_name:
                scan_info = self._get_sophos_macos_info()
            elif 'Avast' in av_name or 'AVG' in av_name:
                scan_info = self._get_avast_macos_info()
            else:
                scan_info = self._get_generic_macos_antivirus_info(primary_av)
            
            if scan_info:
                if scan_info.get('last_scan'):
                    antivirus_info['last_scan'] = scan_info['last_scan']
                if scan_info.get('last_update'):
                    antivirus_info['last_update'] = scan_info['last_update']
                if scan_info.get('definitions_up_to_date') is not None:
                    antivirus_info['definitions_up_to_date'] = scan_info['definitions_up_to_date']
        
        elif xprotect_detected:
            # Solo XProtect (nativo)
            antivirus_info['antivirus_name'] = 'XProtect'
            antivirus_info['protection_status'] = 'active'
            antivirus_info['real_time_protection'] = True
            antivirus_info['third_party_antivirus'] = []
            
            
            
            # Obtener información de XProtect
            xprotect_info = self._get_xprotect_info()
            if xprotect_info:
                antivirus_info['last_update'] = xprotect_info.get('last_update')
                if xprotect_info.get('definitions_up_to_date') is not None:
                    antivirus_info['definitions_up_to_date'] = xprotect_info['definitions_up_to_date'] 
        
        else:
            # No se detectó nada (muy raro en macOS)
            antivirus_info['antivirus_name'] = 'XProtect (default)'
            antivirus_info['protection_status'] = 'active'
            antivirus_info['real_time_protection'] = True
            antivirus_info['third_party_antivirus'] = []
            
            print(f"⚠️  No se detectaron antivirus, usando XProtect por defecto (presente en macOS)")
        
        # ═══════════════════════════════════════════════════════════
        # FIREWALL DE macOS
        # ═══════════════════════════════════════════════════════════
        
        try:
            result = subprocess.run(
                ['defaults', 'read', '/Library/Preferences/com.apple.alf', 'globalstate'],
                capture_output=True,
                text=True,
                timeout=5
            )
            fw_state = result.stdout.strip()
            antivirus_info['firewall_status'] = 'active' if fw_state != '0' else 'inactive'
        except:
            antivirus_info['firewall_status'] = 'unknown'
        
        return antivirus_info
    
    def _get_xprotect_info(self) -> Optional[Dict]:
        """Obtiene información de XProtect de macOS"""
        try:
            scan_info = {}
            
           
            
            # Posibles ubicaciones del archivo de configuración de XProtect
            xprotect_files = [
                '/System/Library/CoreServices/XProtect.bundle/Contents/Resources/XProtect.meta.plist',
                '/System/Library/CoreServices/XProtect.bundle/Contents/Resources/XProtect.plist',
                '/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/Resources/XProtect.meta.plist',
                '/System/Library/CoreServices/XProtect.app/Contents/Resources/XProtect.plist',
            ]
            
            for plist_path in xprotect_files:
                if os.path.exists(plist_path):
                    try:
                        # Obtener fecha de modificación del archivo
                        mod_time = os.path.getmtime(plist_path)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        
                        scan_info['last_update'] = last_update
                        
                        # Calcular si está actualizado (menos de 30 días para XProtect)
                        days_old = (datetime.now() - datetime.fromtimestamp(mod_time)).days
                        scan_info['definitions_up_to_date'] = days_old < 30
                        
                        
                        return scan_info
                    except Exception as e:
                        print(f"   ⚠️  Error leyendo {plist_path}: {e}")
            
            # Si no encontramos archivos, intentar con softwareupdate
            try:
                print("   🔍 Intentando obtener info con softwareupdate...")
                result = subprocess.run(
                    ['softwareupdate', '--history'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Buscar actualizaciones de XProtect en el historial
                for line in result.stdout.split('\n'):
                    if 'XProtect' in line or 'Security Update' in line:
                        print(f"   📄 {line}")
                        # Intentar extraer fecha
                        # El formato varía, pero típicamente tiene fechas
            except Exception as e:
                print(f"   ⚠️  Error con softwareupdate: {e}")
            
            if not scan_info:
                # Como último recurso, usar una fecha genérica reciente
                print("   ℹ️  No se pudo determinar última actualización exacta")
                print("   ℹ️  XProtect se actualiza automáticamente con macOS")
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ❌ Error obteniendo info de XProtect: {e}")
            return None
    def _get_malwarebytes_macos_info(self) -> Optional[Dict]:
        """Obtiene información de Malwarebytes en macOS"""
        try:
            scan_info = {}
            
            # Malwarebytes guarda información en Library
            log_paths = [
                os.path.expanduser('~/Library/Logs/Malwarebytes'),
                '/Library/Logs/Malwarebytes'
            ]
            
            for log_dir in log_paths:
                if os.path.exists(log_dir):
                    try:
                        mod_time = os.path.getmtime(log_dir)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = last_update
                        print(f"   Última actividad Malwarebytes: {last_update}")
                        break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Malwarebytes: {e}")
            return None


    def _get_eset_macos_info(self) -> Optional[Dict]:
        """Obtiene información de ESET Cyber Security en macOS"""
        try:
            scan_info = {}
            
            print("   🔍 Buscando información de ESET...")
            
            # Ubicaciones donde ESET guarda información en macOS
            eset_paths = [
                '/Library/Application Support/ESET/esets',
                '/Library/Application Support/com.eset.esets',
                os.path.expanduser('~/Library/Application Support/ESET'),
                '/Library/Logs/ESET',
                os.path.expanduser('~/Library/Logs/ESET')
            ]
            
            # Buscar carpeta de logs
            for eset_path in eset_paths:
                if os.path.exists(eset_path):
                    print(f"   📁 Encontrado: {eset_path}")
                    
                    try:
                        # Obtener fecha de modificación
                        mod_time = os.path.getmtime(eset_path)
                        last_activity = datetime.fromtimestamp(mod_time).isoformat()
                        
                        # Si no tenemos last_update aún, usar esta fecha
                        if not scan_info.get('last_update'):
                            scan_info['last_update'] = last_activity
                        
                        # Buscar archivos específicos dentro
                        if os.path.isdir(eset_path):
                            for root, dirs, files in os.walk(eset_path):
                                for file in files:
                                    file_lower = file.lower()
                                    
                                    # Buscar archivos de actualización o escaneo
                                    if any(keyword in file_lower for keyword in ['update', 'scan', 'virus', 'signature']):
                                        file_path = os.path.join(root, file)
                                        try:
                                            file_mod_time = os.path.getmtime(file_path)
                                            file_date = datetime.fromtimestamp(file_mod_time).isoformat()
                                            
                                            if 'scan' in file_lower and not scan_info.get('last_scan'):
                                                scan_info['last_scan'] = file_date
                                            
                                            if 'update' in file_lower or 'signature' in file_lower:
                                                scan_info['last_update'] = file_date
                                        except:
                                            pass
                                
                                # No buscar demasiado profundo
                                if root.count(os.sep) - eset_path.count(os.sep) > 2:
                                    break
                    except Exception as e:
                        print(f"   ⚠️  Error procesando {eset_path}: {e}")
            
            # Buscar base de datos de virus
            virus_db_paths = [
                '/Library/Application Support/ESET/esets/cache/virusdbs',
                '/Library/Application Support/com.eset.esets/cache'
            ]
            
            for db_path in virus_db_paths:
                if os.path.exists(db_path):
                    try:
                        mod_time = os.path.getmtime(db_path)
                        db_date = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = db_date
                        
                        # Verificar si está actualizado (menos de 7 días)
                        days_old = (datetime.now() - datetime.fromtimestamp(mod_time)).days
                        scan_info['definitions_up_to_date'] = days_old < 7
                        
                        print(f"   📊 Base de datos encontrada: {db_path}")
                        print(f"   📅 Última actualización: {db_date} ({days_old} días)")
                        break
                    except Exception as e:
                        print(f"   ⚠️  Error leyendo base de datos: {e}")
            
            # Intentar leer preferencias de ESET
            plist_paths = [
                os.path.expanduser('~/Library/Preferences/com.eset.esets.plist'),
                '/Library/Preferences/com.eset.esets.plist'
            ]
            
            for plist_path in plist_paths:
                if os.path.exists(plist_path):
                    try:
                        mod_time = os.path.getmtime(plist_path)
                        plist_date = datetime.fromtimestamp(mod_time).isoformat()
                        
                        if not scan_info.get('last_update'):
                            scan_info['last_update'] = plist_date
                        
                        print(f"   ⚙️  Preferencias encontradas: {plist_path}")
                    except:
                        pass
            
            if scan_info:
                print(f"   ✅ Información de ESET obtenida:")
                if scan_info.get('last_update'):
                    print(f"      - Última actualización: {scan_info['last_update']}")
                if scan_info.get('last_scan'):
                    print(f"      - Último escaneo: {scan_info['last_scan']}")
                if scan_info.get('definitions_up_to_date') is not None:
                    print(f"      - Definiciones actualizadas: {scan_info['definitions_up_to_date']}")
            else:
                print(f"   ⚠️  No se pudo obtener información detallada de ESET")
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ❌ Error obteniendo info de ESET: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_sophos_macos_info(self) -> Optional[Dict]:
        """Obtiene información de Sophos en macOS"""
        try:
            scan_info = {}
            
            # Sophos guarda logs en Library
            log_paths = [
                '/Library/Logs/Sophos',
                os.path.expanduser('~/Library/Logs/Sophos')
            ]
            
            for log_dir in log_paths:
                if os.path.exists(log_dir):
                    try:
                        mod_time = os.path.getmtime(log_dir)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = last_update
                        print(f"   Última actualización Sophos: {last_update}")
                        break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Sophos: {e}")
            return None


    def _get_avast_macos_info(self) -> Optional[Dict]:
        """Obtiene información de Avast/AVG en macOS"""
        try:
            scan_info = {}
            
            # Avast guarda información en Library
            db_paths = [
                '/Library/Application Support/Avast/config',
                '/Library/Application Support/AVG/config'
            ]
            
            for db_path in db_paths:
                if os.path.exists(db_path):
                    try:
                        mod_time = os.path.getmtime(db_path)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = last_update
                        print(f"   Última actualización: {last_update}")
                        break
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de Avast: {e}")
            return None


    def _get_generic_macos_antivirus_info(self, av_info: Dict) -> Optional[Dict]:
        """Método genérico para antivirus de macOS"""
        try:
            scan_info = {}
            
            # Buscar en ubicaciones comunes de logs
            log_bases = [
                '/Library/Logs',
                os.path.expanduser('~/Library/Logs'),
                '/Library/Application Support',
                os.path.expanduser('~/Library/Application Support')
            ]
            
            av_name = av_info['name'].split()[0]  # Primera palabra
            
            for log_base in log_bases:
                av_log_path = os.path.join(log_base, av_name)
                if os.path.exists(av_log_path):
                    try:
                        mod_time = os.path.getmtime(av_log_path)
                        last_update = datetime.fromtimestamp(mod_time).isoformat()
                        scan_info['last_update'] = last_update
                        print(f"   Última actualización (genérico): {last_update}")
                        return scan_info
                    except:
                        pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error en detección genérica macOS: {e}")
            return None


    def _decode_antivirus_state(self, product_state: int) -> Dict[str, any]:
        """
        Decodifica el productState de Windows Security Center
        
        Estructura del productState (hexadecimal):
        - Bits 16-19 (nibble 5): Estado del producto
          - 0x0 = Disabled
          - Cualquier otro valor (0x1, 0x2, 0x4, 0x6, etc.) = Enabled
        - Bits 12-15 (nibble 4): Estado de definiciones
          - 0x0 = Up to date
          - 0x1 = Out of date
        
        Ejemplos:
        - 397312 (0x061000): producto=0x6 (ON), definiciones=0x1 (OUT OF DATE)
        - 266240 (0x041000): producto=0x4 (ON), definiciones=0x1 (OUT OF DATE)
        - 393216 (0x060000): producto=0x6 (ON), definiciones=0x0 (UP TO DATE)
        """
        
        state_info = {
            'protection_status': 'unknown',
            'real_time_protection': False,
            'definitions_up_to_date': False
        }
        
        try:
            # Extraer nibbles (4 bits cada uno)
            # Bits 16-19: Estado del producto
            product_enabled = (product_state & 0x000F0000) >> 16
            
            # Bits 12-15: Estado de definiciones
            definitions_state = (product_state & 0x0000F000) >> 12
            
            # Producto habilitado si el nibble NO es 0x0
            if product_enabled != 0x0:
                state_info['protection_status'] = 'active'
                state_info['real_time_protection'] = True
            else:
                state_info['protection_status'] = 'inactive'
                state_info['real_time_protection'] = False
            
            # Definiciones actualizadas si el nibble ES 0x0
            if definitions_state == 0x0:
                state_info['definitions_up_to_date'] = True
            else:
                state_info['definitions_up_to_date'] = False
            
            print(f"   📊 productState: {product_state} (0x{product_state:06X})")
            print(f"      - Producto: 0x{product_enabled:X} → {'Habilitado' if state_info['real_time_protection'] else 'Deshabilitado'}")
            print(f"      - Definiciones: 0x{definitions_state:X} → {'Actualizadas' if state_info['definitions_up_to_date'] else 'Desactualizadas'}")
            
        except Exception as e:
            print(f"   ⚠️  Error decodificando estado: {e}")
        
        return state_info
    # ═══════════════════════════════════════════════════════════
    # Linux - Paquetes, Procesos y Servicios
    # ═══════════════════════════════════════════════════════════
    
    def _collect_linux_antivirus(self, antivirus_info: Dict) -> Dict:
        """Recopila información de antivirus en Linux"""
        
        antivirus_info['detection_method'] = 'Package, Process and Service scanning'
        
        # Antivirus conocidos para Linux
        known_antivirus = {
            # Nombre del proceso/paquete: (Nombre completo, vendor)
            'clamav': ('ClamAV', 'Cisco'),
            'clamd': ('ClamAV Daemon', 'Cisco'),
            'freshclam': ('ClamAV Updater', 'Cisco'),
            'avast': ('Avast for Linux', 'Avast Software'),
            'avg': ('AVG Antivirus', 'AVG Technologies'),
            'bitdefender': ('Bitdefender', 'Bitdefender'),
            'comodo': ('Comodo Antivirus', 'Comodo'),
            'chkrootkit': ('chkrootkit', 'chkrootkit'),
            'rkhunter': ('RKHunter', 'RKHunter'),
            'sophos': ('Sophos Antivirus', 'Sophos'),
            'eset': ('ESET NOD32', 'ESET'),
            'esets': ('ESET Server Security', 'ESET'),
            'fsecure': ('F-Secure', 'F-Secure'),
            'kaspersky': ('Kaspersky', 'Kaspersky'),
            'mcafee': ('McAfee', 'McAfee'),
            'trend': ('Trend Micro', 'Trend Micro'),
        }
        
        detected = []
        
        # Método 1: Verificar procesos en ejecución
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            processes = result.stdout.lower()
            
            for process_name, (full_name, vendor) in known_antivirus.items():
                if process_name in processes:
                    detected.append({
                        'name': full_name,
                        'vendor': vendor,
                        'detection_method': 'Running process',
                        'process_name': process_name
                    })
        except Exception as e:
            print(f"⚠️  Error verificando procesos: {e}")
        
        # Método 2: Verificar paquetes (dpkg - Debian/Ubuntu)
        if os.path.exists('/usr/bin/dpkg'):
            try:
                result = subprocess.run(['dpkg', '-l'], capture_output=True, text=True, timeout=5)
                packages = result.stdout.lower()
                
                for package_name, (full_name, vendor) in known_antivirus.items():
                    if package_name in packages:
                        if not any(d['name'] == full_name for d in detected):
                            detected.append({
                                'name': full_name,
                                'vendor': vendor,
                                'detection_method': 'Installed package (dpkg)',
                                'package_name': package_name
                            })
            except Exception as e:
                print(f"⚠️  Error verificando paquetes dpkg: {e}")
        
        # Método 3: Verificar paquetes (rpm - RedHat/CentOS/Fedora)
        if os.path.exists('/usr/bin/rpm'):
            try:
                result = subprocess.run(['rpm', '-qa'], capture_output=True, text=True, timeout=5)
                packages = result.stdout.lower()
                
                for package_name, (full_name, vendor) in known_antivirus.items():
                    if package_name in packages:
                        if not any(d['name'] == full_name for d in detected):
                            detected.append({
                                'name': full_name,
                                'vendor': vendor,
                                'detection_method': 'Installed package (rpm)',
                                'package_name': package_name
                            })
            except Exception as e:
                print(f"⚠️  Error verificando paquetes rpm: {e}")
        
        # Método 4: Verificar servicios systemd
        if os.path.exists('/usr/bin/systemctl'):
            try:
                result = subprocess.run(
                    ['systemctl', 'list-units', '--type=service', '--all'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                services = result.stdout.lower()
                
                for service_name, (full_name, vendor) in known_antivirus.items():
                    if service_name in services and not any(d['name'] == full_name for d in detected):
                        detected.append({
                            'name': full_name,
                            'vendor': vendor,
                            'detection_method': 'systemd service',
                            'service_name': service_name
                        })
            except Exception as e:
                print(f"⚠️  Error verificando servicios systemd: {e}")
        
        print(f"\n🛡️  Antivirus detectados en Linux: {len(detected)}")
        for av in detected:
            print(f"   - {av['name']} ({av.get('vendor', 'Unknown')})")
        
         # Determinar antivirus principal
        if detected:
            primary_av = detected[0]
            antivirus_info['antivirus_name'] = primary_av['name']
            antivirus_info['third_party_antivirus'] = [av['name'] for av in detected]
            
            # Si el proceso está corriendo, asumimos que está activo
            if primary_av.get('detection_method') == 'Running process':
                antivirus_info['protection_status'] = 'active'
                antivirus_info['real_time_protection'] = True
            else:
                antivirus_info['protection_status'] = 'installed'
                antivirus_info['real_time_protection'] = False
            
            print(f"✅ Usando antivirus principal: {primary_av['name']}")
            
            # ✅ NUEVO: Obtener información de escaneo para ClamAV
            if 'clamav' in primary_av['name'].lower():
                clamav_info = self._get_clamav_scan_info()
                if clamav_info:
                    antivirus_info['last_scan'] = clamav_info.get('last_scan')
                    antivirus_info['last_update'] = clamav_info.get('last_update')
            else:
                antivirus_info['antivirus_name'] = 'None detected'
                print(f"⚠️  No se detectaron productos antivirus")
            
            # Firewall (iptables/ufw/firewalld)
            try:
                # Intentar con ufw primero
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True, timeout=5)
                if 'active' in result.stdout.lower():
                    antivirus_info['firewall_status'] = 'active'
                elif 'inactive' in result.stdout.lower():
                    antivirus_info['firewall_status'] = 'inactive'
            except:
                try:
                    # Intentar con firewalld
                    result = subprocess.run(['firewall-cmd', '--state'], capture_output=True, text=True, timeout=5)
                    if 'running' in result.stdout.lower():
                        antivirus_info['firewall_status'] = 'active'
                except:
                    antivirus_info['firewall_status'] = 'unknown'
            
        return antivirus_info

    def _get_clamav_scan_info(self) -> Optional[Dict]:
        """
        Obtiene información de escaneo de ClamAV desde logs
        
        Returns:
            dict: Información de último escaneo y actualización, o None si falla
        """
        try:
            scan_info = {}
            
            # Intentar obtener última actualización de freshclam
            freshclam_log = '/var/log/clamav/freshclam.log'
            if os.path.exists(freshclam_log):
                try:
                    # Leer las últimas líneas del log
                    result = subprocess.run(
                        ['tail', '-20', freshclam_log],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    # Buscar líneas con "Database updated"
                    for line in result.stdout.split('\n'):
                        if 'database updated' in line.lower():
                            # Extraer fecha (formato: Mon Dec 25 12:00:00 2025)
                            parts = line.split()
                            if len(parts) >= 5:
                                import datetime
                                try:
                                    date_str = ' '.join(parts[:5])
                                    # Parsear la fecha
                                    scan_info['last_update'] = date_str
                                    print(f"   Última actualización de ClamAV: {scan_info['last_update']}")
                                    break
                                except:
                                    pass
                except Exception as e:
                    print(f"   ⚠️  Error leyendo log de freshclam: {e}")
            
            # Intentar obtener última actualización desde base de datos
            clamav_db = '/var/lib/clamav/daily.cvd'
            if os.path.exists(clamav_db):
                try:
                    import datetime
                    mod_time = os.path.getmtime(clamav_db)
                    last_update = datetime.datetime.fromtimestamp(mod_time).isoformat()
                    scan_info['last_update'] = last_update
                    print(f"   Última actualización de base de datos: {last_update}")
                except:
                    pass
            
            return scan_info if scan_info else None
        
        except Exception as e:
            print(f"   ⚠️  Error obteniendo info de ClamAV: {e}")
            return None
# ═══════════════════════════════════════════════════════════
# USO COMO SCRIPT INDEPENDIENTE
# ═══════════════════════════════════════════════════════════

def main():
    """Función principal para ejecutar como script"""
    print("="*80)
    print("🛡️  DETECTOR DE ANTIVIRUS MULTIPLATAFORMA")
    print("="*80)
    print(f"Sistema Operativo: {platform.system()}")
    print(f"Versión: {platform.version()}")
    print("="*80)
    
    collector = AntivirusCollector()
    result = collector.collect_antivirus_info()
    
    print(f"\n{'='*80}")
    print("📊 RESULTADO FINAL")
    print("="*80)
    
    for key, value in result.items():
        if isinstance(value, list):
            print(f"{key}: {', '.join(value) if value else '[]'}")
        else:
            print(f"{key}: {value}")
    
    print("="*80)
    
    return result


if __name__ == "__main__":
    main()