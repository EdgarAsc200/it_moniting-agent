# tests/conftest.py

"""
Configuración y fixtures compartidos para todos los tests
"""

import sys
import os
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

import pytest
from datetime import datetime, timedelta
import uuid
import platform


# ═══════════════════════════════════════════════════════════
# FIXTURES PARA MODELOS
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def sample_asset_data():
    """Datos de ejemplo para crear un Asset"""
    return {
        'id': str(uuid.uuid4()),
        'asset_tag': 'IT-TEST-001',
        'name': 'Test Computer',
        'manufacturer': 'Test Manufacturer',
        'model': 'Test Model 2024',
        'serial_number': 'SN123456789'
    }


@pytest.fixture
def sample_hardware_data():
    """Datos de ejemplo para crear Hardware"""
    return {
        'id': str(uuid.uuid4()),
        'asset_id': str(uuid.uuid4()),
        'manufacturer': 'Dell',
        'model': 'OptiPlex 7090',
        'serial_number': 'DELL123456',
        'processor': 'Intel Core i7-10700',
        'ram_gb': 16,
        'storage_gb': 512
    }


@pytest.fixture
def sample_software_data():
    """Datos de ejemplo para crear Software"""
    return {
        'id': str(uuid.uuid4()),
        'asset_id': str(uuid.uuid4()),
        'name': 'Google Chrome',
        'version': '120.0.6099.109',
        'vendor': 'Google LLC'
    }


@pytest.fixture
def sample_collector_output():
    """Salida de ejemplo de un collector"""
    return {
        'report_date': datetime.now().isoformat(),
        'hostname': 'test-computer',
        'operating_system': 'Darwin',
        'os_version': '14.0',
        'architecture': 'arm64',
        'processor': 'Apple M2',
        'processor_cores': 8,
        'total_ram_gb': 16.0,
        'total_disk_gb': 512.0,
        'system_info': {
            'manufacturer': 'Apple',
            'model': 'MacBook Pro',
            'serial_number': 'TESTSERIAL123'
        }
    }


@pytest.fixture
def sample_antivirus_data():
    """Datos de ejemplo para antivirus"""
    return {
        'antivirus_name': 'ESET Security',
        'antivirus_version': '12.1.2057.3',
        'protection_status': 'active',
        'real_time_protection': True,
        'definitions_up_to_date': True,
        'firewall_status': 'active',
        'third_party_antivirus': ['ESET Security'],
        'last_update': datetime.now().isoformat(),
        'last_scan': (datetime.now() - timedelta(hours=2)).isoformat()
    }


@pytest.fixture
def mock_config():
    """Mock de configuración para tests"""
    class MockConfig:
        def __init__(self):
            self._defaults = {
                # Agent
                ('agent', 'id'): '0',
                ('agent', 'name'): 'Test Agent',
                ('agent', 'version'): '1.0.0',
                ('agent', 'report_interval'): '300',
                
                # API
                ('api', 'use_mock'): 'true',
                ('api', 'base_url'): 'http://localhost:8000/api',
                ('api', 'timeout'): '30',
                ('api', 'retry_attempts'): '3',
                ('api', 'verify_ssl'): 'false',
                ('api', 'api_key'): 'test_api_key_123',
                
                # Logging
                ('logging', 'level'): 'INFO',
                ('logging', 'file'): 'logs/test_agent.log',
                
                # Collectors
                ('collectors', 'hardware'): 'true',
                ('collectors', 'software'): 'true',
            }
        
        def get(self, section, key, fallback=None):
            """Obtener valor como string"""
            value = self._defaults.get((section, key))
            return value if value is not None else fallback
        
        def getint(self, section, key, fallback=None):
            """Obtener valor como int"""
            value = self.get(section, key)
            if value is None:
                return fallback
            try:
                return int(value)
            except (ValueError, TypeError):
                return fallback if fallback is not None else 0
        
        def getboolean(self, section, key, fallback=None):
            """Obtener valor como boolean"""
            value = self.get(section, key)
            if value is None:
                return fallback if fallback is not None else False
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', 'yes', '1', 'on')
        
        def getfloat(self, section, key, fallback=None):
            """Obtener valor como float"""
            value = self.get(section, key)
            if value is None:
                return fallback if fallback is not None else 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return fallback if fallback is not None else 0.0
    
    return MockConfig()

# ═══════════════════════════════════════════════════════════
# FIXTURES PARA COLLECTORS (Windows)
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def wmi_security_center():
    """
    Fixture para Windows Security Center 2
    Solo disponible en Windows - se salta automáticamente en otros OS
    """
    if platform.system() != "Windows":
        pytest.skip("WMI solo disponible en Windows")
        return  # Esta línea nunca se ejecuta, pero por claridad
    
    try:
        import wmi
        return wmi.WMI(namespace="root/SecurityCenter2")
    except ImportError:
        pytest.skip("Librería WMI no instalada. Ejecuta: pip install wmi pywin32")
    except Exception as e:
        pytest.skip(f"Error conectando a SecurityCenter2: {e}")

@pytest.fixture(scope="session")
def wmi_root():
    """
    Fixture para WMI root
    Solo disponible en Windows - se salta automáticamente en otros OS
    """
    if platform.system() != "Windows":
        pytest.skip("WMI solo disponible en Windows")
    
    try:
        import wmi
        return wmi.WMI()
    except ImportError:
        pytest.skip("Librería WMI no instalada. Ejecuta: pip install wmi pywin32")
    except Exception as e:
        pytest.skip(f"Error conectando a WMI: {e}")


# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PYTEST
# ═══════════════════════════════════════════════════════════

def pytest_configure(config):
    """Configuración inicial de pytest"""
    config.addinivalue_line(
        "markers", "integration: tests de integración (lentos)"
    )
    config.addinivalue_line(
        "markers", "unit: tests unitarios (rápidos)"
    )
    config.addinivalue_line(
        "markers", "slow: tests que toman mucho tiempo"
    )
    config.addinivalue_line(
        "markers", "windows: tests que solo funcionan en Windows"
    )
    config.addinivalue_line(
        "markers", "antivirus: tests relacionados con antivirus"
    )
    config.addinivalue_line(
        "markers", "collectors: tests de recolectores de datos"
    )