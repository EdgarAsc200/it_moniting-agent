# src/collectors/hardware_collector.py

import platform
import psutil
import socket
import subprocess
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

# Importar modelos
from models import Hardware, HardwareType, HardwareStatus, HardwareComponent, Asset, AssetType, AssetStatus, AssetLocation


class HardwareCollector:
    """
    Recopila información de hardware del sistema.
    Soporta Windows, macOS y Linux.
    """
    
    def __init__(self):
        self.os_type = platform.system()
    
    def collect(self) -> Dict[str, Any]:
        """
        Recopila información de hardware del sistema
        """
        return {
            'report_date': datetime.now().isoformat(),
            'hostname': socket.gethostname(),
            'operating_system': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'processor_cores': psutil.cpu_count(logical=False),
            'processor_threads': psutil.cpu_count(logical=True),
            'processor_speed': self._get_cpu_speed(),
            'total_ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'available_ram_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'total_disk_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
            'available_disk_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
            'system_info': self._get_system_info(),
            'disk_info': self._get_disk_info()
        }
    
    def _get_cpu_speed(self) -> Optional[float]:
        """Obtiene la velocidad del CPU en GHz"""
        try:
            if self.os_type == "Darwin":  # macOS
                result = subprocess.run(
                    ["sysctl", "-n", "hw.cpufrequency"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    hz = int(result.stdout.strip())
                    return round(hz / 1e9, 2)  # Convertir a GHz
            elif self.os_type == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'cpu MHz' in line:
                            mhz = float(line.split(':')[1].strip())
                            return round(mhz / 1000, 2)  # Convertir a GHz
        except:
            pass
        return None
    
    def _get_system_info(self) -> Dict[str, str]:
        """Obtiene información del sistema"""
        info = {
            'manufacturer': 'Unknown',
            'model': 'Unknown',
            'serial_number': None
        }
        
        try:
            if self.os_type == "Darwin":  # macOS
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Model Name:' in line:
                            info['manufacturer'] = 'Apple'
                            info['model'] = line.split(':')[1].strip()
                        elif 'Serial Number' in line:
                            info['serial_number'] = line.split(':')[1].strip()
            
            elif self.os_type == "Windows":
                # Manufacturer
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "manufacturer"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        info['manufacturer'] = lines[1].strip()
                
                # Model
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "model"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        info['model'] = lines[1].strip()
                
                # Serial
                result = subprocess.run(
                    ["wmic", "bios", "get", "serialnumber"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        info['serial_number'] = lines[1].strip()
            
            elif self.os_type == "Linux":
                try:
                    with open('/sys/class/dmi/id/sys_vendor', 'r') as f:
                        info['manufacturer'] = f.read().strip()
                except:
                    pass
                
                try:
                    with open('/sys/class/dmi/id/product_name', 'r') as f:
                        info['model'] = f.read().strip()
                except:
                    pass
                
                try:
                    with open('/sys/class/dmi/id/product_serial', 'r') as f:
                        info['serial_number'] = f.read().strip()
                except:
                    pass
        
        except Exception as e:
            pass
        
        return info
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Obtiene información de discos"""
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': usage.percent
                })
            except:
                continue
        return {'partitions': disks}
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS PARA MODELOS
    # ═══════════════════════════════════════════════════════════
    
    def collect_as_model(self, asset_id: str = None) -> Hardware:
        """
        Recopila información de hardware y retorna modelo Hardware
        
        Args:
            asset_id: ID del asset asociado (se genera si no se proporciona)
            
        Returns:
            Hardware: Instancia del modelo Hardware validada
        """
        # Recolectar datos usando el método original
        data = self.collect()
        
        # Generar IDs
        hardware_id = str(uuid.uuid4())
        if not asset_id:
            asset_id = str(uuid.uuid4())
        
        # Determinar tipo de hardware
        os_name = data.get('operating_system', 'Unknown')
        hardware_type = self._determine_hardware_type(os_name)
        
        # Extraer información del sistema
        system_info = data.get('system_info', {})
        
        # Crear componentes
        components = self._create_components(data)
        
        # Crear modelo Hardware
        hardware = Hardware(
            id=hardware_id,
            asset_id=asset_id,
            type=hardware_type,
            manufacturer=system_info.get('manufacturer', 'Unknown'),
            model=system_info.get('model', 'Unknown'),
            serial_number=system_info.get('serial_number'),
            processor=data.get('processor'),
            ram_gb=data.get('total_ram_gb'),
            storage_gb=data.get('total_disk_gb'),
            components=components,
            status=HardwareStatus.OPERATIONAL,
            specifications={
                'operating_system': os_name,
                'os_version': data.get('os_version'),
                'architecture': data.get('architecture'),
                'hostname': data.get('hostname'),
                'processor_cores': data.get('processor_cores'),
                'processor_speed': data.get('processor_speed'),
                'system_info': system_info,
                'disk_info': data.get('disk_info', {})
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Validar antes de retornar
        hardware.validate()
        
        return hardware
    
    def create_asset(
        self, 
        location: str = None, 
        department: str = None, 
        assigned_to: str = None
    ) -> Asset:
        """
        Crea un Asset desde información del sistema
        
        Args:
            location: Ubicación del asset
            department: Departamento
            assigned_to: Usuario asignado
            
        Returns:
            Asset: Instancia del modelo Asset validada
        """
        # Recolectar datos
        data = self.collect()
        
        # Generar ID y asset tag
        asset_id = str(uuid.uuid4())
        hostname = data.get('hostname', socket.gethostname())
        asset_tag = f"IT-{hostname.upper()}"
        
        # Determinar tipo de asset
        os_name = data.get('operating_system', '').lower()
        if 'server' in os_name:
            asset_type = AssetType.SERVER
        else:
            asset_type = AssetType.COMPUTER
        
        # Crear ubicación si se proporciona
        location_obj = None
        if location:
            location_obj = AssetLocation(
                building=location,
                floor=None,
                room=None,
                notes=f"Department: {department}" if department else None
            )
        
        # Extraer información del sistema
        system_info = data.get('system_info', {})
        
        # Crear Asset
        asset = Asset(
            id=asset_id,
            asset_tag=asset_tag,
            name=hostname,
            asset_type=asset_type,
            status=AssetStatus.IN_USE,
            manufacturer=system_info.get('manufacturer', 'Unknown'),
            model=system_info.get('model', 'Unknown'),
            serial_number=system_info.get('serial_number'),
            location=location_obj,
            department=department,
            assigned_to=assigned_to,
            description=f"{data.get('operating_system')} - {data.get('processor')}",
            tags=[
                data.get('operating_system', 'unknown_os'),
                asset_type.value
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Validar
        asset.validate()
        
        return asset
    
    def _determine_hardware_type(self, os_name: str) -> HardwareType:
        """Determina el tipo de hardware basado en el OS"""
        os_lower = os_name.lower()
        
        if 'server' in os_lower:
            return HardwareType.SERVER
        elif 'windows' in os_lower or 'macos' in os_lower or 'linux' in os_lower:
            return HardwareType.DESKTOP
        else:
            return HardwareType.OTHER
    
    def _create_components(self, data: Dict[str, Any]) -> list:
        """Crea lista de HardwareComponents desde los datos"""
        components = []
        
        # Componente: Procesador
        processor = data.get('processor')
        if processor:
            components.append(HardwareComponent(
                type='CPU',
                name=processor,
                specification=f"{data.get('processor_cores', 'N/A')} cores",
                manufacturer=self._extract_cpu_manufacturer(processor)
            ))
        
        # Componente: RAM
        ram_gb = data.get('total_ram_gb')
        if ram_gb:
            components.append(HardwareComponent(
                type='RAM',
                name=f'{ram_gb} GB RAM',
                specification=f'{ram_gb} GB'
            ))
        
        # Componente: Almacenamiento
        storage_gb = data.get('total_disk_gb')
        if storage_gb:
            components.append(HardwareComponent(
                type='Storage',
                name=f'{storage_gb} GB Storage',
                specification=f'{storage_gb} GB'
            ))
        
        return components
    
    def _extract_cpu_manufacturer(self, processor_name: str) -> Optional[str]:
        """Extrae el fabricante del nombre del procesador"""
        processor_lower = processor_name.lower()
        
        if 'intel' in processor_lower:
            return 'Intel'
        elif 'amd' in processor_lower:
            return 'AMD'
        elif 'apple' in processor_lower or 'm1' in processor_lower or 'm2' in processor_lower or 'm3' in processor_lower or 'm4' in processor_lower:
            return 'Apple'
        elif 'arm' in processor_lower:
            return 'ARM'
        else:
            return None