"""
IT Monitoring Agent - File Utilities
Funciones para operaciones seguras con archivos y directorios
"""

import os
import shutil
import hashlib
import gzip
import zipfile
import json
from pathlib import Path
from typing import Optional, Union, List, Dict, Any


def ensure_directory(directory: Union[str, Path], mode: int = 0o755) -> bool:
    """
    Asegura que un directorio existe, creándolo si es necesario
    
    Args:
        directory: Path del directorio
        mode: Permisos del directorio (Unix/Linux)
        
    Returns:
        True si el directorio existe o fue creado
    """
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True, mode=mode)
        return True
    except Exception as e:
        return False


def safe_read_file(
    filepath: Union[str, Path],
    encoding: str = 'utf-8',
    default: Optional[str] = None
) -> Optional[str]:
    """
    Lee un archivo de manera segura
    
    Args:
        filepath: Path del archivo
        encoding: Encoding a usar
        default: Valor por defecto si falla
        
    Returns:
        Contenido del archivo o default
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        return default


def safe_write_file(
    filepath: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> bool:
    """
    Escribe un archivo de manera segura
    
    Args:
        filepath: Path del archivo
        content: Contenido a escribir
        encoding: Encoding a usar
        create_dirs: Si True, crea directorios padre si no existen
        
    Returns:
        True si se escribió correctamente
    """
    try:
        path = Path(filepath)
        
        if create_dirs:
            ensure_directory(path.parent)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
    except Exception as e:
        return False


def safe_read_json(
    filepath: Union[str, Path],
    default: Optional[dict] = None
) -> Optional[dict]:
    """
    Lee un archivo JSON de manera segura
    
    Args:
        filepath: Path del archivo JSON
        default: Valor por defecto si falla
        
    Returns:
        Datos parseados o default
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return default if default is not None else {}


def safe_write_json(
    filepath: Union[str, Path],
    data: dict,
    indent: int = 2,
    create_dirs: bool = True
) -> bool:
    """
    Escribe un archivo JSON de manera segura
    
    Args:
        filepath: Path del archivo
        data: Datos a escribir
        indent: Indentación del JSON
        create_dirs: Crear directorios padre
        
    Returns:
        True si se escribió correctamente
    """
    try:
        path = Path(filepath)
        
        if create_dirs:
            ensure_directory(path.parent)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
    except Exception as e:
        return False


def get_file_hash(
    filepath: Union[str, Path],
    algorithm: str = 'sha256'
) -> Optional[str]:
    """
    Calcula el hash de un archivo
    
    Args:
        filepath: Path del archivo
        algorithm: Algoritmo (md5, sha1, sha256, sha512)
        
    Returns:
        Hash hexadecimal o None si falla
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            # Leer en chunks para archivos grandes
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    except Exception as e:
        return None


def compress_file(
    source_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    compression_level: int = 6
) -> Optional[Path]:
    """
    Comprime un archivo usando gzip
    
    Args:
        source_file: Archivo a comprimir
        output_file: Archivo de salida (default: source_file.gz)
        compression_level: Nivel de compresión (1-9)
        
    Returns:
        Path del archivo comprimido o None si falla
    """
    try:
        source = Path(source_file)
        
        if output_file is None:
            output = source.with_suffix(source.suffix + '.gz')
        else:
            output = Path(output_file)
        
        with open(source, 'rb') as f_in:
            with gzip.open(output, 'wb', compresslevel=compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return output
    except Exception as e:
        return None


def decompress_file(
    compressed_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    Descomprime un archivo gzip
    
    Args:
        compressed_file: Archivo comprimido
        output_file: Archivo de salida (default: sin .gz)
        
    Returns:
        Path del archivo descomprimido o None si falla
    """
    try:
        source = Path(compressed_file)
        
        if output_file is None:
            if source.suffix == '.gz':
                output = source.with_suffix('')
            else:
                output = source.with_name(source.stem + '_decompressed')
        else:
            output = Path(output_file)
        
        with gzip.open(source, 'rb') as f_in:
            with open(output, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return output
    except Exception as e:
        return None


def create_zip(
    files: List[Union[str, Path]],
    output_file: Union[str, Path],
    compression: int = zipfile.ZIP_DEFLATED
) -> bool:
    """
    Crea un archivo ZIP con los archivos especificados
    
    Args:
        files: Lista de archivos a incluir
        output_file: Archivo ZIP de salida
        compression: Método de compresión
        
    Returns:
        True si se creó correctamente
    """
    try:
        with zipfile.ZipFile(output_file, 'w', compression=compression) as zipf:
            for file in files:
                file_path = Path(file)
                if file_path.exists():
                    # Mantener estructura de directorios relativa
                    zipf.write(file_path, arcname=file_path.name)
        
        return True
    except Exception as e:
        return False


def extract_zip(
    zip_file: Union[str, Path],
    output_dir: Union[str, Path],
    members: Optional[List[str]] = None
) -> bool:
    """
    Extrae un archivo ZIP
    
    Args:
        zip_file: Archivo ZIP a extraer
        output_dir: Directorio de salida
        members: Lista de miembros específicos a extraer (None = todos)
        
    Returns:
        True si se extrajo correctamente
    """
    try:
        ensure_directory(output_dir)
        
        with zipfile.ZipFile(zip_file, 'r') as zipf:
            if members:
                zipf.extractall(output_dir, members=members)
            else:
                zipf.extractall(output_dir)
        
        return True
    except Exception as e:
        return False


def get_file_size(filepath: Union[str, Path]) -> int:
    """
    Obtiene el tamaño de un archivo en bytes
    
    Args:
        filepath: Path del archivo
        
    Returns:
        Tamaño en bytes
    """
    try:
        return Path(filepath).stat().st_size
    except Exception:
        return 0


def get_directory_size(directory: Union[str, Path]) -> int:
    """
    Obtiene el tamaño total de un directorio
    
    Args:
        directory: Path del directorio
        
    Returns:
        Tamaño total en bytes
    """
    try:
        total = 0
        for entry in Path(directory).rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
    except Exception:
        return 0


def list_files(
    directory: Union[str, Path],
    pattern: str = '*',
    recursive: bool = False
) -> List[Path]:
    """
    Lista archivos en un directorio
    
    Args:
        directory: Directorio a listar
        pattern: Patrón de búsqueda (wildcard)
        recursive: Si True, busca recursivamente
        
    Returns:
        Lista de Paths
    """
    try:
        dir_path = Path(directory)
        
        if recursive:
            return list(dir_path.rglob(pattern))
        else:
            return list(dir_path.glob(pattern))
    except Exception:
        return []


def delete_old_files(
    directory: Union[str, Path],
    days: int,
    pattern: str = '*',
    recursive: bool = False
) -> int:
    """
    Elimina archivos más antiguos que X días
    
    Args:
        directory: Directorio a limpiar
        days: Días de antigüedad
        pattern: Patrón de archivos
        recursive: Buscar recursivamente
        
    Returns:
        Número de archivos eliminados
    """
    try:
        import time
        
        cutoff_time = time.time() - (days * 86400)
        deleted_count = 0
        
        files = list_files(directory, pattern, recursive)
        
        for file_path in files:
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        
        return deleted_count
    except Exception:
        return 0


def copy_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    overwrite: bool = True
) -> bool:
    """
    Copia un archivo de manera segura
    
    Args:
        source: Archivo origen
        destination: Archivo destino
        overwrite: Si True, sobrescribe si existe
        
    Returns:
        True si se copió correctamente
    """
    try:
        dest_path = Path(destination)
        
        if dest_path.exists() and not overwrite:
            return False
        
        ensure_directory(dest_path.parent)
        shutil.copy2(source, destination)
        
        return True
    except Exception:
        return False


def move_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    overwrite: bool = True
) -> bool:
    """
    Mueve un archivo de manera segura
    
    Args:
        source: Archivo origen
        destination: Archivo destino
        overwrite: Si True, sobrescribe si existe
        
    Returns:
        True si se movió correctamente
    """
    try:
        dest_path = Path(destination)
        
        if dest_path.exists() and not overwrite:
            return False
        
        ensure_directory(dest_path.parent)
        shutil.move(str(source), str(destination))
        
        return True
    except Exception:
        return False


def backup_file(
    filepath: Union[str, Path],
    backup_dir: Optional[Union[str, Path]] = None,
    suffix: str = '.bak'
) -> Optional[Path]:
    """
    Crea un backup de un archivo
    
    Args:
        filepath: Archivo a respaldar
        backup_dir: Directorio de backup (None = mismo directorio)
        suffix: Sufijo para el backup
        
    Returns:
        Path del backup o None si falla
    """
    try:
        source = Path(filepath)
        
        if not source.exists():
            return None
        
        if backup_dir:
            backup_path = Path(backup_dir) / (source.name + suffix)
        else:
            backup_path = source.with_suffix(source.suffix + suffix)
        
        ensure_directory(backup_path.parent)
        shutil.copy2(source, backup_path)
        
        return backup_path
    except Exception:
        return None


def rotate_file(
    filepath: Union[str, Path],
    max_backups: int = 5
) -> bool:
    """
    Rota un archivo manteniendo N backups
    
    Args:
        filepath: Archivo a rotar
        max_backups: Número máximo de backups
        
    Returns:
        True si se rotó correctamente
    """
    try:
        path = Path(filepath)
        
        if not path.exists():
            return False
        
        # Rotar backups existentes
        for i in range(max_backups - 1, 0, -1):
            old_backup = path.with_suffix(f'{path.suffix}.{i}')
            new_backup = path.with_suffix(f'{path.suffix}.{i + 1}')
            
            if old_backup.exists():
                if new_backup.exists():
                    new_backup.unlink()
                old_backup.rename(new_backup)
        
        # Crear nuevo backup .1
        first_backup = path.with_suffix(f'{path.suffix}.1')
        shutil.copy2(path, first_backup)
        
        # Limpiar archivo original
        path.write_text('')
        
        return True
    except Exception:
        return False


def read_lines(
    filepath: Union[str, Path],
    encoding: str = 'utf-8',
    strip: bool = True
) -> List[str]:
    """
    Lee un archivo línea por línea
    
    Args:
        filepath: Path del archivo
        encoding: Encoding
        strip: Si True, elimina whitespace de cada línea
        
    Returns:
        Lista de líneas
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            lines = f.readlines()
            
            if strip:
                lines = [line.strip() for line in lines]
            
            return lines
    except Exception:
        return []


def write_lines(
    filepath: Union[str, Path],
    lines: List[str],
    encoding: str = 'utf-8',
    add_newline: bool = True
) -> bool:
    """
    Escribe líneas a un archivo
    
    Args:
        filepath: Path del archivo
        lines: Lista de líneas
        encoding: Encoding
        add_newline: Si True, agrega newline a cada línea
        
    Returns:
        True si se escribió correctamente
    """
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            for line in lines:
                if add_newline and not line.endswith('\n'):
                    f.write(line + '\n')
                else:
                    f.write(line)
        
        return True
    except Exception:
        return False


def append_to_file(
    filepath: Union[str, Path],
    content: str,
    encoding: str = 'utf-8'
) -> bool:
    """
    Agrega contenido al final de un archivo
    
    Args:
        filepath: Path del archivo
        content: Contenido a agregar
        encoding: Encoding
        
    Returns:
        True si se agregó correctamente
    """
    try:
        with open(filepath, 'a', encoding=encoding) as f:
            f.write(content)
        
        return True
    except Exception:
        return False