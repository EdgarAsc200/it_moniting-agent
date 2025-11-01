# src/models/__init__.py

"""
Módulo de modelos de datos para IT Monitoring Agent

Este módulo contiene las definiciones de los modelos de datos principales:
- Asset: Modelo base para activos de TI
- Hardware: Especificaciones de hardware
- Software: Información de software instalado con gestión de licencias

Cada modelo incluye validación, métodos utilitarios y serialización.
"""

from .asset import (
    Asset,
    AssetType,
    AssetStatus,
    AssetLocation
)

from .hardware import (
    Hardware,
    HardwareType,
    HardwareStatus,
    HardwareComponent
)

from .software import (
    Software,
    SoftwareType,
    SoftwareLicense,
    LicenseType,
    LicenseStatus
)

# Definir qué se exporta cuando se hace: from models import *
__all__ = [
    # Asset
    'Asset',
    'AssetType',
    'AssetStatus',
    'AssetLocation',
    
    # Hardware
    'Hardware',
    'HardwareType',
    'HardwareStatus',
    'HardwareComponent',
    
    # Software
    'Software',
    'SoftwareType',
    'SoftwareLicense',
    'LicenseType',
    'LicenseStatus',
]

# Versión del módulo
__version__ = '1.0.0'

# Metadata del módulo
__author__ = 'IT Monitoring Team'
__description__ = 'Data models for IT asset management and monitoring'