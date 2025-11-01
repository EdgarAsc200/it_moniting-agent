# tests/test_collectors/test_domain_collector.py

"""
Tests para DomainCollector
"""

import pytest
from collectors.domain_collector import DomainCollector


@pytest.mark.unit
class TestDomainCollector:
    """Suite de tests para DomainCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = DomainCollector()
        assert collector is not None
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = DomainCollector()
        data = collector.collect()
        
        assert isinstance(data, dict)
        assert 'is_domain_joined' in data
    
    def test_collect_domain_fields(self):
        """Test: Campos de dominio"""
        collector = DomainCollector()
        data = collector.collect()
        
        assert isinstance(data['is_domain_joined'], bool)
        
        if data['is_domain_joined']:
            assert 'domain_name' in data
