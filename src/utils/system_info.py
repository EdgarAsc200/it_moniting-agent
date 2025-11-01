"""
IT Monitoring Agent - System Information Utilities
Funciones para obtener información del sistema de manera unificada
"""

import sys
import os
import platform
import socket
import ctypes
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def get_os_info() -> Dict[str, str]:
    """
    Obtiene información detallada del sistema operativo
    
    Returns:
        Dict con información del OS
    """
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'architecture': platform.architecture()[0],
        'platform': platform.platform()
    }


def get_hostname() -> str:
    """
    Obtiene el nombre del host
    
    Returns:
        Nombre del host
    """
    return platform.node()


def get_platform_info() -> Dict[str, Any]:
    """
    Obtiene información completa de la plataforma
    
    Returns:
        Dict con información completa
    """
    return {
        'hostname': get_hostname(),
        'os': get_os_info(),
        'python_version': get_python_version(),
        'is_admin': is_admin(),
        'uptime': get_uptime()
    }


def get_python_version() -> Dict[str, Any]:
    """
    Obtiene información de la versión de Python
    
    Returns:
        Dict con información de Python
    """
    return {
        'version': sys.version,
        'version_info': {
            'major': sys.version_info.major,
            'minor': sys.version_info.minor,
            'micro': sys.version_info.micro
        },
        'implementation': platform.python_implementation(),
        'compiler': platform.python_compiler()
    }


def is_admin() -> bool:
    """
    Verifica si el script se está ejecutando con privilegios de administrador
    
    Returns:
        True si tiene privilegios de administrador
    """
    try:
        if platform.system() == 'Windows':
            # Windows: verificar si es administrador
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix/Linux/Mac: verificar si es root (UID 0)
            return os.geteuid() == 0
    except Exception:
        return False


def get_uptime() -> Optional[Dict[str, Any]]:
    """
    Obtiene el tiempo de actividad del sistema
    
    Returns:
        Dict con información de uptime o None si no se puede determinar
    """
    try:
        if platform.system() == 'Windows':
            import ctypes
            
            # GetTickCount64 retorna milisegundos desde el inicio
            lib = ctypes.windll.kernel32
            t = lib.GetTickCount64()
            uptime_seconds = t / 1000.0
            
        elif platform.system() == 'Linux':
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                
        elif platform.system() == 'Darwin':  # macOS
            import subprocess
            
            output = subprocess.check_output(['sysctl', '-n', 'kern.boottime'])
            boot_time_str = output.decode().strip()
            
            # Parse: { sec = 1234567890, usec = 123456 }
            boot_time = int(boot_time_str.split('=')[1].split(',')[0].strip())
            uptime_seconds = (datetime.now() - datetime.fromtimestamp(boot_time)).total_seconds()
            
        else:
            return None
        
        # Convertir a formato legible
        uptime_delta = timedelta(seconds=int(uptime_seconds))
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            'total_seconds': int(uptime_seconds),
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'formatted': f"{days}d {hours}h {minutes}m {seconds}s"
        }
        
    except Exception as e:
        return None


def get_boot_time() -> Optional[datetime]:
    """
    Obtiene la fecha/hora de inicio del sistema
    
    Returns:
        datetime del boot o None si no se puede determinar
    """
    uptime_info = get_uptime()
    
    if uptime_info:
        boot_time = datetime.now() - timedelta(seconds=uptime_info['total_seconds'])
        return boot_time
    
    return None


def get_current_user() -> str:
    """
    Obtiene el usuario actual del sistema
    
    Returns:
        Nombre de usuario
    """
    try:
        if platform.system() == 'Windows':
            return os.environ.get('USERNAME', 'Unknown')
        else:
            import pwd
            return pwd.getpwuid(os.getuid()).pw_name
    except Exception:
        return os.environ.get('USER', 'Unknown')


def get_system_locale() -> Dict[str, str]:
    """
    Obtiene la configuración regional del sistema
    
    Returns:
        Dict con información de locale
    """
    import locale
    
    try:
        system_locale = locale.getdefaultlocale()
        return {
            'language': system_locale[0] or 'Unknown',
            'encoding': system_locale[1] or 'Unknown',
            'full': f"{system_locale[0]}.{system_locale[1]}" if system_locale[0] and system_locale[1] else 'Unknown'
        }
    except Exception:
        return {
            'language': 'Unknown',
            'encoding': 'Unknown',
            'full': 'Unknown'
        }


def get_environment_variables() -> Dict[str, str]:
    """
    Obtiene variables de entorno relevantes (filtrando sensibles)
    
    Returns:
        Dict con variables de entorno seguras
    """
    # Variables que es seguro exponer
    safe_vars = [
        'PATH', 'HOME', 'USER', 'USERNAME', 'SHELL', 'TERM',
        'LANG', 'LC_ALL', 'COMPUTERNAME', 'PROCESSOR_ARCHITECTURE',
        'NUMBER_OF_PROCESSORS', 'OS', 'TEMP', 'TMP'
    ]
    
    env = {}
    for var in safe_vars:
        value = os.environ.get(var)
        if value:
            env[var] = value
    
    return env


def is_64bit() -> bool:
    """
    Verifica si el sistema es de 64 bits
    
    Returns:
        True si es 64 bits
    """
    return platform.machine().endswith('64') or sys.maxsize > 2**32


def get_cpu_count() -> Dict[str, int]:
    """
    Obtiene el número de CPUs
    
    Returns:
        Dict con información de CPUs
    """
    import multiprocessing
    
    return {
        'physical': multiprocessing.cpu_count(),
        'logical': os.cpu_count() or multiprocessing.cpu_count()
    }


def get_system_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen completo del sistema
    
    Returns:
        Dict con resumen completo
    """
    return {
        'hostname': get_hostname(),
        'os': get_os_info(),
        'python': get_python_version(),
        'user': get_current_user(),
        'is_admin': is_admin(),
        'is_64bit': is_64bit(),
        'cpu_count': get_cpu_count(),
        'uptime': get_uptime(),
        'boot_time': get_boot_time().isoformat() if get_boot_time() else None,
        'locale': get_system_locale()
    }


# ═══════════════════════════════════════════════════════════
# FUNCIONES DE COMPATIBILIDAD MULTIPLATAFORMA
# ═══════════════════════════════════════════════════════════

def is_windows() -> bool:
    """Verifica si el sistema es Windows"""
    return platform.system() == 'Windows'


def is_linux() -> bool:
    """Verifica si el sistema es Linux"""
    return platform.system() == 'Linux'


def is_macos() -> bool:
    """Verifica si el sistema es macOS"""
    return platform.system() == 'Darwin'


def is_unix() -> bool:
    """Verifica si el sistema es tipo Unix (Linux o macOS)"""
    return is_linux() or is_macos()


def get_os_type() -> str:
    """
    Retorna un identificador simple del OS
    
    Returns:
        'windows', 'linux', 'macos', o 'unknown'
    """
    system = platform.system()
    
    if system == 'Windows':
        return 'windows'
    elif system == 'Linux':
        return 'linux'
    elif system == 'Darwin':
        return 'macos'
    else:
        return 'unknown'