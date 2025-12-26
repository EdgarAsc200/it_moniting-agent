# tests/test_core/test_api_client.py
"""
Tests para el cliente de API
"""

import pytest
from src.core.api_client import APIClient


@pytest.fixture
def api_client(mock_config):
    """Fixture para crear un cliente API"""
    return APIClient(mock_config)


@pytest.mark.unit
class TestAPIClientInitialization:
    """Tests de inicialización del cliente API"""
    
    def test_create_api_client(self, api_client):
        """Test: Crear cliente API con configuración"""
        assert api_client is not None
        print("\n✅ Cliente API creado")
    
    def test_has_required_attributes(self, api_client):
        """Test: Verificar que tiene los atributos del __init__"""
        # Atributos del constructor
        assert hasattr(api_client, 'config')
        assert hasattr(api_client, 'logger')
        assert hasattr(api_client, 'base_url')
        assert hasattr(api_client, 'timeout')
        assert hasattr(api_client, 'verify_ssl')
        assert hasattr(api_client, 'api_key')
        assert hasattr(api_client, 'agent_id')
        assert hasattr(api_client, 'ssl_context')
        
        print("\n✅ Todos los atributos requeridos están presentes")
    
    def test_configuration_loaded(self, api_client):
        """Test: Verificar que la configuración se cargó correctamente"""
        # Verificar valores del mock_config
        assert api_client.base_url == 'http://localhost:8000/api'
        assert api_client.timeout == 30
        assert api_client.verify_ssl is False
        assert api_client.agent_id == 0
        
        print(f"\n✅ Configuración cargada correctamente")
        print(f"   base_url: {api_client.base_url}")
        print(f"   timeout: {api_client.timeout}s")
        print(f"   verify_ssl: {api_client.verify_ssl}")
        print(f"   agent_id: {api_client.agent_id}")
    
    def test_ssl_context_created(self, api_client):
        """Test: Verificar que el contexto SSL se creó"""
        import ssl
        assert api_client.ssl_context is not None
        assert isinstance(api_client.ssl_context, ssl.SSLContext)
        
        print("\n✅ Contexto SSL creado correctamente")


@pytest.mark.unit
class TestAPIClientMethods:
    """Tests de métodos del cliente API"""
    
    def test_has_public_methods(self, api_client):
        """Test: Verificar que tiene los métodos públicos esperados"""
        # Métodos que vimos en el código
        assert hasattr(api_client, 'register_agent')
        assert callable(api_client.register_agent)
        
        print("\n✅ Métodos públicos disponibles:")
        print("   - register_agent()")
    
    def test_has_private_methods(self, api_client):
        """Test: Verificar métodos privados auxiliares"""
        assert hasattr(api_client, '_setup_ssl_context')
        assert hasattr(api_client, '_build_headers')
        assert hasattr(api_client, '_make_request')
        
        print("\n✅ Métodos privados auxiliares presentes")
    
    def test_build_headers(self, api_client):
        """Test: Verificar construcción de headers"""
        headers = api_client._build_headers()
        
        assert 'Content-Type' in headers
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert headers['Content-Type'] == 'application/json'
        assert headers['Accept'] == 'application/json'
        
        # Si hay API key, debe estar en Authorization
        if api_client.api_key:
            assert 'Authorization' in headers
            assert headers['Authorization'].startswith('Bearer ')
        
        print("\n✅ Headers construidos correctamente:")
        for key, value in headers.items():
            if key == 'Authorization' and value:
                print(f"   {key}: Bearer ***")
            else:
                print(f"   {key}: {value}")


@pytest.mark.unit
@pytest.mark.skip(reason="Requiere mock del servidor - implementar con unittest.mock")
class TestAPIClientRegistration:
    """Tests de registro de agente - REQUIERE MOCKING"""
    
    def test_register_agent_structure(self, api_client):
        """Test: Verificar estructura del método register_agent"""
        import inspect
        
        # Verificar firma del método
        sig = inspect.signature(api_client.register_agent)
        params = list(sig.parameters.keys())
        
        # Debe tener el parámetro registration_data
        assert 'registration_data' in params
        
        print(f"\n✅ Firma del método: register_agent{sig}")
    
    def test_register_agent_mock(self, api_client):
        """Test: Llamar register_agent con datos de prueba (requiere mock)"""
        # TODO: Implementar con unittest.mock para simular respuesta HTTP
        # from unittest.mock import patch
        # with patch('urllib.request.urlopen') as mock_urlopen:
        #     mock_response = ...
        #     success, agent_id = api_client.register_agent({'hostname': 'test'})
        #     assert success is True
        pass


@pytest.mark.integration
@pytest.mark.skip(reason="Test de integración - requiere servidor real")
class TestAPIClientIntegration:
    """Tests de integración - REQUIEREN SERVIDOR REAL"""
    
    def test_register_agent_integration(self, api_client):
        """Test de integración: Registrar agente con servidor real"""
        # Este test solo funciona con un servidor real corriendo
        registration_data = {
            'hostname': 'test-computer',
            'operating_system': 'Darwin',
            'agent_version': '1.0.0'
        }
        
        # Esto fallará si no hay servidor
        # success, agent_id = api_client.register_agent(registration_data)
        # assert success is True
        # assert agent_id is not None
        pass