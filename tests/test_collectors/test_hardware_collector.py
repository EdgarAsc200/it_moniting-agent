# tests/test_collectors/test_hardware_collector.py

"""
Tests para HardwareCollector
"""

import pytest
from collectors.hardware_collector import HardwareCollector
from models import Hardware, Asset, HardwareType, AssetType


@pytest.mark.unit
class TestHardwareCollector:
    """Suite de tests para HardwareCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = HardwareCollector()
        assert collector is not None
        assert collector.os_type is not None
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = HardwareCollector()
        data = collector.collect()
        
        assert isinstance(data, dict)
        assert 'hostname' in data
        assert 'operating_system' in data
        assert 'processor' in data
        assert 'total_ram_gb' in data
        assert 'system_info' in data
    
    def test_collect_hardware_fields(self):
        """Test: Verificar campos específicos de hardware"""
        collector = HardwareCollector()
        data = collector.collect()
        
        # Verificar tipos de datos
        assert isinstance(data['total_ram_gb'], (int, float))
        assert isinstance(data['total_disk_gb'], (int, float))
        assert isinstance(data['processor_cores'], int)
        assert isinstance(data['system_info'], dict)
        
        # Verificar que los valores tienen sentido
        assert data['total_ram_gb'] > 0
        assert data['total_disk_gb'] > 0
        assert data['processor_cores'] > 0
    
    def test_collect_system_info_structure(self):
        """Test: Verificar estructura de system_info"""
        collector = HardwareCollector()
        data = collector.collect()
        
        system_info = data['system_info']
        assert 'manufacturer' in system_info
        assert 'model' in system_info
        assert isinstance(system_info['manufacturer'], str)
        assert isinstance(system_info['model'], str)
    
    # ═══════════════════════════════════════════════════════════
    # TESTS PARA MÉTODOS CON MODELOS
    # ═══════════════════════════════════════════════════════════
    
    def test_collect_as_model_returns_hardware(self):
        """Test: collect_as_model() retorna Hardware"""
        collector = HardwareCollector()
        hardware = collector.collect_as_model()
        
        assert isinstance(hardware, Hardware)
        assert hardware.id is not None
        assert hardware.asset_id is not None
        assert hardware.manufacturer is not None
        assert hardware.model is not None
        assert isinstance(hardware.type, HardwareType)
    
    def test_collect_as_model_with_asset_id(self):
        """Test: collect_as_model() con asset_id específico"""
        collector = HardwareCollector()
        test_asset_id = "test-asset-123"
        
        hardware = collector.collect_as_model(asset_id=test_asset_id)
        
        assert hardware.asset_id == test_asset_id
    
    def test_collect_as_model_has_components(self):
        """Test: Hardware tiene componentes"""
        collector = HardwareCollector()
        hardware = collector.collect_as_model()
        
        assert len(hardware.components) > 0
        # Debe tener al menos CPU
        component_types = [c.type for c in hardware.components]
        assert 'CPU' in component_types
    
    def test_collect_as_model_validated(self):
        """Test: Hardware modelo está validado"""
        collector = HardwareCollector()
        hardware = collector.collect_as_model()
        
        # No debe lanzar excepción
        hardware.validate()
    
    def test_create_asset_returns_asset(self):
        """Test: create_asset() retorna Asset"""
        collector = HardwareCollector()
        asset = collector.create_asset(
            location='Test Location',
            department='IT',
            assigned_to='Test User'
        )
        
        assert isinstance(asset, Asset)
        assert asset.id is not None
        assert asset.asset_tag is not None
        assert asset.department == 'IT'
        assert asset.assigned_to == 'Test User'
        assert isinstance(asset.asset_type, AssetType)
    
    def test_create_asset_with_location(self):
        """Test: Asset con ubicación"""
        collector = HardwareCollector()
        asset = collector.create_asset(location='Building A')
        
        assert asset.location is not None
        assert asset.location.building == 'Building A'
    
    def test_create_asset_without_params(self):
        """Test: Asset sin parámetros opcionales"""
        collector = HardwareCollector()
        asset = collector.create_asset()
        
        assert isinstance(asset, Asset)
        assert asset.location is None
        assert asset.department is None
        assert asset.assigned_to is None
    
    def test_create_asset_validated(self):
        """Test: Asset está validado"""
        collector = HardwareCollector()
        asset = collector.create_asset()
        
        # No debe lanzar excepción
        asset.validate()
    
    def test_determine_hardware_type(self):
        """Test: Determinar tipo de hardware"""
        collector = HardwareCollector()
        
        # Desktop/Laptop por defecto
        assert collector._determine_hardware_type('Windows') == HardwareType.DESKTOP
        assert collector._determine_hardware_type('macOS') == HardwareType.DESKTOP
        assert collector._determine_hardware_type('Linux') == HardwareType.DESKTOP
        
        # Server
        assert collector._determine_hardware_type('Windows Server') == HardwareType.SERVER
