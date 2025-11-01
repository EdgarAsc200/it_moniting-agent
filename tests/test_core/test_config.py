# tests/test_core/test_config.py

"""
Tests para Config
"""

import pytest
import tempfile
import os
from pathlib import Path
from core.config import Config


@pytest.mark.unit
class TestConfig:
    """Suite de tests para Config"""
    
    def test_config_with_mock(self, mock_config):
        """Test: Usar mock de configuración"""
        # get() retorna strings, usar getint() para valores numéricos
        assert mock_config.getint('agent', 'id') == 0
        assert mock_config.getboolean('api', 'use_mock') is True
    
    def test_config_get_with_fallback(self, mock_config):
        """Test: Obtener valor con fallback"""
        value = mock_config.get('nonexistent', 'key', fallback='default')
        assert value == 'default'
    
    def test_config_get_existing(self, mock_config):
        """Test: Obtener valor existente"""
        # get() retorna string, usar getint() para valores numéricos
        value = mock_config.getint('agent', 'report_interval')
        assert value == 300
    
    def test_config_getint(self, mock_config):
        """Test: Obtener valor como int"""
        value = mock_config.getint('api', 'timeout')
        assert value == 30
        assert isinstance(value, int)
    
    def test_config_getboolean(self, mock_config):
        """Test: Obtener valor como boolean"""
        value = mock_config.getboolean('api', 'use_mock')
        assert value is True
        assert isinstance(value, bool)
