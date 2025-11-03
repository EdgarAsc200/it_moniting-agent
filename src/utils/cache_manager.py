# src/utils/cache_manager.py

"""
Sistema de gestión de cache para datos temporales
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import hashlib


class CacheManager:
    """Gestor de cache para datos temporales"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración por defecto
        self.max_age_hours = 24  # Tiempo máximo de vida del cache
        self.max_size_mb = 100   # Tamaño máximo del cache
    
    def set(self, key: str, data: Any, ttl_hours: int = None) -> bool:
        """
        Guardar datos en cache
        
        Args:
            key: Clave única para identificar los datos
            data: Datos a cachear (debe ser serializable a JSON)
            ttl_hours: Tiempo de vida en horas (None = usar default)
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            cache_file = self._get_cache_file(key)
            
            # Preparar metadata
            ttl = ttl_hours if ttl_hours is not None else self.max_age_hours
            expires_at = datetime.now() + timedelta(hours=ttl)
            
            cache_data = {
                'key': key,
                'data': data,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'ttl_hours': ttl
            }
            
            # Guardar
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"⚠️  Error guardando en cache: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener datos del cache
        
        Args:
            key: Clave de los datos
        
        Returns:
            Los datos cacheados o None si no existen/expiraron
        """
        try:
            cache_file = self._get_cache_file(key)
            
            if not cache_file.exists():
                return None
            
            # Leer datos
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar expiración
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            
            if datetime.now() > expires_at:
                # Cache expirado, eliminar
                cache_file.unlink()
                return None
            
            return cache_data['data']
        
        except Exception as e:
            print(f"⚠️  Error leyendo cache: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Eliminar entrada del cache"""
        try:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"⚠️  Error eliminando cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Verificar si una clave existe y no ha expirado"""
        return self.get(key) is not None
    
    def clear(self) -> int:
        """
        Limpiar todo el cache
        
        Returns:
            int: Número de archivos eliminados
        """
        try:
            count = 0
            for file in self.cache_dir.glob('*.json'):
                file.unlink()
                count += 1
            return count
        except Exception as e:
            print(f"⚠️  Error limpiando cache: {e}")
            return 0
    
    def cleanup_expired(self) -> int:
        """
        Limpiar entradas expiradas
        
        Returns:
            int: Número de archivos eliminados
        """
        try:
            count = 0
            for file in self.cache_dir.glob('*.json'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(cache_data['expires_at'])
                    
                    if datetime.now() > expires_at:
                        file.unlink()
                        count += 1
                except:
                    # Si hay error leyendo, eliminar el archivo corrupto
                    file.unlink()
                    count += 1
            
            return count
        except Exception as e:
            print(f"⚠️  Error en cleanup: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        try:
            files = list(self.cache_dir.glob('*.json'))
            total_size = sum(f.stat().st_size for f in files)
            
            expired = 0
            valid = 0
            
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(cache_data['expires_at'])
                    
                    if datetime.now() > expires_at:
                        expired += 1
                    else:
                        valid += 1
                except:
                    expired += 1
            
            return {
                'total_entries': len(files),
                'valid_entries': valid,
                'expired_entries': expired,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir)
            }
        except Exception as e:
            print(f"⚠️  Error obteniendo stats: {e}")
            return {}
    
    def _get_cache_file(self, key: str) -> Path:
        """Generar ruta de archivo para una clave"""
        # Crear hash de la clave para nombre de archivo seguro
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"cache_{key_hash}.json"
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """Listar todas las claves en el cache"""
        keys = []
        
        for file in self.cache_dir.glob('*.json'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                expires_at = datetime.fromisoformat(cache_data['expires_at'])
                created_at = datetime.fromisoformat(cache_data['created_at'])
                
                keys.append({
                    'key': cache_data['key'],
                    'created_at': created_at,
                    'expires_at': expires_at,
                    'expired': datetime.now() > expires_at,
                    'size_kb': round(file.stat().st_size / 1024, 2)
                })
            except:
                continue
        
        return keys


# CLI de prueba
if __name__ == "__main__":
    cache = CacheManager()
    
    # Ejemplo de uso
    print("📦 Cache Manager Demo\n")
    
    # Guardar datos
    print("1. Guardando datos en cache...")
    cache.set('test_data', {'name': 'Test', 'value': 123}, ttl_hours=1)
    cache.set('inventory', {'hardware': 'data', 'software': 'data'}, ttl_hours=24)
    
    # Leer datos
    print("2. Leyendo datos...")
    data = cache.get('test_data')
    print(f"   Datos: {data}")
    
    # Estadísticas
    print("\n3. Estadísticas del cache:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Listar claves
    print("\n4. Claves en cache:")
    keys = cache.list_keys()
    for key_info in keys:
        print(f"   • {key_info['key']} - {key_info['size_kb']} KB")
