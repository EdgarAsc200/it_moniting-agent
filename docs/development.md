# 👨‍💻 Guía de Desarrollo

Guía para desarrolladores que desean contribuir o extender el IT Monitoring Agent.

## 📋 Tabla de Contenidos

- [Configuración del Entorno](#configuración-del-entorno)
- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Crear Nuevos Collectors](#crear-nuevos-collectors)
- [Crear Nuevos Modelos](#crear-nuevos-modelos)
- [Testing](#testing)
- [Estilo de Código](#estilo-de-código)
- [Contribuir](#contribuir)

---

## 🛠️ Configuración del Entorno

### Requisitos de Desarrollo

- Python 3.9+
- git
- Editor de código (VS Code, PyCharm, etc.)
- pytest (para tests)

### Setup Inicial
```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/it-monitoring-agent.git
cd it-monitoring-agent

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Instalar dependencias de desarrollo
pip install pytest pytest-cov pylint black flake8 mypy

# 6. Ejecutar tests
pytest tests/ -v
```

### Configuración de VS Code

**`.vscode/settings.json`:**
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ]
}
```

---

## 🏗️ Arquitectura del Proyecto

### Estructura de Directorios
```
it_monitoring_agent/
├── src/
│   ├── models/              # Modelos de datos (Asset, Hardware, Software)
│   ├── collectors/          # Recolectores de información
│   ├── core/               # Funcionalidad central
│   │   ├── agent.py        # Clase principal del agente
│   │   ├── config.py       # Gestión de configuración
│   │   ├── api_client.py   # Cliente API
│   │   └── scheduler.py    # Programación de tareas
│   ├── utils/              # Utilidades
│   └── main.py             # Punto de entrada
├── tests/                  # Tests unitarios
├── config/                 # Archivos de configuración
├── data/                   # Datos locales
├── scripts/                # Scripts de instalación
└── docs/                   # Documentación
```

### Flujo de Ejecución
```
main.py
   │
   ├─> Agent.init()
   │     │
   │     ├─> Config.load()
   │     ├─> APIClient.init()
   │     ├─> Collectors.init()
   │     └─> Scheduler.init()
   │
   ├─> Agent.collect_data()
   │     │
   │     ├─> HardwareCollector.collect()
   │     ├─> SoftwareCollector.collect()
   │     ├─> NetworkCollector.collect()
   │     └─> ... otros collectors
   │
   ├─> Agent.create_models()
   │     │
   │     ├─> Asset.from_dict()
   │     ├─> Hardware.from_dict()
   │     └─> Software.from_dict()
   │
   └─> APIClient.send_inventory()
```

---

## 🔧 Crear Nuevos Collectors

### Plantilla de Collector
```python
# src/collectors/my_collector.py

"""
Collector para [descripción]
"""

import platform
from typing import Dict, Any


class MyCollector:
    """Recolecta información de [fuente]"""
    
    def __init__(self):
        """Inicializar collector"""
        self.name = "MyCollector"
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Configurar logger"""
        import logging
        return logging.getLogger(f"ITAgent.{self.name}")
    
    def collect(self) -> Dict[str, Any]:
        """
        Recolectar datos
        
        Returns:
            Dict con los datos recolectados
        """
        try:
            data = {}
            
            # Tu lógica de recolección aquí
            if platform.system() == "Windows":
                data = self._collect_windows()
            elif platform.system() == "Linux":
                data = self._collect_linux()
            elif platform.system() == "Darwin":
                data = self._collect_macos()
            
            self.logger.info(f"{self.name} completed successfully")
            return data
        
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
            return {}
    
    def _collect_windows(self) -> Dict[str, Any]:
        """Recolección específica para Windows"""
        # Implementar
        return {}
    
    def _collect_linux(self) -> Dict[str, Any]:
        """Recolección específica para Linux"""
        # Implementar
        return {}
    
    def _collect_macos(self) -> Dict[str, Any]:
        """Recolección específica para macOS"""
        # Implementar
        return {}


# Ejemplo de uso
if __name__ == "__main__":
    collector = MyCollector()
    data = collector.collect()
    print(data)
```

### Agregar Collector al Agent

**En `src/core/agent.py`:**
```python
from collectors.my_collector import MyCollector

class Agent:
    def __init__(self, config):
        # ... código existente ...
        
        # Agregar tu collector
        self.my_collector = MyCollector()
        
    def collect_all_data(self):
        data = {}
        
        # ... otros collectors ...
        
        # Agregar tu collector
        if self.config.get('Collectors', 'my_collector', fallback='true') == 'true':
            data['my_data'] = self.my_collector.collect()
        
        return data
```

### Test del Collector
```python
# tests/test_collectors/test_my_collector.py

import pytest
from collectors.my_collector import MyCollector


class TestMyCollector:
    """Tests para MyCollector"""
    
    def test_collector_initialization(self):
        """Test: Inicializar collector"""
        collector = MyCollector()
        assert collector is not None
        assert collector.name == "MyCollector"
    
    def test_collect_returns_dict(self):
        """Test: collect() retorna diccionario"""
        collector = MyCollector()
        data = collector.collect()
        assert isinstance(data, dict)
    
    def test_collect_has_expected_fields(self):
        """Test: Verificar campos esperados"""
        collector = MyCollector()
        data = collector.collect()
        
        # Verificar tus campos específicos
        assert 'field1' in data
        assert 'field2' in data
```

---

## 📦 Crear Nuevos Modelos

### Plantilla de Modelo
```python
# src/models/my_model.py

"""
Modelo para [descripción]
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class MyModel:
    """Modelo de datos para [entidad]"""
    
    # Campos requeridos
    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Campos opcionales
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validación después de inicialización"""
        self.validate()
    
    def validate(self):
        """Validar datos del modelo"""
        errors = []
        
        # Validaciones
        if not self.id:
            errors.append("ID es requerido")
        
        if not self.name:
            errors.append("Name es requerido")
        
        if errors:
            raise ValueError(f"Errores de validación: {', '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MyModel':
        """Crear instancia desde diccionario"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description'),
            metadata=data.get('metadata', {})
        )


# Ejemplo de uso
if __name__ == "__main__":
    model = MyModel(
        id="001",
        name="Test Model",
        description="Example"
    )
    
    print(model.to_dict())
```

### Test del Modelo
```python
# tests/test_models/test_my_model.py

import pytest
from models.my_model import MyModel


class TestMyModel:
    """Tests para MyModel"""
    
    def test_create_model(self):
        """Test: Crear modelo básico"""
        model = MyModel(
            id="001",
            name="Test"
        )
        assert model.id == "001"
        assert model.name == "Test"
    
    def test_validation_empty_id(self):
        """Test: Validación de ID vacío"""
        with pytest.raises(ValueError):
            MyModel(id="", name="Test")
    
    def test_to_dict(self):
        """Test: Conversión a diccionario"""
        model = MyModel(id="001", name="Test")
        data = model.to_dict()
        
        assert isinstance(data, dict)
        assert data['id'] == "001"
        assert data['name'] == "Test"
    
    def test_from_dict(self):
        """Test: Crear desde diccionario"""
        data = {
            'id': '001',
            'name': 'Test',
            'description': 'Example'
        }
        model = MyModel.from_dict(data)
        
        assert model.id == '001'
        assert model.name == 'Test'
        assert model.description == 'Example'
```

---

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_collectors/ -v
pytest tests/test_models/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
```

### Estructura de Tests
```python
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_config():
    """Fixture de configuración mock"""
    config = Mock()
    config.get.return_value = 'test_value'
    return config


class TestMyFeature:
    """Suite de tests para MyFeature"""
    
    def test_basic_functionality(self):
        """Test básico"""
        # Arrange
        input_data = "test"
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_output
    
    def test_with_mock(self, mock_config):
        """Test usando fixture"""
        obj = MyClass(mock_config)
        assert obj.config == mock_config
    
    @patch('module.external_call')
    def test_with_patch(self, mock_external):
        """Test con patch"""
        mock_external.return_value = "mocked"
        result = function_that_calls_external()
        assert result == "expected"
```

### Best Practices de Testing

1. **Usar nombres descriptivos:**
```python
   def test_hardware_collector_returns_cpu_info()
   def test_software_collector_detects_installed_packages()
```

2. **Seguir patrón AAA (Arrange-Act-Assert):**
```python
   def test_example():
       # Arrange
       input_data = setup_test_data()
       
       # Act
       result = function_under_test(input_data)
       
       # Assert
       assert result == expected
```

3. **Un assert por test (cuando sea posible)**

4. **Usar fixtures para setup común**

5. **Mockear dependencias externas**

---

## 📝 Estilo de Código

### PEP 8 y Convenciones
```python
# Imports agrupados y ordenados
import os
import sys
from typing import Dict, List, Any

import psutil
import requests

from models.asset import Asset
from collectors.base import BaseCollector


# Constantes en MAYÚSCULAS
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30


# Clases en PascalCase
class MyCollector:
    """Docstring de clase"""
    
    def __init__(self):
        # Variables de instancia en snake_case
        self.retry_count = 0
        self.is_running = False
    
    def my_method(self, param1: str, param2: int) -> Dict[str, Any]:
        """
        Docstring de método
        
        Args:
            param1: Descripción
            param2: Descripción
        
        Returns:
            Descripción del retorno
        """
        # Código aquí
        pass


# Funciones en snake_case
def calculate_total(items: List[int]) -> int:
    """Docstring de función"""
    return sum(items)
```

### Formateo Automático
```bash
# Black (formatter)
black src/ tests/

# isort (ordenar imports)
isort src/ tests/

# flake8 (linter)
flake8 src/ tests/

# pylint (análisis estático)
pylint src/

# mypy (type checking)
mypy src/
```

### Pre-commit Hooks

**`.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

---

## 🤝 Contribuir

### Proceso de Contribución

1. **Fork el repositorio**

2. **Crear rama feature:**
```bash
   git checkout -b feature/mi-nueva-feature
```

3. **Hacer commits descriptivos:**
```bash
   git commit -m "feat: Agregar collector para GPU"
   git commit -m "fix: Corregir detección de RAM en Linux"
   git commit -m "docs: Actualizar guía de instalación"
```

4. **Agregar tests:**
   - Todo código nuevo debe tener tests
   - Mantener cobertura >90%

5. **Ejecutar tests y linters:**
```bash
   pytest tests/ -v
   black src/ tests/
   flake8 src/ tests/
```

6. **Push y crear Pull Request:**
```bash
   git push origin feature/mi-nueva-feature
```

### Convenciones de Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: Nueva funcionalidad
fix: Corrección de bug
docs: Cambios en documentación
style: Formato, punto y coma faltantes, etc
refactor: Refactorización de código
test: Agregar o actualizar tests
chore: Tareas de mantenimiento
```

### Checklist de PR

- [ ] Tests agregados y pasando
- [ ] Documentación actualizada
- [ ] Código formateado (black)
- [ ] Sin errores de linter (flake8)
- [ ] Cobertura de tests >90%
- [ ] CHANGELOG actualizado
- [ ] Commits descriptivos

---

## 📚 Recursos Adicionales

- **Python Style Guide:** https://pep8.org/
- **pytest Documentation:** https://docs.pytest.org/
- **Type Hints:** https://docs.python.org/3/library/typing.html
- **Dataclasses:** https://docs.python.org/3/library/dataclasses.html

---

## 🐛 Debug

### Habilitar Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Usar pdb (Python Debugger)
```python
import pdb

def my_function():
    x = 10
    pdb.set_trace()  # Breakpoint aquí
    y = x * 2
    return y
```

### VS Code Debugging

**`.vscode/launch.json`:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "args": ["--debug"],
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

---

## 📞 Soporte para Desarrolladores

- **GitHub Issues:** https://github.com/tu-usuario/it-monitoring-agent/issues
- **Discussions:** https://github.com/tu-usuario/it-monitoring-agent/discussions
- **Wiki:** https://github.com/tu-usuario/it-monitoring-agent/wiki
