"""
IT Monitoring Agent - Network Utilities
Funciones para operaciones y verificaciones de red
"""

import socket
import subprocess
import platform
from typing import Optional, Tuple, List, Dict, Any


def is_port_open(
    host: str,
    port: int,
    timeout: float = 2.0
) -> bool:
    """
    Verifica si un puerto está abierto en un host
    
    Args:
        host: Hostname o IP
        port: Puerto a verificar
        timeout: Timeout en segundos
        
    Returns:
        True si el puerto está abierto
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        return result == 0
    except Exception:
        return False


def ping_host(
    host: str,
    count: int = 1,
    timeout: int = 5
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Hace ping a un host
    
    Args:
        host: Hostname o IP
        count: Número de paquetes a enviar
        timeout: Timeout en segundos
        
    Returns:
        Tuple (success, result_dict)
    """
    try:
        system = platform.system()
        
        # Comandos específicos por plataforma
        if system == 'Windows':
            command = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
        else:  # Linux, macOS
            command = ['ping', '-c', str(count), '-W', str(timeout), host]
        
        # Ejecutar ping
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        
        success = result.returncode == 0
        
        # Parsear resultado básico
        output = result.stdout
        
        return success, {
            'host': host,
            'reachable': success,
            'output': output,
            'packets_sent': count
        }
        
    except Exception as e:
        return False, {
            'host': host,
            'reachable': False,
            'error': str(e)
        }


def get_local_ip() -> Optional[str]:
    """
    Obtiene la dirección IP local del sistema
    
    Returns:
        Dirección IP local o None
    """
    try:
        # Crear socket UDP para obtener la IP local
        # No necesita conectarse realmente
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        
        return local_ip
    except Exception:
        try:
            # Fallback: obtener hostname y resolver
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return None


def get_public_ip() -> Optional[str]:
    """
    Obtiene la dirección IP pública usando un servicio externo
    
    Returns:
        IP pública o None
    """
    try:
        import urllib.request
        
        # Usar servicio de ipify
        with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
            return response.read().decode('utf-8').strip()
    except Exception:
        return None


def resolve_hostname(hostname: str) -> Optional[str]:
    """
    Resuelve un hostname a dirección IP
    
    Args:
        hostname: Hostname a resolver
        
    Returns:
        Dirección IP o None
    """
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return None


def reverse_dns_lookup(ip: str) -> Optional[str]:
    """
    Realiza lookup reverso de DNS (IP a hostname)
    
    Args:
        ip: Dirección IP
        
    Returns:
        Hostname o None
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def check_internet_connection(
    test_host: str = '8.8.8.8',
    test_port: int = 53,
    timeout: float = 3.0
) -> bool:
    """
    Verifica si hay conexión a Internet
    
    Args:
        test_host: Host para probar (default: Google DNS)
        test_port: Puerto para probar (default: DNS 53)
        timeout: Timeout en segundos
        
    Returns:
        True si hay conexión
    """
    return is_port_open(test_host, test_port, timeout)


def get_hostname() -> str:
    """
    Obtiene el hostname del sistema
    
    Returns:
        Hostname
    """
    try:
        return socket.gethostname()
    except Exception:
        return 'unknown'


def get_fqdn() -> str:
    """
    Obtiene el FQDN (Fully Qualified Domain Name)
    
    Returns:
        FQDN del sistema
    """
    try:
        return socket.getfqdn()
    except Exception:
        return get_hostname()


def check_port_range(
    host: str,
    start_port: int,
    end_port: int,
    timeout: float = 1.0
) -> Dict[int, bool]:
    """
    Verifica un rango de puertos
    
    Args:
        host: Host a verificar
        start_port: Puerto inicial
        end_port: Puerto final
        timeout: Timeout por puerto
        
    Returns:
        Dict {puerto: está_abierto}
    """
    results = {}
    
    for port in range(start_port, end_port + 1):
        results[port] = is_port_open(host, port, timeout)
    
    return results


def get_network_interfaces() -> List[Dict[str, Any]]:
    """
    Obtiene información de las interfaces de red
    
    Returns:
        Lista de interfaces
    """
    try:
        import netifaces
        
        interfaces = []
        
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            
            interface_info = {
                'name': iface,
                'ipv4': [],
                'ipv6': [],
                'mac': None
            }
            
            # IPv4
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    interface_info['ipv4'].append({
                        'address': addr.get('addr'),
                        'netmask': addr.get('netmask'),
                        'broadcast': addr.get('broadcast')
                    })
            
            # IPv6
            if netifaces.AF_INET6 in addrs:
                for addr in addrs[netifaces.AF_INET6]:
                    interface_info['ipv6'].append({
                        'address': addr.get('addr'),
                        'netmask': addr.get('netmask')
                    })
            
            # MAC
            if netifaces.AF_LINK in addrs:
                interface_info['mac'] = addrs[netifaces.AF_LINK][0].get('addr')
            
            interfaces.append(interface_info)
        
        return interfaces
        
    except ImportError:
        # Si netifaces no está disponible, retornar info básica
        return [{
            'name': 'default',
            'ipv4': [{'address': get_local_ip()}],
            'ipv6': [],
            'mac': None
        }]


def download_file(
    url: str,
    output_path: str,
    timeout: int = 30,
    chunk_size: int = 8192
) -> bool:
    """
    Descarga un archivo desde una URL
    
    Args:
        url: URL del archivo
        output_path: Path donde guardar
        timeout: Timeout en segundos
        chunk_size: Tamaño de chunks para descarga
        
    Returns:
        True si se descargó correctamente
    """
    try:
        import urllib.request
        
        with urllib.request.urlopen(url, timeout=timeout) as response:
            with open(output_path, 'wb') as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
        
        return True
    except Exception:
        return False


def test_http_connection(
    url: str,
    timeout: int = 10,
    method: str = 'GET'
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Prueba una conexión HTTP/HTTPS
    
    Args:
        url: URL a probar
        timeout: Timeout en segundos
        method: Método HTTP (GET, POST, HEAD)
        
    Returns:
        Tuple (success, status_code, error_message)
    """
    try:
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return True, response.status, None
            
    except urllib.error.HTTPError as e:
        return False, e.code, str(e)
    except urllib.error.URLError as e:
        return False, None, str(e.reason)
    except Exception as e:
        return False, None, str(e)


def get_dns_servers() -> List[str]:
    """
    Obtiene la lista de servidores DNS configurados
    
    Returns:
        Lista de IPs de servidores DNS
    """
    dns_servers = []
    
    try:
        system = platform.system()
        
        if system == 'Windows':
            # Windows: usar ipconfig
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if 'DNS Servers' in line or 'Servidores DNS' in line:
                    # Extraer IP
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        if ip:
                            dns_servers.append(ip)
        
        elif system == 'Linux':
            # Linux: leer /etc/resolv.conf
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.strip().startswith('nameserver'):
                            parts = line.split()
                            if len(parts) > 1:
                                dns_servers.append(parts[1])
            except Exception:
                pass
        
        elif system == 'Darwin':  # macOS
            # macOS: usar scutil
            result = subprocess.run(
                ['scutil', '--dns'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if 'nameserver' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        if ip and ip not in dns_servers:
                            dns_servers.append(ip)
    
    except Exception:
        pass
    
    return dns_servers


def traceroute(host: str, max_hops: int = 30) -> List[Dict[str, Any]]:
    """
    Realiza un traceroute a un host
    
    Args:
        host: Host destino
        max_hops: Número máximo de saltos
        
    Returns:
        Lista de hops
    """
    try:
        system = platform.system()
        
        if system == 'Windows':
            command = ['tracert', '-h', str(max_hops), host]
        else:
            command = ['traceroute', '-m', str(max_hops), host]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parseo básico del output
        hops = []
        for line in result.stdout.split('\n'):
            if line.strip():
                hops.append({'line': line.strip()})
        
        return hops
        
    except Exception:
        return []


def check_ssl_certificate(
    hostname: str,
    port: int = 443,
    timeout: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Verifica el certificado SSL de un servidor
    
    Args:
        hostname: Hostname del servidor
        port: Puerto SSL (default: 443)
        timeout: Timeout en segundos
        
    Returns:
        Dict con información del certificado o None
    """
    try:
        import ssl
        from datetime import datetime
        
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                # Parsear fechas
                not_before = datetime.strptime(
                    cert['notBefore'],
                    '%b %d %H:%M:%S %Y %Z'
                )
                not_after = datetime.strptime(
                    cert['notAfter'],
                    '%b %d %H:%M:%S %Y %Z'
                )
                
                return {
                    'subject': dict(x[0] for x in cert['subject']),
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'version': cert['version'],
                    'serial_number': cert['serialNumber'],
                    'not_before': not_before.isoformat(),
                    'not_after': not_after.isoformat(),
                    'expired': datetime.now() > not_after,
                    'days_until_expiry': (not_after - datetime.now()).days
                }
    
    except Exception:
        return None


def get_connection_info() -> Dict[str, Any]:
    """
    Obtiene información completa de conectividad
    
    Returns:
        Dict con información de red
    """
    return {
        'hostname': get_hostname(),
        'fqdn': get_fqdn(),
        'local_ip': get_local_ip(),
        'public_ip': get_public_ip(),
        'dns_servers': get_dns_servers(),
        'internet_connected': check_internet_connection()
    }