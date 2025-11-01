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
def mock_config():
    """Mock de configuración para tests"""
    class MockConfig:
        def __init__(self):
            self._defaults = {
                ('agent', 'id'): '0',
                ('agent', 'name'): 'Test Agent',
                ('agent', 'report_interval'): '300',
                ('api', 'use_mock'): 'true',
                ('api', 'base_url'): 'http://localhost:8000/api',
                ('api', 'timeout'): '30',
                ('api', 'retry_attempts'): '3',
                ('logging', 'level'): 'INFO',
                ('logging', 'file'): 'logs/test_agent.log',
                ('collectors', 'hardware'): 'true',
                ('collectors', 'software'): 'true',
            }
        
        def get(self, section, key, fallback=None):
            """Obtener valor como string"""
            value = self._defaults.get((section, key), fallback)
            return value if value is not None else fallback
        
        def getint(self, section, key, fallback=None):
            """Obtener valor como int"""
            value = self.get(section, key, fallback)
            if value is None:
                return fallback
            try:
                return int(value)
            except (ValueError, TypeError):
                return fallback
        
        def getboolean(self, section, key, fallback=None):
            """Obtener valor como boolean"""
            value = self.get(section, key, fallback)
            if value is None:
                return fallback
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', 'yes', '1', 'on')
        
        def getfloat(self, section, key, fallback=None):
            """Obtener valor como float"""
            value = self.get(section, key, fallback)
            if value is None:
                return fallback
            try:
                return float(value)
            except (ValueError, TypeError):
                return fallback
    
    return MockConfig()


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
