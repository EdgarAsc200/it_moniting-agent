# tests/test_collectors/test_office_collector.py

"""
Tests para OfficeCollector
"""

import pytest
from collectors.office_collector import OfficeCollector


@pytest.mark.unit
class TestOfficeCollector:
    """Suite de tests para OfficeCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = OfficeCollector()
        assert collector is not None
        assert collector.os_type is not None
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = OfficeCollector()
        data = collector.collect()
        
        assert isinstance(data, dict)
        # Verificar estructura básica
        assert len(data) > 0
