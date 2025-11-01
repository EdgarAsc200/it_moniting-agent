# tests/test_models/test_hardware.py

"""
Tests para el modelo Hardware
"""

import pytest
import time
from datetime import datetime, timedelta
from models import Hardware, HardwareType, HardwareStatus, HardwareComponent


@pytest.mark.unit
class TestHardware:
    """Suite de tests para Hardware"""
    
    def test_create_hardware_basic(self, sample_hardware_data):
        """Test: Crear hardware básico"""
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.DESKTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model']
        )
        
        assert hardware.id == sample_hardware_data['id']
        assert hardware.type == HardwareType.DESKTOP
        assert hardware.manufacturer == sample_hardware_data['manufacturer']
    
    def test_hardware_validation_success(self, sample_hardware_data):
        """Test: Validación exitosa"""
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.LAPTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model']
        )
        
        hardware.validate()  # No debe lanzar excepción
    
    def test_hardware_validation_empty_id(self, sample_hardware_data):
        """Test: Validación falla con ID vacío"""
        hardware = Hardware(
            id='',
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.DESKTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model']
        )
        
        with pytest.raises(ValueError, match="Hardware ID cannot be empty"):
            hardware.validate()
    
    def test_hardware_validation_empty_asset_id(self, sample_hardware_data):
        """Test: Validación falla con asset_id vacío"""
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id='',
            type=HardwareType.DESKTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model']
        )
        
        with pytest.raises(ValueError, match="Asset ID cannot be empty"):
            hardware.validate()
    
    def test_hardware_with_components(self, sample_hardware_data):
        """Test: Hardware con componentes"""
        component = HardwareComponent(
            type='CPU',
            name='Intel Core i7',
            specification='8 cores @ 3.6GHz',
            manufacturer='Intel'
        )
        
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.DESKTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model'],
            components=[component]
        )
        
        assert len(hardware.components) == 1
        assert hardware.components[0].type == 'CPU'
    
    def test_hardware_add_component(self, sample_hardware_data):
        """Test: Agregar componente"""
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.SERVER,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model']
        )
        
        component = HardwareComponent(
            type='RAM',
            name='32GB DDR4',
            specification='32GB @ 3200MHz'
        )
        
        hardware.add_component(component)
        
        assert len(hardware.components) == 1
        assert hardware.components[0].type == 'RAM'
    
    def test_hardware_update_status(self, sample_hardware_data):
        """Test: Actualizar estado"""
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.LAPTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model']
        )
        
        original_status = hardware.status
        original_updated_at = hardware.updated_at
        
        # Pequeño delay para asegurar timestamp diferente
        time.sleep(0.01)
        
        hardware.update_status(HardwareStatus.IN_REPAIR)
        
        assert hardware.status == HardwareStatus.IN_REPAIR
        assert hardware.status != original_status
        assert hardware.updated_at >= original_updated_at
    
    def test_hardware_warranty_check(self, sample_hardware_data):
        """Test: Verificar garantía"""
        # Con garantía vigente
        hardware_valid = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.LAPTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model'],
            warranty_expiry=datetime.now() + timedelta(days=180)
        )
        
        assert hardware_valid.is_under_warranty() is True
        
        # Con garantía vencida
        hardware_expired = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.LAPTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model'],
            warranty_expiry=datetime.now() - timedelta(days=30)
        )
        
        assert hardware_expired.is_under_warranty() is False
    
    def test_hardware_to_dict(self, sample_hardware_data):
        """Test: Convertir a diccionario"""
        hardware = Hardware(
            id=sample_hardware_data['id'],
            asset_id=sample_hardware_data['asset_id'],
            type=HardwareType.LAPTOP,
            manufacturer=sample_hardware_data['manufacturer'],
            model=sample_hardware_data['model'],
            processor=sample_hardware_data['processor'],
            ram_gb=sample_hardware_data['ram_gb'],
            storage_gb=sample_hardware_data['storage_gb']
        )
        
        hw_dict = hardware.to_dict()
        
        assert isinstance(hw_dict, dict)
        assert hw_dict['type'] == 'laptop'
        assert hw_dict['ram_gb'] == 16
        assert hw_dict['storage_gb'] == 512
        assert hw_dict['processor'] == sample_hardware_data['processor']
