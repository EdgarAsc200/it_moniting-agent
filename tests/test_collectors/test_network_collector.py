# tests/test_collectors/test_network_collector.py

"""
Tests para NetworkCollector
"""

import pytest
from collectors.network_collector import NetworkCollector


@pytest.mark.unit
class TestNetworkCollector:
    """Suite de tests para NetworkCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = NetworkCollector()
        assert collector is not None
        assert collector.os_type is not None
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = NetworkCollector()
        data = collector.collect()
        
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_collect_has_interfaces(self):
        """Test: Debe detectar interfaces de red"""
        collector = NetworkCollector()
        data = collector.collect()
        
        # Todo sistema tiene al menos una interfaz de red
        assert 'interfaces' in data or 'network_interfaces' in data
