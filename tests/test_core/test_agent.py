# tests/test_core/test_agent.py

"""
Tests para Agent
"""

import pytest
from core.agent import Agent


@pytest.mark.unit
class TestAgent:
    """Suite de tests para Agent"""
    
    def test_agent_initialization(self, mock_config):
        """Test: Inicializar agent"""
        agent = Agent(mock_config)
        
        assert agent is not None
        assert agent.hostname is not None
        assert agent.os_type is not None
        assert len(agent.collectors) > 0
    
    def test_agent_has_collectors(self, mock_config):
        """Test: Agent tiene collectors"""
        agent = Agent(mock_config)
        
        assert 'hardware' in agent.collectors
        assert 'software' in agent.collectors
    
    def test_agent_collect_all_data(self, mock_config):
        """Test: Recolectar todos los datos"""
        agent = Agent(mock_config)
        
        data = agent.collect_all_data()
        
        assert isinstance(data, dict)
        assert 'timestamp' in data
        assert 'hostname' in data
        assert 'hardware' in data
    
    @pytest.mark.slow
    def test_agent_collect_as_models(self, mock_config):
        """Test: Recolectar con modelos"""
        agent = Agent(mock_config)
        
        asset, hardware, software_list, raw_data = agent.collect_as_models(
            location='Test',
            department='IT'
        )
        
        assert asset is not None
        assert hardware is not None
        assert isinstance(software_list, list)
        assert isinstance(raw_data, dict)
    
    def test_agent_get_status(self, mock_config):
        """Test: Obtener estado básico del agent"""
        agent = Agent(mock_config)
        
        status = agent.get_status()
        
        assert isinstance(status, dict)
        assert 'version' in status
        assert 'hostname' in status
        assert 'collectors' in status
        # scheduler_running es opcional pero debe estar presente
        assert 'scheduler_running' in status
