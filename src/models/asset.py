# src/models/asset.py

"""
Modelo Asset - Modelo base para activos de TI
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AssetType(Enum):
    """Tipos de activos"""
    COMPUTER = "computer"
    LAPTOP = "laptop"
    SERVER = "server"
    NETWORK_DEVICE = "network_device"
    PRINTER = "printer"
    MOBILE = "mobile"
    TABLET = "tablet"
    MONITOR = "monitor"
    PERIPHERAL = "peripheral"
    OTHER = "other"


class AssetStatus(Enum):
    """Estados del activo"""
    ACTIVE = "active"
    IN_USE = "in_use"
    AVAILABLE = "available"
    IN_REPAIR = "in_repair"
    RETIRED = "retired"
    DISPOSED = "disposed"
    LOST = "lost"
    STOLEN = "stolen"


@dataclass
class AssetLocation:
    """Ubicación del activo"""
    building: str
    floor: Optional[str] = None
    room: Optional[str] = None
    notes: Optional[str] = None
    
    def validate(self) -> None:
        """Validar ubicación"""
        if not self.building or not self.building.strip():
            raise ValueError("Building cannot be empty")


@dataclass
class Asset:
    """Modelo base de Asset para activos de TI"""
    
    # Identificación
    id: str
    asset_tag: str
    name: str
    asset_type: AssetType
    
    # Estado
    status: AssetStatus = AssetStatus.ACTIVE
    
    # Información básica
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Ubicación y asignación
    location: Optional[AssetLocation] = None
    department: Optional[str] = None
    assigned_to: Optional[str] = None
    
    # Información financiera
    purchase_date: Optional[datetime] = None
    purchase_cost: Optional[float] = None
    warranty_expiry: Optional[datetime] = None
    
    # Descripción y notas
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> None:
        """Validar el asset"""
        # Validar campos requeridos
        if not self.id or not self.id.strip():
            raise ValueError("Asset ID cannot be empty")
        
        if not self.asset_tag or not self.asset_tag.strip():
            raise ValueError("Asset tag cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Asset name cannot be empty")
        
        # Validar tipo
        if not isinstance(self.asset_type, AssetType):
            raise ValueError(f"Invalid asset type: {self.asset_type}")
        
        # Validar estado
        if not isinstance(self.status, AssetStatus):
            raise ValueError(f"Invalid asset status: {self.status}")
        
        # Validar ubicación si existe
        if self.location:
            self.location.validate()
        
        # Validar costos
        if self.purchase_cost is not None and self.purchase_cost < 0:
            raise ValueError("Purchase cost cannot be negative")
        
        # Validar fechas
        if self.warranty_expiry and self.purchase_date:
            if self.warranty_expiry < self.purchase_date:
                raise ValueError("Warranty expiry cannot be before purchase date")
    
    def update_location(self, location: AssetLocation) -> None:
        """Actualizar ubicación del asset"""
        location.validate()
        self.location = location
        self.updated_at = datetime.now()
    
    def assign_to_user(self, user: str, department: str = None) -> None:
        """Asignar asset a un usuario"""
        self.assigned_to = user
        if department:
            self.department = department
        self.status = AssetStatus.IN_USE
        self.updated_at = datetime.now()
    
    def unassign(self) -> None:
        """Desasignar asset"""
        self.assigned_to = None
        self.status = AssetStatus.AVAILABLE
        self.updated_at = datetime.now()
    
    def retire(self) -> None:
        """Retirar asset"""
        self.status = AssetStatus.RETIRED
        self.updated_at = datetime.now()
    
    def is_under_warranty(self) -> bool:
        """Verificar si está bajo garantía"""
        if not self.warranty_expiry:
            return False
        return datetime.now() < self.warranty_expiry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        result = {
            'id': self.id,
            'asset_tag': self.asset_tag,
            'name': self.name,
            'asset_type': self.asset_type.value,
            'status': self.status.value,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'department': self.department,
            'assigned_to': self.assigned_to,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_cost': self.purchase_cost,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'is_under_warranty': self.is_under_warranty(),
            'description': self.description,
            'notes': self.notes,
            'tags': self.tags,
            'custom_fields': self.custom_fields,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        # Agregar ubicación si existe
        if self.location:
            result['location'] = {
                'building': self.location.building,
                'floor': self.location.floor,
                'room': self.location.room,
                'notes': self.location.notes
            }
        else:
            result['location'] = None
        
        return result