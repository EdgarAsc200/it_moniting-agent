# src/utils/backup_manager.py

"""
Sistema de gestión de backups para configuraciones
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import zipfile


class BackupManager:
    """Gestor de backups automáticos"""
    
    def __init__(self, backup_dir: str = "data/backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración
        self.max_backups = 10  # Mantener últimos N backups
        self.compress = True   # Comprimir backups
    
    def create_backup(
        self, 
        source_files: List[str], 
        backup_name: str = None
    ) -> Optional[str]:
        """
        Crear backup de archivos
        
        Args:
            source_files: Lista de archivos a respaldar
            backup_name: Nombre del backup (None = automático con timestamp)
        
        Returns:
            str: Ruta del backup creado o None si falla
        """
        try:
            # Generar nombre del backup
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{timestamp}"
            
            if self.compress:
                backup_file = self.backup_dir / f"{backup_name}.zip"
                return self._create_compressed_backup(source_files, backup_file)
            else:
                backup_folder = self.backup_dir / backup_name
                return self._create_folder_backup(source_files, backup_folder)
        
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None
    
    def _create_compressed_backup(
        self, 
        source_files: List[str], 
        backup_file: Path
    ) -> str:
        """Crear backup comprimido en ZIP"""
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for source in source_files:
                source_path = Path(source)
                
                if source_path.exists():
                    if source_path.is_file():
                        zipf.write(source_path, source_path.name)
                    elif source_path.is_dir():
                        for file in source_path.rglob('*'):
                            if file.is_file():
                                arcname = file.relative_to(source_path.parent)
                                zipf.write(file, arcname)
        
        # Agregar metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'files': source_files,
            'compressed': True
        }
        
        metadata_file = backup_file.with_suffix('.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return str(backup_file)
    
    def _create_folder_backup(
        self, 
        source_files: List[str], 
        backup_folder: Path
    ) -> str:
        """Crear backup en carpeta"""
        backup_folder.mkdir(parents=True, exist_ok=True)
        
        for source in source_files:
            source_path = Path(source)
            
            if source_path.exists():
                dest = backup_folder / source_path.name
                
                if source_path.is_file():
                    shutil.copy2(source_path, dest)
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest, dirs_exist_ok=True)
        
        # Agregar metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'files': source_files,
            'compressed': False
        }
        
        metadata_file = backup_folder / 'backup_info.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return str(backup_folder)
    
    def restore_backup(self, backup_name: str, restore_dir: str = None) -> bool:
        """
        Restaurar backup
        
        Args:
            backup_name: Nombre del backup a restaurar
            restore_dir: Directorio destino (None = ubicación original)
        
        Returns:
            bool: True si se restauró correctamente
        """
        try:
            backup_file = self.backup_dir / f"{backup_name}.zip"
            
            if backup_file.exists():
                return self._restore_compressed_backup(backup_file, restore_dir)
            else:
                backup_folder = self.backup_dir / backup_name
                if backup_folder.exists():
                    return self._restore_folder_backup(backup_folder, restore_dir)
            
            print(f"❌ Backup no encontrado: {backup_name}")
            return False
        
        except Exception as e:
            print(f"❌ Error restaurando backup: {e}")
            return False
    
    def _restore_compressed_backup(
        self, 
        backup_file: Path, 
        restore_dir: str = None
    ) -> bool:
        """Restaurar backup comprimido"""
        target_dir = Path(restore_dir) if restore_dir else Path.cwd()
        
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(target_dir)
        
        return True
    
    def _restore_folder_backup(
        self, 
        backup_folder: Path, 
        restore_dir: str = None
    ) -> bool:
        """Restaurar backup de carpeta"""
        target_dir = Path(restore_dir) if restore_dir else Path.cwd()
        
        for item in backup_folder.iterdir():
            if item.name == 'backup_info.json':
                continue
            
            dest = target_dir / item.name
            
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
        
        return True
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Listar todos los backups disponibles"""
        backups = []
        
        # Buscar backups comprimidos
        for zip_file in self.backup_dir.glob('*.zip'):
            metadata_file = zip_file.with_suffix('.json')
            
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            backups.append({
                'name': zip_file.stem,
                'type': 'compressed',
                'size_mb': round(zip_file.stat().st_size / (1024 * 1024), 2),
                'created_at': metadata.get('created_at', 'Unknown'),
                'files': metadata.get('files', []),
                'path': str(zip_file)
            })
        
        # Buscar backups en carpetas
        for folder in self.backup_dir.iterdir():
            if folder.is_dir():
                metadata_file = folder / 'backup_info.json'
                
                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                # Calcular tamaño total
                total_size = sum(
                    f.stat().st_size 
                    for f in folder.rglob('*') 
                    if f.is_file()
                )
                
                backups.append({
                    'name': folder.name,
                    'type': 'folder',
                    'size_mb': round(total_size / (1024 * 1024), 2),
                    'created_at': metadata.get('created_at', 'Unknown'),
                    'files': metadata.get('files', []),
                    'path': str(folder)
                })
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self) -> int:
        """
        Limpiar backups antiguos manteniendo solo los últimos N
        
        Returns:
            int: Número de backups eliminados
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= self.max_backups:
                return 0
            
            # Eliminar los más antiguos
            to_delete = backups[self.max_backups:]
            count = 0
            
            for backup in to_delete:
                backup_path = Path(backup['path'])
                
                if backup['type'] == 'compressed':
                    backup_path.unlink()
                    # Eliminar metadata
                    metadata_file = backup_path.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                else:
                    shutil.rmtree(backup_path)
                
                count += 1
            
            return count
        
        except Exception as e:
            print(f"⚠️  Error en cleanup: {e}")
            return 0
    
    def backup_config(self, config_dir: str = "config") -> Optional[str]:
        """
        Crear backup específico de configuración
        
        Args:
            config_dir: Directorio de configuración
        
        Returns:
            str: Ruta del backup creado
        """
        config_path = Path(config_dir)
        
        if not config_path.exists():
            print(f"❌ Directorio de configuración no existe: {config_dir}")
            return None
        
        # Obtener todos los archivos de configuración
        config_files = [
            str(f) for f in config_path.rglob('*') 
            if f.is_file() and not f.name.startswith('.')
        ]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"config_backup_{timestamp}"
        
        return self.create_backup(config_files, backup_name)


# CLI de prueba
if __name__ == "__main__":
    backup_mgr = BackupManager()
    
    print("💾 Backup Manager Demo\n")
    
    # Crear backup de configuración
    print("1. Creando backup de configuración...")
    backup_path = backup_mgr.backup_config()
    if backup_path:
        print(f"   ✓ Backup creado: {backup_path}")
    
    # Listar backups
    print("\n2. Backups disponibles:")
    backups = backup_mgr.list_backups()
    for backup in backups:
        print(f"   • {backup['name']} - {backup['size_mb']} MB ({backup['type']})")
    
    print(f"\n3. Total de backups: {len(backups)}")
