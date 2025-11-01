"""
IT Monitoring Agent - Data Validators
Funciones para validar diferentes tipos de datos
"""

import re
import ipaddress
from typing import Optional
from urllib.parse import urlparse


def validate_ip(ip: str, version: Optional[int] = None) -> bool:
    """
    Valida una dirección IP (IPv4 o IPv6)
    
    Args:
        ip: Dirección IP a validar
        version: 4 para IPv4, 6 para IPv6, None para cualquiera
        
    Returns:
        True si la IP es válida
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        if version is None:
            return True
        elif version == 4:
            return isinstance(ip_obj, ipaddress.IPv4Address)
        elif version == 6:
            return isinstance(ip_obj, ipaddress.IPv6Address)
        else:
            return False
            
    except ValueError:
        return False


def validate_ipv4(ip: str) -> bool:
    """
    Valida una dirección IPv4
    
    Args:
        ip: Dirección IP a validar
        
    Returns:
        True si es IPv4 válida
    """
    return validate_ip(ip, version=4)


def validate_ipv6(ip: str) -> bool:
    """
    Valida una dirección IPv6
    
    Args:
        ip: Dirección IP a validar
        
    Returns:
        True si es IPv6 válida
    """
    return validate_ip(ip, version=6)


def validate_network(network: str) -> bool:
    """
    Valida una red CIDR (ej: 192.168.1.0/24)
    
    Args:
        network: Red en formato CIDR
        
    Returns:
        True si la red es válida
    """
    try:
        ipaddress.ip_network(network, strict=False)
        return True
    except ValueError:
        return False


def validate_email(email: str) -> bool:
    """
    Valida una dirección de email (validación básica)
    
    Args:
        email: Email a validar
        
    Returns:
        True si el formato es válido
    """
    # Patrón básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_version(version: str) -> bool:
    """
    Valida un número de versión semver (ej: 1.0.0, 2.1.3-beta)
    
    Args:
        version: Versión a validar
        
    Returns:
        True si el formato es válido
    """
    # Patrón semver simplificado
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$'
    return bool(re.match(pattern, version))


def validate_port(port: int) -> bool:
    """
    Valida un número de puerto
    
    Args:
        port: Puerto a validar
        
    Returns:
        True si el puerto es válido (1-65535)
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def validate_url(url: str, require_scheme: bool = True) -> bool:
    """
    Valida una URL
    
    Args:
        url: URL a validar
        require_scheme: Si True, requiere http:// o https://
        
    Returns:
        True si la URL es válida
    """
    try:
        result = urlparse(url)
        
        if require_scheme:
            # Debe tener scheme (http, https, etc.)
            has_scheme = bool(result.scheme)
            has_netloc = bool(result.netloc)
            return has_scheme and has_netloc
        else:
            # Solo verificar que tenga al menos netloc
            return bool(result.netloc) or bool(result.path)
            
    except Exception:
        return False


def is_valid_mac_address(mac: str) -> bool:
    """
    Valida una dirección MAC
    
    Args:
        mac: Dirección MAC a validar
        
    Returns:
        True si la MAC es válida
    """
    # Soporta formatos: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF
    patterns = [
        r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',  # AA:BB:CC:DD:EE:FF
        r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$',  # AA-BB-CC-DD-EE-FF
        r'^[0-9A-Fa-f]{12}$'                       # AABBCCDDEEFF
    ]
    
    return any(bool(re.match(pattern, mac)) for pattern in patterns)


def validate_hostname(hostname: str) -> bool:
    """
    Valida un nombre de host
    
    Args:
        hostname: Hostname a validar
        
    Returns:
        True si el hostname es válido
    """
    if len(hostname) > 255:
        return False
    
    # Patrón de hostname válido
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, hostname))


def validate_domain(domain: str) -> bool:
    """
    Valida un nombre de dominio
    
    Args:
        domain: Dominio a validar
        
    Returns:
        True si el dominio es válido
    """
    if len(domain) > 253:
        return False
    
    # Patrón de dominio
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_uuid(uuid_string: str, version: Optional[int] = None) -> bool:
    """
    Valida un UUID
    
    Args:
        uuid_string: UUID a validar
        version: Versión específica (1-5) o None para cualquiera
        
    Returns:
        True si el UUID es válido
    """
    import uuid
    
    try:
        uuid_obj = uuid.UUID(uuid_string)
        
        if version is None:
            return True
        else:
            return uuid_obj.version == version
            
    except (ValueError, AttributeError):
        return False


def validate_hex_color(color: str) -> bool:
    """
    Valida un código de color hexadecimal (#RRGGBB o #RGB)
    
    Args:
        color: Color a validar
        
    Returns:
        True si el color es válido
    """
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, color))


def validate_phone(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Valida un número de teléfono (validación básica)
    
    Args:
        phone: Número de teléfono
        country_code: Código de país (ej: 'US', 'MX')
        
    Returns:
        True si el formato es válido
    """
    # Eliminar espacios, guiones y paréntesis
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Aceptar +, números y hasta 15 dígitos (estándar internacional)
    pattern = r'^\+?[0-9]{7,15}$'
    return bool(re.match(pattern, clean_phone))


def validate_json_string(json_str: str) -> bool:
    """
    Valida si una cadena es JSON válido
    
    Args:
        json_str: Cadena JSON a validar
        
    Returns:
        True si es JSON válido
    """
    import json
    
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_date(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """
    Valida una fecha en formato específico
    
    Args:
        date_str: Fecha en string
        format: Formato esperado (default: YYYY-MM-DD)
        
    Returns:
        True si la fecha es válida
    """
    from datetime import datetime
    
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_path(path: str) -> bool:
    """
    Valida si un path es sintácticamente válido
    
    Args:
        path: Path a validar
        
    Returns:
        True si el path es válido
    """
    import os
    
    try:
        # Normalizar el path
        normalized = os.path.normpath(path)
        
        # Verificar caracteres inválidos
        invalid_chars = '<>"|?*' if os.name == 'nt' else ''
        
        return not any(char in normalized for char in invalid_chars)
    except Exception:
        return False


def is_safe_filename(filename: str) -> bool:
    """
    Verifica si un nombre de archivo es seguro (sin path traversal, etc.)
    
    Args:
        filename: Nombre de archivo a verificar
        
    Returns:
        True si es seguro
    """
    # No debe contener path separators
    if '/' in filename or '\\' in filename:
        return False
    
    # No debe contener ..
    if '..' in filename:
        return False
    
    # No debe empezar con .
    if filename.startswith('.'):
        return False
    
    # Caracteres prohibidos
    forbidden = '<>:"|?*\x00'
    if any(char in filename for char in forbidden):
        return False
    
    # Longitud razonable
    if len(filename) > 255:
        return False
    
    return True


def validate_sql_identifier(identifier: str) -> bool:
    """
    Valida un identificador SQL (tabla, columna, etc.)
    Útil para prevenir SQL injection
    
    Args:
        identifier: Identificador a validar
        
    Returns:
        True si es seguro
    """
    # Solo letras, números y underscore, no puede empezar con número
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, identifier)) and len(identifier) <= 64


def is_valid_checksum(checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Valida el formato de un checksum
    
    Args:
        checksum: Checksum a validar
        algorithm: Algoritmo usado (md5, sha1, sha256)
        
    Returns:
        True si el formato es válido
    """
    lengths = {
        'md5': 32,
        'sha1': 40,
        'sha256': 64,
        'sha512': 128
    }
    
    expected_length = lengths.get(algorithm.lower())
    
    if expected_length is None:
        return False
    
    # Debe ser hexadecimal de la longitud esperada
    pattern = f'^[a-fA-F0-9]{{{expected_length}}}$'
    return bool(re.match(pattern, checksum))


def validate_cron_expression(cron: str) -> bool:
    """
    Valida una expresión cron (validación básica)
    
    Args:
        cron: Expresión cron (ej: "0 0 * * *")
        
    Returns:
        True si el formato es básicamente válido
    """
    parts = cron.split()
    
    # Debe tener 5 partes (minute hour day month weekday)
    if len(parts) != 5:
        return False
    
    # Cada parte debe ser número, *, o range
    pattern = r'^(\*|[0-9,\-/]+)$'
    return all(bool(re.match(pattern, part)) for part in parts)