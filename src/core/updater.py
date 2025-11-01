"""
IT Monitoring Agent - Updater Module
Gestiona la verificación, descarga e instalación de actualizaciones del agente
"""

import os
import sys
import shutil
import hashlib
import json
import tempfile
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from packaging import version


class Updater:
    """
    Gestiona las actualizaciones del agente
    
    Funcionalidades:
    - Verificar si hay actualizaciones disponibles
    - Descargar actualizaciones desde el servidor
    - Validar integridad de archivos descargados
    - Aplicar actualizaciones de forma segura
    - Rollback en caso de error
    """
    
    def __init__(self, config, logger, api_client=None):
        """
        Inicializa el Updater
        
        Args:
            config: Objeto de configuración
            logger: Logger del agente
            api_client: Cliente API para comunicación con servidor (opcional)
        """
        self.config = config
        self.logger = logger
        self.api_client = api_client
        
        # Versión actual del agente
        self.current_version = config.get('agent', 'version', fallback='1.0.0')
        
        # Directorios
        self.root_dir = Path(__file__).parent.parent.parent  # Raíz del proyecto
        self.backup_dir = self.root_dir / 'backups'
        self.temp_dir = self.root_dir / 'temp'
        
        # Crear directorios si no existen
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Estado de actualización
        self.update_available = False
        self.latest_version = None
        self.update_info = None
        
        self.logger.info("Updater inicializado")
        self.logger.debug(f"Versión actual: {self.current_version}")
    
    # ═══════════════════════════════════════════════════════════
    # VERIFICACIÓN DE ACTUALIZACIONES
    # ═══════════════════════════════════════════════════════════
    
    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Verifica si hay actualizaciones disponibles
        
        Returns:
            Tuple[bool, Optional[str]]: (hay_actualización, versión_disponible)
        """
        try:
            self.logger.info("🔍 Verificando actualizaciones disponibles...")
            
            # Si no hay API client, verificar desde archivo local o URL pública
            if not self.api_client:
                self.logger.warning("API Client no disponible, verificando desde fuente alternativa")
                return self._check_updates_from_url()
            
            # Obtener información de actualizaciones desde el servidor
            update_info = self._get_update_info_from_server()
            
            if not update_info:
                self.logger.info("✓ No hay actualizaciones disponibles")
                return False, None
            
            latest_version = update_info.get('version')
            
            if not latest_version:
                self.logger.warning("⚠️  Información de actualización inválida")
                return False, None
            
            # Comparar versiones
            if self._is_newer_version(latest_version, self.current_version):
                self.update_available = True
                self.latest_version = latest_version
                self.update_info = update_info
                
                self.logger.info(f"✨ Nueva versión disponible: {latest_version}")
                self.logger.info(f"   Versión actual: {self.current_version}")
                
                # Mostrar notas de la versión si están disponibles
                if 'release_notes' in update_info:
                    self.logger.info(f"   Notas: {update_info['release_notes']}")
                
                return True, latest_version
            else:
                self.logger.info(f"✓ Ya tienes la última versión ({self.current_version})")
                return False, None
                
        except Exception as e:
            self.logger.error(f"❌ Error al verificar actualizaciones: {e}", exc_info=True)
            return False, None
    
    def _get_update_info_from_server(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de actualizaciones desde el servidor
        
        Returns:
            Dict con información de la actualización o None
        """
        try:
            # Intentar obtener info de actualizaciones del API client
            if hasattr(self.api_client, 'check_updates'):
                success, data = self.api_client.check_updates()
                if success and data:
                    return data
            
            # Si el API client no tiene el método, usar endpoint genérico
            response = self.api_client.get('/updates/latest')
            if response and response.get('success'):
                return response.get('data')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al obtener info de actualizaciones: {e}")
            return None
    
    def _check_updates_from_url(self) -> Tuple[bool, Optional[str]]:
        """
        Verifica actualizaciones desde una URL pública (fallback)
        
        Returns:
            Tuple[bool, Optional[str]]: (hay_actualización, versión)
        """
        try:
            # URL de verificación de versiones (puede ser GitHub releases, etc.)
            update_url = self.config.get('updater', 'update_url', fallback=None)
            
            if not update_url:
                self.logger.debug("No hay URL de actualización configurada")
                return False, None
            
            import urllib.request
            
            self.logger.debug(f"Verificando actualizaciones desde: {update_url}")
            
            with urllib.request.urlopen(update_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data.get('version')
                
                if latest_version and self._is_newer_version(latest_version, self.current_version):
                    self.update_info = data
                    return True, latest_version
                
                return False, None
                
        except Exception as e:
            self.logger.debug(f"No se pudo verificar desde URL: {e}")
            return False, None
    
    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """
        Compara dos versiones usando semver
        
        Args:
            new_version: Nueva versión a comparar
            current_version: Versión actual
            
        Returns:
            True si new_version es más reciente que current_version
        """
        try:
            return version.parse(new_version) > version.parse(current_version)
        except Exception as e:
            self.logger.error(f"Error al comparar versiones: {e}")
            # Fallback a comparación simple de strings
            return new_version > current_version
    
    # ═══════════════════════════════════════════════════════════
    # DESCARGA DE ACTUALIZACIONES
    # ═══════════════════════════════════════════════════════════
    
    def download_update(self) -> Optional[Path]:
        """
        Descarga la actualización disponible
        
        Returns:
            Path del archivo descargado o None si falla
        """
        if not self.update_available or not self.update_info:
            self.logger.warning("No hay actualización disponible para descargar")
            return None
        
        try:
            download_url = self.update_info.get('download_url')
            
            if not download_url:
                self.logger.error("No hay URL de descarga en la información de actualización")
                return None
            
            self.logger.info(f"📥 Descargando actualización {self.latest_version}...")
            self.logger.info(f"   URL: {download_url}")
            
            # Nombre del archivo temporal
            filename = f"update_{self.latest_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            download_path = self.temp_dir / filename
            
            # Descargar archivo
            import urllib.request
            
            def _download_progress(block_num, block_size, total_size):
                """Callback para mostrar progreso de descarga"""
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded / total_size) * 100)
                    if block_num % 50 == 0:  # Log cada cierto progreso
                        self.logger.debug(f"   Progreso: {percent:.1f}%")
            
            urllib.request.urlretrieve(download_url, download_path, _download_progress)
            
            self.logger.info(f"✓ Descarga completada: {download_path}")
            
            # Verificar integridad si hay hash disponible
            if 'checksum' in self.update_info:
                if not self._verify_checksum(download_path, self.update_info['checksum']):
                    self.logger.error("❌ Verificación de integridad falló")
                    download_path.unlink()  # Eliminar archivo corrupto
                    return None
                
                self.logger.info("✓ Integridad verificada")
            
            return download_path
            
        except Exception as e:
            self.logger.error(f"❌ Error al descargar actualización: {e}", exc_info=True)
            return None
    
    def _verify_checksum(self, file_path: Path, expected_hash: str) -> bool:
        """
        Verifica el checksum SHA256 de un archivo
        
        Args:
            file_path: Path del archivo a verificar
            expected_hash: Hash esperado (SHA256)
            
        Returns:
            True si el hash coincide
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                # Leer en chunks para archivos grandes
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            calculated_hash = sha256_hash.hexdigest()
            
            self.logger.debug(f"Hash esperado:   {expected_hash}")
            self.logger.debug(f"Hash calculado:  {calculated_hash}")
            
            return calculated_hash.lower() == expected_hash.lower()
            
        except Exception as e:
            self.logger.error(f"Error al verificar checksum: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════
    # APLICACIÓN DE ACTUALIZACIONES
    # ═══════════════════════════════════════════════════════════
    
    def apply_update(self, update_file: Path) -> bool:
        """
        Aplica una actualización descargada
        
        Args:
            update_file: Path del archivo de actualización (.zip)
            
        Returns:
            True si la actualización se aplicó correctamente
        """
        backup_path = None
        
        try:
            self.logger.info("🔄 Aplicando actualización...")
            
            # 1. Crear backup del estado actual
            self.logger.info("   1/5 Creando backup...")
            backup_path = self._create_backup()
            
            if not backup_path:
                self.logger.error("❌ No se pudo crear backup")
                return False
            
            self.logger.info(f"   ✓ Backup creado: {backup_path}")
            
            # 2. Extraer actualización
            self.logger.info("   2/5 Extrayendo actualización...")
            extract_path = self._extract_update(update_file)
            
            if not extract_path:
                self.logger.error("❌ No se pudo extraer actualización")
                self._restore_backup(backup_path)
                return False
            
            self.logger.info(f"   ✓ Actualización extraída")
            
            # 3. Validar estructura
            self.logger.info("   3/5 Validando estructura...")
            
            if not self._validate_update_structure(extract_path):
                self.logger.error("❌ Estructura de actualización inválida")
                self._restore_backup(backup_path)
                shutil.rmtree(extract_path, ignore_errors=True)
                return False
            
            self.logger.info("   ✓ Estructura válida")
            
            # 4. Aplicar archivos
            self.logger.info("   4/5 Aplicando archivos...")
            
            if not self._apply_files(extract_path):
                self.logger.error("❌ Error al aplicar archivos")
                self._restore_backup(backup_path)
                shutil.rmtree(extract_path, ignore_errors=True)
                return False
            
            self.logger.info("   ✓ Archivos aplicados")
            
            # 5. Actualizar configuración
            self.logger.info("   5/5 Actualizando configuración...")
            self._update_version_config()
            
            # Limpiar
            shutil.rmtree(extract_path, ignore_errors=True)
            update_file.unlink(missing_ok=True)
            
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Actualización completada exitosamente")
            self.logger.info(f"   Versión anterior: {self.current_version}")
            self.logger.info(f"   Versión actual:   {self.latest_version}")
            self.logger.info("=" * 60)
            self.logger.info("⚠️  Reinicia el agente para aplicar los cambios")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al aplicar actualización: {e}", exc_info=True)
            
            # Intentar rollback
            if backup_path:
                self.logger.warning("Intentando rollback...")
                self._restore_backup(backup_path)
            
            return False
    
    def _create_backup(self) -> Optional[Path]:
        """
        Crea un backup del estado actual del agente
        
        Returns:
            Path del directorio de backup o None si falla
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_v{self.current_version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # Directorios a respaldar
            dirs_to_backup = ['src', 'config']
            
            backup_path.mkdir(exist_ok=True)
            
            for dir_name in dirs_to_backup:
                src_dir = self.root_dir / dir_name
                
                if src_dir.exists():
                    dst_dir = backup_path / dir_name
                    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error al crear backup: {e}")
            return None
    
    def _restore_backup(self, backup_path: Path) -> bool:
        """
        Restaura un backup anterior
        
        Args:
            backup_path: Path del backup a restaurar
            
        Returns:
            True si se restauró correctamente
        """
        try:
            self.logger.warning(f"Restaurando backup desde: {backup_path}")
            
            # Restaurar cada directorio
            for item in backup_path.iterdir():
                if item.is_dir():
                    dst = self.root_dir / item.name
                    
                    # Eliminar directorio actual
                    if dst.exists():
                        shutil.rmtree(dst)
                    
                    # Copiar desde backup
                    shutil.copytree(item, dst)
            
            self.logger.info("✓ Backup restaurado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al restaurar backup: {e}")
            return False
    
    def _extract_update(self, update_file: Path) -> Optional[Path]:
        """
        Extrae el archivo de actualización
        
        Args:
            update_file: Path del archivo .zip
            
        Returns:
            Path del directorio extraído o None
        """
        try:
            extract_dir = self.temp_dir / f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            return extract_dir
            
        except Exception as e:
            self.logger.error(f"Error al extraer actualización: {e}")
            return None
    
    def _validate_update_structure(self, extract_path: Path) -> bool:
        """
        Valida que la estructura de la actualización sea correcta
        
        Args:
            extract_path: Path del directorio extraído
            
        Returns:
            True si la estructura es válida
        """
        try:
            # Verificar que existan directorios críticos
            required_dirs = ['src']
            
            for dir_name in required_dirs:
                dir_path = extract_path / dir_name
                if not dir_path.exists():
                    self.logger.error(f"Falta directorio requerido: {dir_name}")
                    return False
            
            # Verificar que exista main.py
            main_py = extract_path / 'src' / 'main.py'
            if not main_py.exists():
                self.logger.error("Falta archivo crítico: src/main.py")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al validar estructura: {e}")
            return False
    
    def _apply_files(self, extract_path: Path) -> bool:
        """
        Copia los archivos de la actualización al directorio del agente
        
        Args:
            extract_path: Path del directorio con los archivos extraídos
            
        Returns:
            True si se copiaron correctamente
        """
        try:
            # Directorios a actualizar
            dirs_to_update = ['src']
            
            for dir_name in dirs_to_update:
                src_dir = extract_path / dir_name
                
                if not src_dir.exists():
                    continue
                
                dst_dir = self.root_dir / dir_name
                
                # Copiar archivos
                for item in src_dir.rglob('*'):
                    if item.is_file():
                        relative_path = item.relative_to(src_dir)
                        dst_file = dst_dir / relative_path
                        
                        # Crear directorio si no existe
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copiar archivo
                        shutil.copy2(item, dst_file)
                        self.logger.debug(f"   Actualizado: {relative_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al aplicar archivos: {e}")
            return False
    
    def _update_version_config(self):
        """Actualiza la versión en el archivo de configuración"""
        try:
            if self.latest_version:
                self.config.set('agent', 'version', self.latest_version)
                # Si tu Config tiene método save(), usarlo
                if hasattr(self.config, 'save'):
                    self.config.save()
                
                self.current_version = self.latest_version
                
        except Exception as e:
            self.logger.error(f"Error al actualizar versión en config: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # MÉTODOS DE UTILIDAD
    # ═══════════════════════════════════════════════════════════
    
    def auto_update(self) -> bool:
        """
        Realiza el proceso completo de actualización automática
        
        Returns:
            True si se actualizó correctamente
        """
        try:
            # 1. Verificar actualizaciones
            has_update, latest_version = self.check_for_updates()
            
            if not has_update:
                return False
            
            # 2. Descargar actualización
            update_file = self.download_update()
            
            if not update_file:
                self.logger.error("No se pudo descargar la actualización")
                return False
            
            # 3. Aplicar actualización
            success = self.apply_update(update_file)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error en auto_update: {e}", exc_info=True)
            return False
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de actualizaciones
        
        Returns:
            Dict con información del estado
        """
        return {
            'current_version': self.current_version,
            'update_available': self.update_available,
            'latest_version': self.latest_version,
            'update_info': self.update_info
        }
    
    def cleanup_old_backups(self, keep_last_n: int = 5):
        """
        Limpia backups antiguos, manteniendo solo los últimos N
        
        Args:
            keep_last_n: Número de backups a mantener
        """
        try:
            self.logger.info(f"Limpiando backups antiguos (manteniendo últimos {keep_last_n})...")
            
            # Obtener lista de backups ordenados por fecha
            backups = sorted(
                [d for d in self.backup_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Eliminar backups antiguos
            for backup in backups[keep_last_n:]:
                self.logger.debug(f"Eliminando backup: {backup.name}")
                shutil.rmtree(backup)
            
            self.logger.info(f"✓ Limpieza completada ({len(backups) - keep_last_n} backups eliminados)")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar backups: {e}")
    
    def cleanup_temp_files(self):
        """Limpia archivos temporales de actualizaciones"""
        try:
            self.logger.debug("Limpiando archivos temporales...")
            
            for item in self.temp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    self.logger.debug(f"No se pudo eliminar {item}: {e}")
            
            self.logger.debug("✓ Archivos temporales limpiados")
            
        except Exception as e:
            self.logger.error(f"Error al limpiar temporales: {e}")


# ═══════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════

def restart_agent():
    """
    Reinicia el agente después de una actualización
    
    Nota: Esta función debe ser llamada después de aplicar una actualización
    """
    import sys
    import os
    
    print("🔄 Reiniciando agente...")
    
    # Obtener el comando actual
    python = sys.executable
    script = sys.argv[0]
    
    # Reiniciar
    os.execl(python, python, script, *sys.argv[1:])