# tests/test_models/test_software.py

"""
Tests para el modelo Software
"""

import pytest
from datetime import datetime, timedelta
from models import Software, SoftwareType, SoftwareLicense, LicenseType, LicenseStatus


@pytest.mark.unit
class TestSoftware:
    """Suite de tests para Software"""
    
    def test_create_software_basic(self, sample_software_data):
        """Test: Crear software básico"""
        software = Software(
            id=sample_software_data['id'],
            asset_id=sample_software_data['asset_id'],
            name=sample_software_data['name'],
            version=sample_software_data['version'],
            vendor=sample_software_data['vendor']
        )
        
        assert software.name == sample_software_data['name']
        assert software.version == sample_software_data['version']
        assert software.vendor == sample_software_data['vendor']
    
    def test_software_validation_success(self, sample_software_data):
        """Test: Validación exitosa"""
        software = Software(
            id=sample_software_data['id'],
            asset_id=sample_software_data['asset_id'],
            name=sample_software_data['name']
        )
        
        software.validate()  # No debe lanzar excepción
    
    def test_software_validation_empty_id(self, sample_software_data):
        """Test: Validación falla con ID vacío"""
        software = Software(
            id='',
            asset_id=sample_software_data['asset_id'],
            name=sample_software_data['name']
        )
        
        with pytest.raises(ValueError, match="Software ID cannot be empty"):
            software.validate()
    
    def test_software_with_license(self, sample_software_data):
        """Test: Software con licencia"""
        license = SoftwareLicense(
            license_type=LicenseType.PERPETUAL,
            license_key='XXXX-XXXX-XXXX-XXXX',
            license_status=LicenseStatus.ACTIVE
        )
        
        software = Software(
            id=sample_software_data['id'],
            asset_id=sample_software_data['asset_id'],
            name='Microsoft Office',
            license=license
        )
        
        assert software.license is not None
        assert software.license.license_type == LicenseType.PERPETUAL
        assert software.is_licensed() is True
    
    def test_software_add_license(self, sample_software_data):
        """Test: Agregar licencia"""
        software = Software(
            id=sample_software_data['id'],
            asset_id=sample_software_data['asset_id'],
            name=sample_software_data['name']
        )
        
        license = SoftwareLicense(
            license_type=LicenseType.SUBSCRIPTION,
            license_status=LicenseStatus.ACTIVE
        )
        
        software.add_license(license)
        
        assert software.license is not None
        assert software.license.license_type == LicenseType.SUBSCRIPTION
    
    def test_software_license_expired(self, sample_software_data):
        """Test: Licencia vencida"""
        license = SoftwareLicense(
            license_type=LicenseType.SUBSCRIPTION,
            license_status=LicenseStatus.EXPIRED,
            expiry_date=datetime.now() - timedelta(days=30)
        )
        
        software = Software(
            id=sample_software_data['id'],
            asset_id=sample_software_data['asset_id'],
            name='Test Software',
            license=license
        )
        
        assert software.is_licensed() is False
        assert license.is_expired() is True
    
    def test_software_to_dict(self, sample_software_data):
        """Test: Convertir a diccionario"""
        software = Software(
            id=sample_software_data['id'],
            asset_id=sample_software_data['asset_id'],
            name=sample_software_data['name'],
            version=sample_software_data['version'],
            software_type=SoftwareType.PRODUCTIVITY
        )
        
        sw_dict = software.to_dict()
        
        assert isinstance(sw_dict, dict)
        assert sw_dict['name'] == sample_software_data['name']
        assert sw_dict['software_type'] == 'productivity'
    
    def test_software_all_types(self, sample_software_data):
        """Test: Todos los tipos de software"""
        types = [
            SoftwareType.APPLICATION,
            SoftwareType.SYSTEM,
            SoftwareType.SECURITY,
            SoftwareType.PRODUCTIVITY,
            SoftwareType.DEVELOPMENT
        ]
        
        for sw_type in types:
            software = Software(
                id=sample_software_data['id'],
                asset_id=sample_software_data['asset_id'],
                name=f"Test {sw_type.value}",
                software_type=sw_type
            )
            assert software.software_type == sw_type
