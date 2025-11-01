"""
IT Monitoring Agent - Data Formatters
Funciones para formatear y presentar datos de manera legible
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union


def format_bytes(bytes_value: Union[int, float], precision: int = 2) -> str:
    """
    Formatea un valor en bytes a una representación legible
    
    Args:
        bytes_value: Valor en bytes
        precision: Decimales a mostrar
        
    Returns:
        String formateado (ej: "1.5 GB")
    """
    if bytes_value < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
    
    bytes_value = float(bytes_value)
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024.0
        unit_index += 1
    
    if unit_index == 0:  # Bytes
        return f"{int(bytes_value)} {units[unit_index]}"
    else:
        return f"{bytes_value:.{precision}f} {units[unit_index]}"


def format_bits(bits_value: Union[int, float], precision: int = 2) -> str:
    """
    Formatea un valor en bits a una representación legible (para velocidades)
    
    Args:
        bits_value: Valor en bits
        precision: Decimales a mostrar
        
    Returns:
        String formateado (ej: "100 Mbps")
    """
    if bits_value < 0:
        return "0 bps"
    
    units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
    
    bits_value = float(bits_value)
    unit_index = 0
    
    while bits_value >= 1000 and unit_index < len(units) - 1:
        bits_value /= 1000.0
        unit_index += 1
    
    if unit_index == 0:  # bps
        return f"{int(bits_value)} {units[unit_index]}"
    else:
        return f"{bits_value:.{precision}f} {units[unit_index]}"


def format_timestamp(
    timestamp: Optional[Union[datetime, float, int, str]] = None,
    format: str = '%Y-%m-%d %H:%M:%S',
    timezone: Optional[str] = None
) -> str:
    """
    Formatea un timestamp a string legible
    
    Args:
        timestamp: Timestamp (datetime, unix timestamp, o ISO string)
        format: Formato de salida
        timezone: Timezone (aún no implementado)
        
    Returns:
        String formateado
    """
    if timestamp is None:
        dt = datetime.now()
    elif isinstance(timestamp, datetime):
        dt = timestamp
    elif isinstance(timestamp, (int, float)):
        # Unix timestamp
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        # Intentar parsear ISO format
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            dt = datetime.now()
    else:
        dt = datetime.now()
    
    return dt.strftime(format)


def format_duration(
    seconds: Union[int, float],
    short: bool = False,
    max_units: int = 2
) -> str:
    """
    Formatea una duración en segundos a formato legible
    
    Args:
        seconds: Duración en segundos
        short: Si True, usa formato abreviado (1d 2h vs 1 day 2 hours)
        max_units: Máximo número de unidades a mostrar
        
    Returns:
        String formateado
    """
    if seconds < 0:
        seconds = 0
    
    seconds = int(seconds)
    
    units = [
        ('year', 'y', 31536000),
        ('month', 'mo', 2592000),
        ('week', 'w', 604800),
        ('day', 'd', 86400),
        ('hour', 'h', 3600),
        ('minute', 'm', 60),
        ('second', 's', 1)
    ]
    
    result = []
    remaining = seconds
    
    for long_name, short_name, divisor in units:
        value = remaining // divisor
        
        if value > 0:
            if short:
                result.append(f"{value}{short_name}")
            else:
                plural = 's' if value > 1 else ''
                result.append(f"{value} {long_name}{plural}")
            
            remaining %= divisor
            
            if len(result) >= max_units:
                break
    
    return ' '.join(result) if result else ('0s' if short else '0 seconds')


def format_percentage(
    value: Union[int, float],
    total: Union[int, float],
    precision: int = 1
) -> str:
    """
    Formatea un valor como porcentaje
    
    Args:
        value: Valor actual
        total: Valor total
        precision: Decimales a mostrar
        
    Returns:
        String formateado (ej: "75.5%")
    """
    if total == 0:
        return "0%"
    
    percentage = (value / total) * 100
    return f"{percentage:.{precision}f}%"


def truncate_string(
    text: str,
    max_length: int = 80,
    suffix: str = '...'
) -> str:
    """
    Trunca un string a una longitud máxima
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca
        
    Returns:
        String truncado
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(
    filename: str,
    replacement: str = '_',
    max_length: int = 255
) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres inválidos
    
    Args:
        filename: Nombre de archivo original
        replacement: Caracter de reemplazo
        max_length: Longitud máxima
        
    Returns:
        Nombre de archivo sanitizado
    """
    # Caracteres prohibidos en nombres de archivo
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    
    # Reemplazar caracteres inválidos
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remover espacios al inicio/fin
    sanitized = sanitized.strip()
    
    # Truncar si es muy largo
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        if ext:
            max_name_length = max_length - len(ext) - 1
            sanitized = f"{name[:max_name_length]}.{ext}"
        else:
            sanitized = sanitized[:max_length]
    
    # No permitir nombres vacíos o solo puntos
    if not sanitized or sanitized.strip('.') == '':
        sanitized = 'unnamed'
    
    return sanitized


def format_phone(
    phone: str,
    country_code: str = 'US',
    format_style: str = 'standard'
) -> str:
    """
    Formatea un número de teléfono
    
    Args:
        phone: Número de teléfono
        country_code: Código de país
        format_style: 'standard', 'dots', 'international'
        
    Returns:
        Número formateado
    """
    # Limpiar el número
    digits = re.sub(r'\D', '', phone)
    
    if country_code == 'US' and len(digits) == 10:
        if format_style == 'standard':
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif format_style == 'dots':
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:]}"
        elif format_style == 'international':
            return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Por defecto, retornar solo los dígitos
    return digits


def format_mac_address(
    mac: str,
    separator: str = ':',
    uppercase: bool = True
) -> str:
    """
    Formatea una dirección MAC a un formato estándar
    
    Args:
        mac: Dirección MAC
        separator: Separador a usar (: o -)
        uppercase: Si True, usa mayúsculas
        
    Returns:
        MAC formateada
    """
    # Remover cualquier separador
    clean_mac = re.sub(r'[:\-\.]', '', mac)
    
    # Validar longitud
    if len(clean_mac) != 12:
        return mac  # Retornar original si inválida
    
    # Separar en pares
    pairs = [clean_mac[i:i+2] for i in range(0, 12, 2)]
    
    # Unir con separador
    formatted = separator.join(pairs)
    
    return formatted.upper() if uppercase else formatted.lower()


def format_list(
    items: list,
    conjunction: str = 'and',
    max_items: Optional[int] = None
) -> str:
    """
    Formatea una lista de items a string legible
    
    Args:
        items: Lista de items
        conjunction: Conjunción a usar ('and' o 'or')
        max_items: Máximo de items a mostrar antes de truncar
        
    Returns:
        String formateado (ej: "item1, item2, and item3")
    """
    if not items:
        return ""
    
    # Convertir a strings
    str_items = [str(item) for item in items]
    
    # Truncar si es necesario
    if max_items and len(str_items) > max_items:
        shown = str_items[:max_items]
        remaining = len(str_items) - max_items
        return f"{', '.join(shown)}, and {remaining} more"
    
    if len(str_items) == 1:
        return str_items[0]
    elif len(str_items) == 2:
        return f"{str_items[0]} {conjunction} {str_items[1]}"
    else:
        return f"{', '.join(str_items[:-1])}, {conjunction} {str_items[-1]}"


def format_number(
    number: Union[int, float],
    decimal_places: int = 0,
    thousands_separator: str = ',',
    decimal_separator: str = '.'
) -> str:
    """
    Formatea un número con separadores de miles
    
    Args:
        number: Número a formatear
        decimal_places: Lugares decimales
        thousands_separator: Separador de miles
        decimal_separator: Separador decimal
        
    Returns:
        Número formateado
    """
    if decimal_places > 0:
        formatted = f"{number:,.{decimal_places}f}"
    else:
        formatted = f"{int(number):,}"
    
    # Reemplazar separadores si son diferentes a los default
    if thousands_separator != ',':
        formatted = formatted.replace(',', thousands_separator)
    if decimal_separator != '.':
        formatted = formatted.replace('.', decimal_separator)
    
    return formatted


def format_currency(
    amount: Union[int, float],
    currency: str = 'USD',
    locale: str = 'en_US'
) -> str:
    """
    Formatea un valor como moneda
    
    Args:
        amount: Cantidad
        currency: Código de moneda (USD, EUR, MXN, etc.)
        locale: Locale a usar
        
    Returns:
        Cantidad formateada
    """
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'MXN': '$',
        'CAD': 'C$',
        'AUD': 'A$'
    }
    
    symbol = symbols.get(currency, currency + ' ')
    formatted_number = format_number(amount, decimal_places=2)
    
    return f"{symbol}{formatted_number}"


def format_address(address_dict: dict) -> str:
    """
    Formatea un diccionario de dirección a string
    
    Args:
        address_dict: Dict con keys: street, city, state, zip, country
        
    Returns:
        Dirección formateada
    """
    parts = []
    
    if 'street' in address_dict:
        parts.append(address_dict['street'])
    
    city_state_zip = []
    if 'city' in address_dict:
        city_state_zip.append(address_dict['city'])
    if 'state' in address_dict:
        city_state_zip.append(address_dict['state'])
    if 'zip' in address_dict:
        city_state_zip.append(address_dict['zip'])
    
    if city_state_zip:
        parts.append(', '.join(city_state_zip))
    
    if 'country' in address_dict:
        parts.append(address_dict['country'])
    
    return '\n'.join(parts)


def humanize_timedelta(td: timedelta) -> str:
    """
    Convierte un timedelta a formato legible humanizado
    
    Args:
        td: timedelta object
        
    Returns:
        String humanizado (ej: "2 hours ago", "in 3 days")
    """
    seconds = td.total_seconds()
    
    if seconds == 0:
        return "just now"
    
    future = seconds > 0
    seconds = abs(seconds)
    
    intervals = [
        ('year', 31536000),
        ('month', 2592000),
        ('week', 604800),
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1)
    ]
    
    for name, count in intervals:
        value = seconds // count
        if value >= 1:
            plural = 's' if value > 1 else ''
            if future:
                return f"in {int(value)} {name}{plural}"
            else:
                return f"{int(value)} {name}{plural} ago"
    
    return "just now"


def format_json_pretty(data: dict, indent: int = 2) -> str:
    """
    Formatea un dict/JSON de manera legible
    
    Args:
        data: Datos a formatear
        indent: Espacios de indentación
        
    Returns:
        JSON formateado
    """
    import json
    return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)