# tests/test_models/test_asset.py

"""
Tests para el modelo Asset
"""

import pytest
from datetime import datetime, timedelta
from models import Asset, AssetType, AssetStatus, AssetLocation


@pytest.mark.unit
class TestAsset:
    """Suite de tests para Asset"""
    
    def test_create_asset_basic(self, sample_asset_data):
        """Test: Crear un asset básico"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER,
            status=AssetStatus.ACTIVE,
            manufacturer=sample_asset_data['manufacturer'],
            model=sample_asset_data['model']
        )
        
        assert asset.id == sample_asset_data['id']
        assert asset.asset_tag == sample_asset_data['asset_tag']
        assert asset.name == sample_asset_data['name']
        assert asset.asset_type == AssetType.COMPUTER
        assert asset.status == AssetStatus.ACTIVE
    
    def test_asset_validation_success(self, sample_asset_data):
        """Test: Validación exitosa de asset"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.LAPTOP,
            manufacturer=sample_asset_data['manufacturer'],
            model=sample_asset_data['model']
        )
        
        # No debe lanzar excepción
        asset.validate()
    
    def test_asset_validation_empty_id(self, sample_asset_data):
        """Test: Validación falla con ID vacío"""
        asset = Asset(
            id='',
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER
        )
        
        with pytest.raises(ValueError, match="Asset ID cannot be empty"):
            asset.validate()
    
    def test_asset_validation_empty_tag(self, sample_asset_data):
        """Test: Validación falla con tag vacío"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag='',
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER
        )
        
        with pytest.raises(ValueError, match="Asset tag cannot be empty"):
            asset.validate()
    
    def test_asset_validation_empty_name(self, sample_asset_data):
        """Test: Validación falla con nombre vacío"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name='',
            asset_type=AssetType.COMPUTER
        )
        
        with pytest.raises(ValueError, match="Asset name cannot be empty"):
            asset.validate()
    
    def test_asset_with_location(self, sample_asset_data):
        """Test: Asset con ubicación"""
        location = AssetLocation(
            building='Building A',
            floor='2',
            room='201'
        )
        
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER,
            location=location
        )
        
        assert asset.location is not None
        assert asset.location.building == 'Building A'
        assert asset.location.floor == '2'
        assert asset.location.room == '201'
    
    def test_asset_assign_to_user(self, sample_asset_data):
        """Test: Asignar asset a usuario"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.LAPTOP
        )
        
        asset.assign_to_user('John Doe', 'IT Department')
        
        assert asset.assigned_to == 'John Doe'
        assert asset.department == 'IT Department'
        assert asset.status == AssetStatus.IN_USE
    
    def test_asset_unassign(self, sample_asset_data):
        """Test: Desasignar asset"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.LAPTOP,
            assigned_to='John Doe',
            status=AssetStatus.IN_USE
        )
        
        asset.unassign()
        
        assert asset.assigned_to is None
        assert asset.status == AssetStatus.AVAILABLE
    
    def test_asset_retire(self, sample_asset_data):
        """Test: Retirar asset"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER
        )
        
        asset.retire()
        
        assert asset.status == AssetStatus.RETIRED
    
    def test_asset_to_dict(self, sample_asset_data):
        """Test: Convertir asset a diccionario"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.SERVER,
            manufacturer=sample_asset_data['manufacturer'],
            model=sample_asset_data['model']
        )
        
        asset_dict = asset.to_dict()
        
        assert isinstance(asset_dict, dict)
        assert asset_dict['id'] == sample_asset_data['id']
        assert asset_dict['asset_tag'] == sample_asset_data['asset_tag']
        assert asset_dict['asset_type'] == 'server'
        assert 'created_at' in asset_dict
        assert 'updated_at' in asset_dict
    
    def test_asset_warranty_check_valid(self, sample_asset_data):
        """Test: Verificar garantía vigente"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER,
            warranty_expiry=datetime.now() + timedelta(days=30)
        )
        
        assert asset.is_under_warranty() is True
    
    def test_asset_warranty_check_expired(self, sample_asset_data):
        """Test: Verificar garantía vencida"""
        asset = Asset(
            id=sample_asset_data['id'],
            asset_tag=sample_asset_data['asset_tag'],
            name=sample_asset_data['name'],
            asset_type=AssetType.COMPUTER,
            warranty_expiry=datetime.now() - timedelta(days=30)
        )
        
        assert asset.is_under_warranty() is False
    
    def test_asset_all_types(self, sample_asset_data):
        """Test: Verificar todos los tipos de assets"""
        types = [
            AssetType.COMPUTER,
            AssetType.LAPTOP,
            AssetType.SERVER,
            AssetType.NETWORK_DEVICE,
            AssetType.PRINTER
        ]
        
        for asset_type in types:
            asset = Asset(
                id=sample_asset_data['id'],
                asset_tag=f"IT-{asset_type.value.upper()}",
                name=f"Test {asset_type.value}",
                asset_type=asset_type
            )
            assert asset.asset_type == asset_type
