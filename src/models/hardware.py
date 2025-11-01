# src/models/hardware.py

"""
Modelo Hardware con componentes y validación
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class HardwareType(Enum):
    """Tipos de hardware"""
    DESKTOP = "desktop"
    LAPTOP = "laptop"
    SERVER = "server"
    NETWORK = "network"
    MOBILE = "mobile"
    TABLET = "tablet"
    PERIPHERAL = "peripheral"
    OTHER = "other"


class HardwareStatus(Enum):
    """Estados del hardware"""
    OPERATIONAL = "operational"
    IN_REPAIR = "in_repair"
    MAINTENANCE = "maintenance"
    OBSOLETE = "obsolete"
    RETIRED = "retired"


@dataclass
class HardwareComponent:
    """Componente individual del hardware"""
    type: str
    name: str
    specification: str
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    
    def validate(self) -> None:
        """Validar componente"""
        if not self.type or not self.type.strip():
            raise ValueError("Component type cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Component name cannot be empty")


@dataclass
class Hardware:
    """Modelo de Hardware con componentes y especificaciones"""
    
    # Identificación
    id: str
    asset_id: str
    type: HardwareType
    
    # Información básica
    manufacturer: str
    model: str
    serial_number: Optional[str] = None
    
    # Especificaciones principales
    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    
    # Componentes adicionales
    components: List[HardwareComponent] = field(default_factory=list)
    
    # Estado y ubicación
    status: HardwareStatus = HardwareStatus.OPERATIONAL
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    
    # Garantía y mantenimiento
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    
    # Especificaciones técnicas completas
    specifications: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> None:
        """Validar el hardware"""
        # Validar campos requeridos
        if not self.id or not self.id.strip():
            raise ValueError("Hardware ID cannot be empty")
        
        if not self.asset_id or not self.asset_id.strip():
            raise ValueError("Asset ID cannot be empty")
        
        if not self.manufacturer or not self.manufacturer.strip():
            raise ValueError("Manufacturer cannot be empty")
        
        if not self.model or not self.model.strip():
            raise ValueError("Model cannot be empty")
        
        # Validar tipo
        if not isinstance(self.type, HardwareType):
            raise ValueError(f"Invalid hardware type: {self.type}")
        
        # Validar estado
        if not isinstance(self.status, HardwareStatus):
            raise ValueError(f"Invalid hardware status: {self.status}")
        
        # Validar especificaciones numéricas
        if self.ram_gb is not None and self.ram_gb <= 0:
            raise ValueError("RAM must be positive")
        
        if self.storage_gb is not None and self.storage_gb <= 0:
            raise ValueError("Storage must be positive")
        
        # Validar fechas
        if self.warranty_expiry and self.purchase_date:
            if self.warranty_expiry < self.purchase_date:
                raise ValueError("Warranty expiry cannot be before purchase date")
        
        if self.last_maintenance and self.purchase_date:
            if self.last_maintenance < self.purchase_date:
                raise ValueError("Last maintenance cannot be before purchase date")
        
        # Validar componentes
        for component in self.components:
            component.validate()
    
    def add_component(self, component: HardwareComponent) -> None:
        """Agregar componente al hardware"""
        component.validate()
        self.components.append(component)
        self.updated_at = datetime.now()
    
    def update_status(self, new_status: HardwareStatus) -> None:
        """Actualizar estado del hardware"""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def is_under_warranty(self) -> bool:
        """Verificar si está bajo garantía"""
        if not self.warranty_expiry:
            return False
        return datetime.now() < self.warranty_expiry
    
    def needs_maintenance(self, days: int = 90) -> bool:
        """Verificar si necesita mantenimiento"""
        if not self.last_maintenance:
            return True
        
        days_since_maintenance = (datetime.now() - self.last_maintenance).days
        return days_since_maintenance > days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'type': self.type.value,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'processor': self.processor,
            'ram_gb': self.ram_gb,
            'storage_gb': self.storage_gb,
            'components': [
                {
                    'type': c.type,
                    'name': c.name,
                    'specification': c.specification,
                    'manufacturer': c.manufacturer,
                    'serial_number': c.serial_number
                }
                for c in self.components
            ],
            'status': self.status.value,
            'location': self.location,
            'assigned_to': self.assigned_to,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'specifications': self.specifications,
            'notes': self.notes,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }