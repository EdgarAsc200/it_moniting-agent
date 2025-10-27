"""
Clase base abstracta para todos los collectors
"""

from abc import ABC, abstractmethod
import logging


class BaseCollector(ABC):
    """
    Clase base abstracta para todos los collectors de datos
    """
    
    def __init__(self):
        """
        Inicializa el collector base
        """
        self.logger = logging.getLogger(f'ITAgent.{self.__class__.__name__}')
    
    @abstractmethod
    def collect(self):
        """
        Método abstracto que debe implementar cada collector
        
        Returns:
            dict: Datos recopilados
        """
        pass
    
    def safe_collect(self):
        """
        Ejecuta collect() con manejo de errores
        
        Returns:
            dict: Datos recopilados o dict vacío si hay error
        """
        try:
            self.logger.debug(f"Iniciando recopilación de {self.__class__.__name__}")
            data = self.collect()
            self.logger.debug(f"✓ Recopilación exitosa de {self.__class__.__name__}")
            return data
        except Exception as e:
            self.logger.error(f"Error en {self.__class__.__name__}: {e}", exc_info=True)
            return {}