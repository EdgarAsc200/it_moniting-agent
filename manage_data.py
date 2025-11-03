#!/usr/bin/env python3
"""
Script de gestión de data (cache y backups)
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.cache_manager import CacheManager
from utils.backup_manager import BackupManager
import argparse


def cache_stats():
    """Mostrar estadísticas del cache"""
    cache = CacheManager()
    stats = cache.get_stats()
    
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL CACHE")
    print("="*60)
    
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()


def cache_list():
    """Listar contenido del cache"""
    cache = CacheManager()
    keys = cache.list_keys()
    
    print("\n" + "="*60)
    print("📦 CONTENIDO DEL CACHE")
    print("="*60 + "\n")
    
    if not keys:
        print("  (vacío)")
    else:
        for key_info in keys:
            status = "❌ Expirado" if key_info['expired'] else "✅ Válido"
            print(f"  • {key_info['key']}")
            print(f"    Tamaño: {key_info['size_kb']} KB")
            print(f"    Estado: {status}")
            print(f"    Creado: {key_info['created_at']}")
            print(f"    Expira: {key_info['expires_at']}\n")


def cache_clear():
    """Limpiar todo el cache"""
    cache = CacheManager()
    count = cache.clear()
    print(f"\n✓ {count} archivos eliminados del cache\n")


def cache_cleanup():
    """Limpiar entradas expiradas"""
    cache = CacheManager()
    count = cache.cleanup_expired()
    print(f"\n✓ {count} entradas expiradas eliminadas\n")


def backup_create():
    """Crear backup de configuración"""
    backup_mgr = BackupManager()
    
    print("\n📦 Creando backup de configuración...")
    backup_path = backup_mgr.backup_config()
    
    if backup_path:
        print(f"✓ Backup creado: {backup_path}\n")
    else:
        print("❌ Error creando backup\n")


def backup_list():
    """Listar backups disponibles"""
    backup_mgr = BackupManager()
    backups = backup_mgr.list_backups()
    
    print("\n" + "="*60)
    print("💾 BACKUPS DISPONIBLES")
    print("="*60 + "\n")
    
    if not backups:
        print("  (ninguno)")
    else:
        for backup in backups:
            print(f"  • {backup['name']}")
            print(f"    Tipo: {backup['type']}")
            print(f"    Tamaño: {backup['size_mb']} MB")
            print(f"    Creado: {backup['created_at']}")
            print(f"    Archivos: {len(backup['files'])}\n")
    
    print(f"Total: {len(backups)} backups\n")


def backup_cleanup():
    """Limpiar backups antiguos"""
    backup_mgr = BackupManager()
    count = backup_mgr.cleanup_old_backups()
    print(f"\n✓ {count} backups antiguos eliminados\n")


def main():
    parser = argparse.ArgumentParser(
        description='Gestión de data (cache y backups)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Cache commands
    cache_parser = subparsers.add_parser('cache', help='Gestión de cache')
    cache_subparsers = cache_parser.add_subparsers(dest='cache_action')
    
    cache_subparsers.add_parser('stats', help='Estadísticas del cache')
    cache_subparsers.add_parser('list', help='Listar contenido')
    cache_subparsers.add_parser('clear', help='Limpiar todo')
    cache_subparsers.add_parser('cleanup', help='Limpiar expirados')
    
    # Backup commands
    backup_parser = subparsers.add_parser('backup', help='Gestión de backups')
    backup_subparsers = backup_parser.add_subparsers(dest='backup_action')
    
    backup_subparsers.add_parser('create', help='Crear backup')
    backup_subparsers.add_parser('list', help='Listar backups')
    backup_subparsers.add_parser('cleanup', help='Limpiar antiguos')
    
    args = parser.parse_args()
    
    if args.command == 'cache':
        if args.cache_action == 'stats':
            cache_stats()
        elif args.cache_action == 'list':
            cache_list()
        elif args.cache_action == 'clear':
            cache_clear()
        elif args.cache_action == 'cleanup':
            cache_cleanup()
        else:
            cache_parser.print_help()
    
    elif args.command == 'backup':
        if args.backup_action == 'create':
            backup_create()
        elif args.backup_action == 'list':
            backup_list()
        elif args.backup_action == 'cleanup':
            backup_cleanup()
        else:
            backup_parser.print_help()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
