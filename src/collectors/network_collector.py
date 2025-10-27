# src/collectors/network_collector.py

import platform
import subprocess
import re
import socket
import logging
from typing import Dict, List, Optional

class NetworkCollector:
    """
    Recopila información sobre la configuración de red del sistema.
    Funciona en Windows, macOS y Linux.
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self.logger = logging.getLogger('ITAgent.NetworkCollector')
    
    def safe_collect(self) -> Dict:
        """
        Método seguro de recopilación con manejo de errores
        
        Returns:
            dict: Datos de red, o datos vacíos en caso de error
        """
        try:
            return self.collect()
        except Exception as e:
            self.logger.error(f"Error en recopilación de red: {e}", exc_info=True)
            return self._get_empty_data()
    
    def collect(self) -> Dict:
        """Recopila toda la información de red"""
        
        self.logger.debug(f"Recopilando información de red en {self.os_type}...")
        
        data = {
            'hostname': self._get_hostname(),
            'interfaces': [],
            'default_gateway': None,
            'dns_servers': [],
            'public_ip': None,
            'total_interfaces': 0
        }
        
        if self.os_type == "Windows":
            interfaces = self._collect_windows()
        elif self.os_type == "Darwin":  # macOS
            interfaces = self._collect_macos()
        elif self.os_type == "Linux":
            interfaces = self._collect_linux()
        else:
            interfaces = []
        
        data['interfaces'] = interfaces
        data['total_interfaces'] = len(interfaces)
        
        # Obtener gateway por defecto
        data['default_gateway'] = self._get_default_gateway()
        
        # Obtener servidores DNS
        data['dns_servers'] = self._get_dns_servers()
        
        # Obtener IP pública (opcional, puede fallar si no hay internet)
        try:
            data['public_ip'] = self._get_public_ip()
        except Exception:
            data['public_ip'] = None
        
        return data
    
    def _get_hostname(self) -> str:
        """Obtiene el nombre del host"""
        try:
            return socket.gethostname()
        except Exception as e:
            self.logger.debug(f"Error obteniendo hostname: {e}")
            return 'Unknown'
    
    def _collect_windows(self) -> List[Dict]:
        """Recopila información de red en Windows"""
        interfaces = []
        
        try:
            # Usar PowerShell para obtener configuración de red
            ps_command = """
            Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object {
                $adapter = $_
                $ipConfig = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue
                $ipv4 = $ipConfig | Where-Object {$_.AddressFamily -eq 'IPv4'}
                $ipv6 = $ipConfig | Where-Object {$_.AddressFamily -eq 'IPv6'}
                
                [PSCustomObject]@{
                    Name = $adapter.Name
                    Description = $adapter.InterfaceDescription
                    MAC = $adapter.MacAddress
                    Status = $adapter.Status
                    Speed = $adapter.LinkSpeed
                    IPv4 = if ($ipv4) { $ipv4.IPAddress } else { $null }
                    IPv4Subnet = if ($ipv4) { $ipv4.PrefixLength } else { $null }
                    IPv6 = if ($ipv6) { $ipv6.IPAddress } else { $null }
                    Type = $adapter.InterfaceType
                }
            } | ConvertTo-Json
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                adapters_data = json.loads(result.stdout)
                
                # Si es un solo adaptador, convertir a lista
                if isinstance(adapters_data, dict):
                    adapters_data = [adapters_data]
                
                for adapter in adapters_data:
                    interface_info = {
                        'name': adapter.get('Name', 'Unknown'),
                        'description': adapter.get('Description', 'Unknown'),
                        'mac_address': adapter.get('MAC', 'Unknown'),
                        'status': adapter.get('Status', 'Unknown'),
                        'speed': adapter.get('Speed', 'Unknown'),
                        'ipv4_address': adapter.get('IPv4'),
                        'ipv4_subnet': adapter.get('IPv4Subnet'),
                        'ipv6_address': adapter.get('IPv6'),
                        'type': adapter.get('Type', 'Unknown')
                    }
                    interfaces.append(interface_info)
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de red Windows: {e}")
        
        return interfaces
    
    def _collect_macos(self) -> List[Dict]:
        """Recopila información de red en macOS"""
        interfaces = []
        
        try:
            # Obtener lista de interfaces
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                interfaces = self._parse_ifconfig(result.stdout)
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de red macOS: {e}")
        
        return interfaces
    
    def _collect_linux(self) -> List[Dict]:
        """Recopila información de red en Linux"""
        interfaces = []
        
        try:
            # Intentar usar 'ip' primero (más moderno)
            if self._command_exists('ip'):
                interfaces = self._collect_linux_ip_command()
            
            # Si no funcionó o no está disponible, usar ifconfig
            if not interfaces and self._command_exists('ifconfig'):
                result = subprocess.run(
                    ["ifconfig"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    interfaces = self._parse_ifconfig(result.stdout)
        
        except Exception as e:
            self.logger.error(f"Error en recopilación de red Linux: {e}")
        
        return interfaces
    
    def _collect_linux_ip_command(self) -> List[Dict]:
        """Recopila información de red usando el comando 'ip' en Linux"""
        interfaces = []
        
        try:
            # Obtener lista de interfaces
            result = subprocess.run(
                ["ip", "-details", "address", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                interfaces = self._parse_ip_command(result.stdout)
        
        except Exception as e:
            self.logger.debug(f"Error usando comando 'ip': {e}")
        
        return interfaces
    
    def _parse_ifconfig(self, output: str) -> List[Dict]:
        """Parsea la salida del comando ifconfig"""
        interfaces = []
        current_interface = None
        
        lines = output.split('\n')
        
        for line in lines:
            # Nueva interfaz (no empieza con espacio o tab)
            if line and not line[0].isspace():
                # Guardar interfaz anterior si existe
                if current_interface:
                    interfaces.append(current_interface)
                
                # Parsear nombre de interfaz
                match = re.match(r'^(\S+):', line)
                if match:
                    interface_name = match.group(1)
                    current_interface = {
                        'name': interface_name,
                        'description': interface_name,
                        'mac_address': None,
                        'status': 'Unknown',
                        'ipv4_address': None,
                        'ipv4_subnet': None,
                        'ipv6_address': None,
                        'type': 'Unknown'
                    }
                    
                    # Estado (UP/DOWN)
                    if 'UP' in line:
                        current_interface['status'] = 'Up'
                    elif 'DOWN' in line:
                        current_interface['status'] = 'Down'
            
            # Información de la interfaz actual
            elif current_interface:
                # MAC address
                mac_match = re.search(r'ether\s+([0-9a-f:]+)', line, re.IGNORECASE)
                if not mac_match:
                    mac_match = re.search(r'HWaddr\s+([0-9a-f:]+)', line, re.IGNORECASE)
                if mac_match:
                    current_interface['mac_address'] = mac_match.group(1)
                
                # IPv4
                ipv4_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                if ipv4_match:
                    current_interface['ipv4_address'] = ipv4_match.group(1)
                    
                    # Máscara de subred
                    netmask_match = re.search(r'netmask\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if netmask_match:
                        current_interface['ipv4_subnet'] = netmask_match.group(1)
                    
                    # O en formato CIDR
                    cidr_match = re.search(r'inet\s+\d+\.\d+\.\d+\.\d+/(\d+)', line)
                    if cidr_match:
                        current_interface['ipv4_subnet'] = cidr_match.group(1)
                
                # IPv6
                ipv6_match = re.search(r'inet6\s+([0-9a-f:]+)', line, re.IGNORECASE)
                if ipv6_match:
                    current_interface['ipv6_address'] = ipv6_match.group(1)
        
        # Agregar última interfaz
        if current_interface:
            interfaces.append(current_interface)
        
        # Filtrar solo interfaces activas con IP
        interfaces = [iface for iface in interfaces if iface.get('ipv4_address') or iface.get('ipv6_address')]
        
        return interfaces
    
    def _parse_ip_command(self, output: str) -> List[Dict]:
        """Parsea la salida del comando 'ip address'"""
        interfaces = []
        current_interface = None
        
        lines = output.split('\n')
        
        for line in lines:
            # Nueva interfaz
            if re.match(r'^\d+:', line):
                # Guardar interfaz anterior
                if current_interface:
                    interfaces.append(current_interface)
                
                # Parsear nueva interfaz
                match = re.match(r'^\d+:\s+(\S+):', line)
                if match:
                    interface_name = match.group(1)
                    current_interface = {
                        'name': interface_name,
                        'description': interface_name,
                        'mac_address': None,
                        'status': 'Down',
                        'ipv4_address': None,
                        'ipv4_subnet': None,
                        'ipv6_address': None,
                        'type': 'Unknown'
                    }
                    
                    # Estado
                    if 'state UP' in line:
                        current_interface['status'] = 'Up'
                    elif 'state DOWN' in line:
                        current_interface['status'] = 'Down'
            
            # Información de la interfaz actual
            elif current_interface:
                # MAC address
                mac_match = re.search(r'link/ether\s+([0-9a-f:]+)', line)
                if mac_match:
                    current_interface['mac_address'] = mac_match.group(1)
                
                # IPv4
                ipv4_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)', line)
                if ipv4_match:
                    current_interface['ipv4_address'] = ipv4_match.group(1)
                    current_interface['ipv4_subnet'] = ipv4_match.group(2)
                
                # IPv6
                ipv6_match = re.search(r'inet6\s+([0-9a-f:]+)/(\d+)', line)
                if ipv6_match:
                    current_interface['ipv6_address'] = ipv6_match.group(1)
        
        # Agregar última interfaz
        if current_interface:
            interfaces.append(current_interface)
        
        # Filtrar solo interfaces activas con IP
        interfaces = [iface for iface in interfaces if iface.get('status') == 'Up' and (iface.get('ipv4_address') or iface.get('ipv6_address'))]
        
        return interfaces
    
    def _get_default_gateway(self) -> Optional[str]:
        """Obtiene la puerta de enlace predeterminada"""
        try:
            if self.os_type == "Windows":
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    match = re.search(r'Default Gateway.*:\s*(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        return match.group(1)
            
            elif self.os_type in ["Darwin", "Linux"]:
                # Intentar con 'ip route'
                if self._command_exists('ip'):
                    result = subprocess.run(
                        ["ip", "route", "show", "default"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if match:
                            return match.group(1)
                
                # Intentar con 'route -n' o 'netstat -rn'
                if self._command_exists('route'):
                    result = subprocess.run(
                        ["route", "-n"] if self.os_type == "Linux" else ["route", "-n", "get", "default"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        if self.os_type == "Linux":
                            match = re.search(r'0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                        else:  # macOS
                            match = re.search(r'gateway:\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                        
                        if match:
                            return match.group(1)
        
        except Exception as e:
            self.logger.debug(f"Error obteniendo gateway: {e}")
        
        return None
    
    def _get_dns_servers(self) -> List[str]:
        """Obtiene la lista de servidores DNS"""
        dns_servers = []
        
        try:
            if self.os_type == "Windows":
                result = subprocess.run(
                    ["ipconfig", "/all"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Buscar todas las líneas de DNS
                    dns_matches = re.findall(r'DNS Servers.*?:\s*(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    dns_servers.extend(dns_matches)
            
            elif self.os_type in ["Darwin", "Linux"]:
                # Leer /etc/resolv.conf
                try:
                    with open('/etc/resolv.conf', 'r') as f:
                        content = f.read()
                        dns_matches = re.findall(r'nameserver\s+(\d+\.\d+\.\d+\.\d+)', content)
                        dns_servers.extend(dns_matches)
                except Exception:
                    pass
                
                # En macOS también intentar con scutil
                if self.os_type == "Darwin" and not dns_servers:
                    result = subprocess.run(
                        ["scutil", "--dns"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        dns_matches = re.findall(r'nameserver\[\d+\]\s*:\s*(\d+\.\d+\.\d+\.\d+)', result.stdout)
                        dns_servers.extend(dns_matches)
        
        except Exception as e:
            self.logger.debug(f"Error obteniendo DNS: {e}")
        
        # Eliminar duplicados manteniendo el orden
        return list(dict.fromkeys(dns_servers))
    
    def _get_public_ip(self) -> Optional[str]:
        """Obtiene la IP pública usando un servicio externo"""
        try:
            # Intentar varios servicios por si uno falla
            services = [
                'https://api.ipify.org',
                'https://ifconfig.me/ip',
                'https://icanhazip.com'
            ]
            
            for service in services:
                try:
                    import urllib.request
                    with urllib.request.urlopen(service, timeout=5) as response:
                        public_ip = response.read().decode('utf-8').strip()
                        
                        # Validar que es una IP válida
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', public_ip):
                            return public_ip
                
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.debug(f"Error obteniendo IP pública: {e}")
        
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
            'hostname': 'Unknown',
            'interfaces': [],
            'default_gateway': None,
            'dns_servers': [],
            'public_ip': None,
            'total_interfaces': 0,
            'error': 'Collector failed'
        }