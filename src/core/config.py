"""
Gestor de configuración del agente
"""

import configparser
import os
from pathlib import Path
import logging


class Config:
    """
    Gestiona la configuración del agente desde archivo .ini
    """
    
    def __init__(self, config_file='config/agent.ini'):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_file: Ruta al archivo de configuración
        """
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger('ITAgent.Config')
        
        # Cargar configuración
        self.load()
    
    def load(self):
        """
        Carga la configuración desde el archivo
        """
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Archivo de configuración no encontrado: {self.config_file}\n"
                f"Copia 'config/agent.ini.example' a 'config/agent.ini' y configúralo"
            )
        
        self.config.read(self.config_file, encoding='utf-8')
        self.logger.debug(f"Configuración cargada desde: {self.config_file}")
    
    def get(self, section, key, fallback=None):
        """
        Obtiene un valor de configuración
        
        Args:
            section: Sección del archivo ini
            key: Clave a buscar
            fallback: Valor por defecto si no existe
            
        Returns:
            str: Valor de configuración
        """
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section, key, fallback=0):
        """
        Obtiene un valor entero de configuración
        """
        return self.config.getint(section, key, fallback=fallback)
    
    def getboolean(self, section, key, fallback=False):
        """
        Obtiene un valor booleano de configuración
        """
        return self.config.getboolean(section, key, fallback=fallback)
    
    def set(self, section, key, value):
        """
        Establece un valor de configuración
        
        Args:
            section: Sección del archivo ini
            key: Clave a establecer
            value: Valor a guardar
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
    
    def save(self):
        """
        Guarda la configuración al archivo
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
        
        self.logger.info(f"Configuración guardada en: {self.config_file}")
    
    def validate(self):
        """
        Valida que la configuración tenga los valores mínimos necesarios
        
        Returns:
            bool: True si la configuración es válida
        """
        required_sections = {
            'api': ['url', 'token'],
            'agent': ['report_interval'],
            'logging': ['level', 'file']
        }
        
        errors = []
        
        for section, keys in required_sections.items():
            if not self.config.has_section(section):
                errors.append(f"Falta la sección [{section}]")
                continue
            
            for key in keys:
                if not self.config.has_option(section, key):
                    errors.append(f"Falta la clave '{key}' en la sección [{section}]")
        
        if errors:
            self.logger.error("Errores de configuración:")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
        
        return True
    
    def get_all(self):
        """
        Retorna toda la configuración como diccionario
        
        Returns:
            dict: Configuración completa
        """
        return {section: dict(self.config.items(section)) 
                for section in self.config.sections()}