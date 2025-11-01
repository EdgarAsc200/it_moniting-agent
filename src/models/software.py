# src/models/software.py

"""
Modelo Software con validación y gestión de licencias
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SoftwareType(Enum):
    """Tipos de software"""
    APPLICATION = "application"
    SYSTEM = "system"
    DRIVER = "driver"
    UTILITY = "utility"
    DEVELOPMENT = "development"
    SECURITY = "security"
    PRODUCTIVITY = "productivity"
    OTHER = "other"


class LicenseType(Enum):
    """Tipos de licencia"""
    PERPETUAL = "perpetual"
    SUBSCRIPTION = "subscription"
    TRIAL = "trial"
    FREEWARE = "freeware"
    OPEN_SOURCE = "open_source"
    VOLUME = "volume"
    OEM = "oem"
    UNKNOWN = "unknown"


class LicenseStatus(Enum):
    """Estados de la licencia"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TRIAL = "trial"
    GRACE_PERIOD = "grace_period"
    UNLICENSED = "unlicensed"
    UNKNOWN = "unknown"


@dataclass
class SoftwareLicense:
    """Información de licencia del software"""
    license_type: LicenseType
    license_key: Optional[str] = None
    license_status: LicenseStatus = LicenseStatus.UNKNOWN
    license_holder: Optional[str] = None
    purchase_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    seats_total: Optional[int] = None
    seats_used: Optional[int] = None
    
    def validate(self) -> None:
        """Validar licencia"""
        if self.seats_total is not None and self.seats_total <= 0:
            raise ValueError("Total seats must be positive")
        
        if self.seats_used is not None and self.seats_used < 0:
            raise ValueError("Used seats cannot be negative")
        
        if self.seats_total and self.seats_used:
            if self.seats_used > self.seats_total:
                raise ValueError("Used seats cannot exceed total seats")
        
        if self.expiry_date and self.purchase_date:
            if self.expiry_date < self.purchase_date:
                raise ValueError("Expiry date cannot be before purchase date")
    
    def is_expired(self) -> bool:
        """Verificar si la licencia está vencida"""
        if not self.expiry_date:
            return False
        return datetime.now() > self.expiry_date
    
    def days_until_expiry(self) -> Optional[int]:
        """Días hasta el vencimiento"""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.now()
        return delta.days


@dataclass
class Software:
    """Modelo de Software con licencias y detalles de instalación"""
    
    # Identificación
    id: str
    asset_id: str
    name: str
    
    # Información básica
    version: Optional[str] = None
    vendor: Optional[str] = None
    software_type: SoftwareType = SoftwareType.APPLICATION
    
    # Instalación
    install_date: Optional[datetime] = None
    install_path: Optional[str] = None
    install_size_mb: Optional[int] = None
    
    # Licencia
    license: Optional[SoftwareLicense] = None
    
    # Detalles técnicos
    architecture: Optional[str] = None  # x86, x64, ARM
    language: Optional[str] = None
    build_number: Optional[str] = None
    
    # Estado
    is_active: bool = True
    last_used: Optional[datetime] = None
    
    # Información adicional
    description: Optional[str] = None
    website: Optional[str] = None
    support_url: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> None:
        """Validar el software"""
        # Validar campos requeridos
        if not self.id or not self.id.strip():
            raise ValueError("Software ID cannot be empty")
        
        if not self.asset_id or not self.asset_id.strip():
            raise ValueError("Asset ID cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Software name cannot be empty")
        
        # Validar tipo
        if not isinstance(self.software_type, SoftwareType):
            raise ValueError(f"Invalid software type: {self.software_type}")
        
        # Validar tamaño de instalación
        if self.install_size_mb is not None and self.install_size_mb < 0:
            raise ValueError("Install size cannot be negative")
        
        # Validar fechas
        if self.last_used and self.install_date:
            if self.last_used < self.install_date:
                raise ValueError("Last used cannot be before install date")
        
        # Validar licencia si existe
        if self.license:
            self.license.validate()
    
    def add_license(self, license: SoftwareLicense) -> None:
        """Agregar o actualizar licencia"""
        license.validate()
        self.license = license
        self.updated_at = datetime.now()
    
    def is_licensed(self) -> bool:
        """Verificar si tiene licencia válida"""
        if not self.license:
            return False
        return self.license.license_status == LicenseStatus.ACTIVE
    
    def needs_license_renewal(self, days_threshold: int = 30) -> bool:
        """Verificar si necesita renovación de licencia"""
        if not self.license or not self.license.expiry_date:
            return False
        
        days_left = self.license.days_until_expiry()
        if days_left is None:
            return False
        
        return 0 < days_left <= days_threshold
    
    def get_size_gb(self) -> Optional[float]:
        """Obtener tamaño en GB"""
        if self.install_size_mb is None:
            return None
        return round(self.install_size_mb / 1024, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        result = {
            'id': self.id,
            'asset_id': self.asset_id,
            'name': self.name,
            'version': self.version,
            'vendor': self.vendor,
            'software_type': self.software_type.value,
            'install_date': self.install_date.isoformat() if self.install_date else None,
            'install_path': self.install_path,
            'install_size_mb': self.install_size_mb,
            'install_size_gb': self.get_size_gb(),
            'architecture': self.architecture,
            'language': self.language,
            'build_number': self.build_number,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'description': self.description,
            'website': self.website,
            'support_url': self.support_url,
            'notes': self.notes,
            'tags': self.tags,
            'custom_fields': self.custom_fields,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Agregar información de licencia si existe
        if self.license:
            result['license'] = {
                'license_type': self.license.license_type.value,
                'license_key': self.license.license_key,
                'license_status': self.license.license_status.value,
                'license_holder': self.license.license_holder,
                'purchase_date': self.license.purchase_date.isoformat() if self.license.purchase_date else None,
                'expiry_date': self.license.expiry_date.isoformat() if self.license.expiry_date else None,
                'seats_total': self.license.seats_total,
                'seats_used': self.license.seats_used,
                'is_expired': self.license.is_expired(),
                'days_until_expiry': self.license.days_until_expiry()
            }
        else:
            result['license'] = None
        
        return result