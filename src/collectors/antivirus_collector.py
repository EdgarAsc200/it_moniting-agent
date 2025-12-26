"""
Antivirus Collector - Detección multiplataforma de software antivirus
Soporta: Windows, macOS, Linux
"""

import os
import platform
import subprocess
from typing import Dict, List, Optional
from datetime import datetime


class AntivirusCollector:
    """Recolector de información de antivirus multiplataforma"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.logger = None  # Si tienes logging, asigna aquí
    def collect(self) -> Dict:
        """
        Método de interfaz unificada para compatibilidad con otros collectors
        Llama internamente a collect_antivirus_info()
        
        Returns:
            dict: Información del antivirus detectado
        """
        try:
            return self.collect_antivirus_info()
        except Exception as e:
            print(f"❌ Error en collect(): {e}")
            return {
                'antivirus_name': 'Error',
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
    # macOS - Procesos y Aplicaciones
    # ═══════════════════════════════════════════════════════════
    
    def _collect_macos_antivirus(self, antivirus_info: Dict) -> Dict:
        """Recopila información de antivirus en macOS"""
        
        antivirus_info['detection_method'] = 'Process and Application scanning'
        
        # Lista de antivirus conocidos para macOS
        known_antivirus = {
            # Nombre del proceso: (Nombre completo, vendor)
            'AVGAntivirus': ('AVG Antivirus', 'AVG Technologies'),
            'avast': ('Avast Security', 'Avast Software'),
            'BitdefenderAgent': ('Bitdefender Antivirus', 'Bitdefender'),
            'ClamAV': ('ClamAV', 'Cisco'),
            'clamd': ('ClamAV Daemon', 'Cisco'),
            'DrWeb': ('Dr.Web', 'Doctor Web'),
            'ESET': ('ESET Cyber Security', 'ESET'),
            'esets_daemon': ('ESET Daemon', 'ESET'),
            'FSAgent': ('F-Secure', 'F-Secure'),
            'KasperskyAV': ('Kaspersky Internet Security', 'Kaspersky'),
            'kav': ('Kaspersky', 'Kaspersky'),
            'MalwareBytes': ('Malwarebytes', 'Malwarebytes'),
            'mbam': ('Malwarebytes Anti-Malware', 'Malwarebytes'),
            'McAfee': ('McAfee Antivirus', 'McAfee'),
            'Norton': ('Norton 360', 'NortonLifeLock'),
            'SophosScanD': ('Sophos Home', 'Sophos'),
            'sophossxld': ('Sophos Endpoint', 'Sophos'),
            'TrendMicro': ('Trend Micro', 'Trend Micro'),
            'VirusBarrier': ('Intego VirusBarrier', 'Intego'),
            'Webroot': ('Webroot SecureAnywhere', 'Webroot'),
        }
        
        detected = []
        
        # Método 1: Verificar procesos en ejecución
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            processes = result.stdout.lower()
            
            for process_name, (full_name, vendor) in known_antivirus.items():
                if process_name.lower() in processes:
                    detected.append({
                        'name': full_name,
                        'vendor': vendor,
                        'detection_method': 'Running process',
                        'process_name': process_name
                    })
        except Exception as e:
            print(f"⚠️  Error verificando procesos: {e}")
        
        # Método 2: Verificar aplicaciones instaladas
        app_paths = ['/Applications', os.path.expanduser('~/Applications')]
        
        for app_path in app_paths:
            if os.path.exists(app_path):
                try:
                    apps = os.listdir(app_path)
                    for process_name, (full_name, vendor) in known_antivirus.items():
                        matching_apps = [app for app in apps if process_name.lower() in app.lower()]
                        for app in matching_apps:
                            # Evitar duplicados
                            if not any(d['name'] == full_name for d in detected):
                                detected.append({
                                    'name': full_name,
                                    'vendor': vendor,
                                    'detection_method': 'Installed application',
                                    'app_path': f"{app_path}/{app}"
                                })
                except Exception as e:
                    print(f"⚠️  Error verificando {app_path}: {e}")
        
        # Verificar XProtect (antivirus integrado de macOS)
        xprotect_path = '/System/Library/CoreServices/XProtect.bundle'
        xprotect_detected = False
        if os.path.exists(xprotect_path):
            xprotect_detected = True
            detected.append({
                'name': 'XProtect',
                'vendor': 'Apple',
                'detection_method': 'Built-in macOS protection',
                'app_path': xprotect_path,
                'is_builtin': True
            })
        
        print(f"\n🛡️  Antivirus detectados en macOS: {len(detected)}")
        for av in detected:
            print(f"   - {av['name']} ({av.get('vendor', 'Unknown')})")
        
        # Determinar antivirus principal (priorizar terceros)
        third_party = [av for av in detected if not av.get('is_builtin', False)]
        
        if third_party:
            # Usar el primer antivirus de terceros
            primary_av = third_party[0]
            antivirus_info['antivirus_name'] = primary_av['name']
            antivirus_info['antivirus_version'] = primary_av.get('version', None)
            antivirus_info['third_party_antivirus'] = [av['name'] for av in third_party]
            
            # Si el proceso está corriendo, asumimos que está activo
            if primary_av.get('detection_method') == 'Running process':
                antivirus_info['protection_status'] = 'active'
                antivirus_info['real_time_protection'] = True
            else:
                antivirus_info['protection_status'] = 'installed'
                antivirus_info['real_time_protection'] = False
            
            print(f"✅ Usando antivirus principal: {primary_av['name']}")
        
        elif xprotect_detected:
            # Solo XProtect (nativo)
            antivirus_info['antivirus_name'] = 'XProtect'
            antivirus_info['protection_status'] = 'active'
            antivirus_info['real_time_protection'] = True
            antivirus_info['third_party_antivirus'] = []
            print(f"✅ Usando XProtect (no hay terceros)")
        
        else:
            antivirus_info['antivirus_name'] = 'None detected'
            print(f"⚠️  No se detectaron productos antivirus")
        
        # Firewall de macOS
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