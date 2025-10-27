"""
Hardware Collector - Recopila información de hardware del sistema
Multiplataforma: Windows, macOS, Linux
"""

import platform
import psutil
import socket
import subprocess
import uuid
from typing import Dict, Any, Optional

from .base_collector import BaseCollector


class HardwareCollector(BaseCollector):
    """
    Recopila información de hardware del sistema
    """
    
    def __init__(self):
        super().__init__()
        self.system = platform.system()
    
    def collect(self) -> Dict[str, Any]:
        """
        Recopila toda la información de hardware
        
        Returns:
            dict: Información de hardware del sistema
        """
        info = {
            'operating_system': self.get_os_info(),
            'os_version': self.get_os_version(),
            'processor': self.get_cpu_info(),
            'cpu_cores': psutil.cpu_count(logical=False) or psutil.cpu_count(),
            'total_ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'available_ram_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'total_disk_gb': self.get_total_disk_space(),
            'used_disk_gb': self.get_used_disk_space(),
            'disk_type': self.get_disk_type(),
            'video_card': self.get_gpu_info(),
            'computer_name': socket.gethostname(),
            'ip_address': self.get_ip_address(),
            'mac_address': self.get_mac_address(),
            'bios_version': self.get_bios_version(),
            'uptime_hours': self.get_uptime_hours(),
            'serial_number': self.get_serial_number()
        }
        
        return info
    
    def get_os_info(self) -> str:
        """Obtiene información del sistema operativo"""
        try:
            system = platform.system()
            
            if system == "Windows":
                return f"Windows {platform.release()}"
            elif system == "Darwin":
                return f"macOS {platform.mac_ver()[0]}"
            elif system == "Linux":
                try:
                    import distro
                    return f"{distro.name()} {distro.version()}"
                except ImportError:
                    return f"Linux {platform.release()}"
            else:
                return f"{system} {platform.release()}"
        except Exception as e:
            self.logger.warning(f"Error al obtener OS info: {e}")
            return "Unknown"
    
    def get_os_version(self) -> str:
        """Obtiene la versión detallada del SO"""
        try:
            return platform.version()
        except Exception as e:
            self.logger.warning(f"Error al obtener OS version: {e}")
            return "Unknown"
    
    def get_cpu_info(self) -> str:
        """Obtiene información del procesador"""
        try:
            if self.system == "Windows":
                return platform.processor()
            elif self.system == "Darwin":
                cmd = "sysctl -n machdep.cpu.brand_string"
                result = subprocess.check_output(cmd, shell=True, text=True)
                return result.strip()
            elif self.system == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            return line.split(':')[1].strip()
        except Exception as e:
            self.logger.warning(f"Error al obtener CPU info: {e}")
        
        return platform.processor() or "Unknown"
    
    def get_total_disk_space(self) -> float:
        """Obtiene el espacio total de disco en GB"""
        total = 0
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total += usage.total
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            self.logger.warning(f"Error al obtener espacio total de disco: {e}")
        
        return round(total / (1024**3), 2)
    
    def get_used_disk_space(self) -> float:
        """Obtiene el espacio usado de disco en GB"""
        used = 0
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    used += usage.used
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            self.logger.warning(f"Error al obtener espacio usado de disco: {e}")
        
        return round(used / (1024**3), 2)
    
    def get_disk_type(self) -> str:
        """Intenta detectar el tipo de disco (SSD/HDD)"""
        try:
            if self.system == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    for disk in c.Win32_DiskDrive():
                        media_type = str(disk.MediaType).upper()
                        if 'SSD' in media_type or 'SOLID' in media_type:
                            return 'SSD'
                    return 'HDD'
                except ImportError:
                    self.logger.debug("WMI no disponible en Windows")
                    return 'Unknown'
                    
            elif self.system == "Linux":
                # Verificar si el disco principal es SSD
                cmd = "lsblk -d -o name,rota | grep -w 0"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    return 'SSD'
                return 'HDD'
                
            elif self.system == "Darwin":
                # En macOS, verificar tipo de disco
                cmd = "diskutil info disk0 | grep 'Solid State'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    return 'SSD'
                return 'Unknown'
                
        except Exception as e:
            self.logger.warning(f"No se pudo detectar tipo de disco: {e}")
        
        return 'Unknown'
    
    def get_gpu_info(self) -> str:
        """Obtiene información de la tarjeta gráfica"""
        try:
            if self.system == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    gpus = []
                    for gpu in c.Win32_VideoController():
                        gpus.append(gpu.Name)
                    return ', '.join(gpus) if gpus else 'Unknown'
                except ImportError:
                    return 'Unknown (WMI no disponible)'
                    
            elif self.system == "Linux":
                cmd = "lspci | grep -i vga | cut -d ':' -f 3"
                result = subprocess.check_output(cmd, shell=True, text=True)
                return result.strip() if result.strip() else 'Unknown'
                
            elif self.system == "Darwin":
                cmd = "system_profiler SPDisplaysDataType | grep 'Chipset Model' | cut -d ':' -f 2"
                result = subprocess.check_output(cmd, shell=True, text=True)
                return result.strip() if result.strip() else 'Unknown'
                
        except Exception as e:
            self.logger.warning(f"No se pudo obtener info de GPU: {e}")
        
        return 'Unknown'
    
    def get_ip_address(self) -> str:
        """Obtiene la dirección IP principal"""
        try:
            # Conectar a un servidor externo para obtener la IP local usada
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception as e:
                self.logger.warning(f"Error al obtener IP: {e}")
                return '127.0.0.1'
    
    def get_mac_address(self) -> str:
        """Obtiene la dirección MAC principal"""
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])
            return mac
        except Exception as e:
            self.logger.warning(f"No se pudo obtener MAC address: {e}")
            return 'Unknown'
    
    def get_bios_version(self) -> str:
        """Obtiene la versión del BIOS/UEFI"""
        try:
            if self.system == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    for bios in c.Win32_BIOS():
                        return f"{bios.Manufacturer} {bios.SMBIOSBIOSVersion}"
                except ImportError:
                    return 'Unknown (WMI no disponible)'
                    
            elif self.system == "Linux":
                try:
                    with open('/sys/class/dmi/id/bios_version', 'r') as f:
                        version = f.read().strip()
                    with open('/sys/class/dmi/id/bios_vendor', 'r') as f:
                        vendor = f.read().strip()
                    return f"{vendor} {version}"
                except (FileNotFoundError, PermissionError):
                    return 'Unknown'
                    
            elif self.system == "Darwin":
                cmd = "system_profiler SPHardwareDataType | grep 'Boot ROM Version' | cut -d ':' -f 2"
                result = subprocess.check_output(cmd, shell=True, text=True)
                return result.strip() if result.strip() else 'Unknown'
                
        except Exception as e:
            self.logger.warning(f"No se pudo obtener versión de BIOS: {e}")
        
        return 'Unknown'
    
    def get_uptime_hours(self) -> int:
        """Obtiene las horas desde el último reinicio"""
        try:
            import time as time_module
            boot_time = psutil.boot_time()
            uptime_seconds = time_module.time() - boot_time
            uptime_hours = int(uptime_seconds / 3600)
            return uptime_hours
        except Exception as e:
            self.logger.warning(f"No se pudo obtener uptime: {e}")
            return 0
    
    def get_serial_number(self) -> str:
        """Obtiene el número de serie del equipo"""
        try:
            if self.system == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    for item in c.Win32_BIOS():
                        return item.SerialNumber
                except ImportError:
                    return 'Unknown (WMI no disponible)'
                    
            elif self.system == "Linux":
                try:
                    # Intentar con dmidecode (requiere sudo normalmente)
                    cmd = "cat /sys/class/dmi/id/product_serial 2>/dev/null || cat /sys/class/dmi/id/board_serial 2>/dev/null"
                    result = subprocess.check_output(cmd, shell=True, text=True)
                    serial = result.strip()
                    return serial if serial else 'Unknown'
                except (subprocess.CalledProcessError, FileNotFoundError):
                    return 'Unknown'
                    
            elif self.system == "Darwin":
                cmd = "system_profiler SPHardwareDataType | grep 'Serial Number' | awk '{print $4}'"
                result = subprocess.check_output(cmd, shell=True, text=True)
                return result.strip() if result.strip() else 'Unknown'
                
        except Exception as e:
            self.logger.warning(f"No se pudo obtener número de serie: {e}")
        
        return 'Unknown'