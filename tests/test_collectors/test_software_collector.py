# tests/test_collectors/test_software_collector.py

"""
Tests para SoftwareCollector
"""

import pytest
from collectors.software_collector import SoftwareCollector
from models import Software, SoftwareType


@pytest.mark.unit
class TestSoftwareCollector:
    """Suite de tests para SoftwareCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = SoftwareCollector()
        assert collector is not None
        assert collector.os_type is not None
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = SoftwareCollector()
        data = collector.collect()
        
        assert isinstance(data, dict)
        assert 'total_software' in data
        assert 'installed_software' in data
        assert isinstance(data['installed_software'], list)
    
    def test_collect_software_structure(self):
        """Test: Estructura de software instalado"""
        collector = SoftwareCollector()
        data = collector.collect()
        
        software_list = data['installed_software']
        
        # Debe haber al menos algunos programas
        assert isinstance(data['total_software'], int)
        assert data['total_software'] >= 0
        
        # Si hay software, verificar estructura
        if len(software_list) > 0:
            first_sw = software_list[0]
            assert 'software_name' in first_sw
            assert isinstance(first_sw['software_name'], str)
    
    @pytest.mark.slow
    def test_collect_has_software(self):
        """Test: El sistema tiene software instalado"""
        collector = SoftwareCollector()
        data = collector.collect()
        
        # En un sistema real siempre hay software
        assert data['total_software'] > 0
        assert len(data['installed_software']) > 0
    
    # ═══════════════════════════════════════════════════════════
    # TESTS PARA MÉTODOS CON MODELOS
    # ═══════════════════════════════════════════════════════════
    
    def test_collect_as_models_returns_list(self):
        """Test: collect_as_models() retorna lista de Software"""
        collector = SoftwareCollector()
        test_asset_id = "test-asset-123"
        
        software_list = collector.collect_as_models(asset_id=test_asset_id)
        
        assert isinstance(software_list, list)
        # Si hay software, verificar que sean instancias válidas
        if len(software_list) > 0:
            assert isinstance(software_list[0], Software)
            assert software_list[0].asset_id == test_asset_id
    
    def test_software_models_have_types(self):
        """Test: Software tiene tipos asignados"""
        collector = SoftwareCollector()
        software_list = collector.collect_as_models(asset_id="test-123")
        
        if len(software_list) > 0:
            for sw in software_list:
                assert isinstance(sw.software_type, SoftwareType)
                assert sw.id is not None
                assert sw.name is not None
    
    def test_software_models_validated(self):
        """Test: Modelos de software están validados"""
        collector = SoftwareCollector()
        software_list = collector.collect_as_models(asset_id="test-123")
        
        # Todos deben estar validados
        for sw in software_list:
            sw.validate()  # No debe lanzar excepción
    
    def test_detect_software_type_security(self):
        """Test: Detectar software de seguridad"""
        collector = SoftwareCollector()
        
        assert collector._detect_software_type("Antivirus Pro") == SoftwareType.SECURITY
        assert collector._detect_software_type("Windows Defender") == SoftwareType.SECURITY
        assert collector._detect_software_type("Firewall Plus") == SoftwareType.SECURITY
    
    def test_detect_software_type_development(self):
        """Test: Detectar software de desarrollo"""
        collector = SoftwareCollector()
        
        assert collector._detect_software_type("Visual Studio Code") == SoftwareType.DEVELOPMENT
        assert collector._detect_software_type("Python 3.9") == SoftwareType.DEVELOPMENT
        assert collector._detect_software_type("Git") == SoftwareType.DEVELOPMENT
        assert collector._detect_software_type("Node.js") == SoftwareType.DEVELOPMENT
    
    def test_detect_software_type_productivity(self):
        """Test: Detectar software de productividad"""
        collector = SoftwareCollector()
        
        assert collector._detect_software_type("Microsoft Office") == SoftwareType.PRODUCTIVITY
        assert collector._detect_software_type("Adobe Photoshop") == SoftwareType.PRODUCTIVITY
        assert collector._detect_software_type("Word") == SoftwareType.PRODUCTIVITY
    
    def test_detect_software_type_system(self):
        """Test: Detectar software de sistema"""
        collector = SoftwareCollector()
        
        assert collector._detect_software_type("Microsoft .NET Framework") == SoftwareType.SYSTEM
        assert collector._detect_software_type("Visual C++ Redistributable") == SoftwareType.SYSTEM
        assert collector._detect_software_type("Runtime Environment") == SoftwareType.SYSTEM
    
    def test_detect_software_type_default(self):
        """Test: Tipo por defecto para software desconocido"""
        collector = SoftwareCollector()
        
        assert collector._detect_software_type("Random App 2024") == SoftwareType.APPLICATION
        assert collector._detect_software_type("Unknown Software") == SoftwareType.APPLICATION
    
    def test_parse_install_date_yyyymmdd(self):
        """Test: Parsear fecha formato YYYYMMDD"""
        collector = SoftwareCollector()
        
        date = collector._parse_install_date("20240115")
        
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15
    
    def test_parse_install_date_invalid(self):
        """Test: Fecha inválida retorna None"""
        collector = SoftwareCollector()
        
        assert collector._parse_install_date("invalid") is None
        assert collector._parse_install_date("") is None
        assert collector._parse_install_date(None) is None
    
    def test_command_exists(self):
        """Test: Verificar si comando existe"""
        collector = SoftwareCollector()
        
        # Comandos que deberían existir en cualquier sistema
        assert collector._command_exists("ls") or collector._command_exists("dir")
