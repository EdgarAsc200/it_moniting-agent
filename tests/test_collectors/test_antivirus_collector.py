# tests/test_collectors/test_antivirus_collector.py

"""
Tests para AntivirusCollector
"""

import pytest
from collectors.antivirus_collector import AntivirusCollector


@pytest.mark.unit
class TestAntivirusCollector:
    """Suite de tests para AntivirusCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = AntivirusCollector()
        assert collector is not None
        assert collector.os_type is not None
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = AntivirusCollector()
        data = collector.collect()
        
        assert isinstance(data, dict)
        # Los campos varían según el OS, verificar estructura básica
        assert len(data) > 0
    
    def test_collect_structure(self):
        """Test: Estructura básica del resultado"""
        collector = AntivirusCollector()
        data = collector.collect()
        
        # Debe tener al menos algún campo relacionado con antivirus/seguridad
        assert isinstance(data, dict)
        assert len(data) > 0
