"""
Punto de entrada principal del IT Monitoring Agent
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.agent import Agent
from core.logger import setup_logger


def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
    """
    parser = argparse.ArgumentParser(
        description='IT Monitoring Agent - Sistema de monitoreo de activos IT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python src/main.py                    # Ejecutar en modo continuo
  python src/main.py --debug            # Modo debug (validar configuración)
  python src/main.py --validate         # Validar configuración
  python src/main.py --register         # Registrar agente en servidor
  python src/main.py --test             # Probar recolección (sin enviar)
  python src/main.py --once             # Ejecutar una sola vez
  python src/main.py --models           # Usar modelos validados
  python src/main.py --export-models    # Exportar inventario a JSON
        """
    )
    
    # Modos de operación
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--debug',
        action='store_true',
        help='Modo debug - Validar configuración sin ejecutar'
    )
    mode_group.add_argument(
        '--validate',
        action='store_true',
        help='Validar configuración sin ejecutar (alias de --debug)'
    )
    mode_group.add_argument(
        '--register',
        action='store_true',
        help='Registrar el agente en el servidor'
    )
    mode_group.add_argument(
        '--test',
        action='store_true',
        help='Probar recolección de datos sin enviar al servidor'
    )
    mode_group.add_argument(
        '--once',
        action='store_true',
        help='Ejecutar un solo ciclo de recolección y envío'
    )
    mode_group.add_argument(
        '--models',
        action='store_true',
        help='Recolectar y enviar usando modelos validados'
    )
    mode_group.add_argument(
        '--export-models',
        action='store_true',
        help='Exportar inventario con modelos a archivo JSON'
    )
    
    # Opciones para modelos
    parser.add_argument(
        '--location',
        type=str,
        default=None,
        help='Ubicación del asset (usado con --models o --export-models)'
    )
    parser.add_argument(
        '--department',
        type=str,
        default=None,
        help='Departamento (usado con --models o --export-models)'
    )
    parser.add_argument(
        '--assigned-to',
        type=str,
        default=None,
        help='Usuario asignado (usado con --models o --export-models)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='inventory.json',
        help='Archivo de salida para --export-models (default: inventory.json)'
    )
    
    # Configuración
    parser.add_argument(
    '--config',
    type=str,
    default='config/agent.ini',  # ⬅️ Cambiado a agent.ini
    help='Ruta al archivo de configuración'
)
    
    return parser.parse_args()


def print_banner():
    """Imprime el banner del agente"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         IT MONITORING AGENT v1.0.0                        ║
    ║         Sistema de Monitoreo de Activos IT                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def mode_debug(agent: Agent):
    """
    Modo: Debug/Validar configuración
    """
    print("\n🔍 MODO DEBUG - Validación de Configuración\n")
    agent.validate()


def mode_register(agent: Agent):
    """
    Modo: Registrar agente
    """
    print("\n📝 MODO: REGISTRO DE AGENTE\n")
    success = agent.register()
    
    if success:
        print("\n✅ REGISTRO EXITOSO")
        print(f"   Agent ID: {agent.asset_id}")
        print("\n💡 El agente está listo para comenzar a reportar datos.")
    else:
        print("\n❌ REGISTRO FALLIDO")
        print("   Verifica la configuración del servidor y vuelve a intentar.")
        sys.exit(1)


def mode_test(agent: Agent):
    """
    Modo: Probar recolección sin enviar
    """
    print("\n🧪 MODO: PRUEBA DE RECOLECCIÓN (sin enviar datos)\n")
    
    print("Recolectando datos del sistema...")
    data = agent.collect_all_data()
    
    print("\n" + "="*70)
    print("📊 DATOS RECOLECTADOS")
    print("="*70)
    
    # Mostrar resumen
    print(f"\n📅 Timestamp: {data.get('timestamp')}")
    print(f"🖥️  Hostname: {data.get('hostname')}")
    print(f"💻 OS: {data.get('os_type')}")
    
    print("\n📦 Módulos recolectados:")
    for key in data.keys():
        if key not in ['timestamp', 'hostname', 'os_type']:
            if isinstance(data[key], dict) and 'error' not in data[key]:
                print(f"   ✓ {key}")
            elif isinstance(data[key], dict) and 'error' in data[key]:
                print(f"   ✗ {key} (error: {data[key]['error']})")
            else:
                print(f"   ✓ {key}")
    
    # Guardar en archivo temporal
    test_file = 'test_collection.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Datos guardados en: {test_file}")
    print("\n✅ PRUEBA COMPLETADA")


def mode_once(agent: Agent):
    """
    Modo: Ejecutar una sola vez
    """
    print("\n🔄 MODO: EJECUCIÓN ÚNICA\n")
    
    print("Ejecutando ciclo de recolección y envío...")
    success = agent.run_once()
    
    if success:
        print("\n✅ CICLO COMPLETADO EXITOSAMENTE")
    else:
        print("\n⚠️  CICLO COMPLETADO CON ERRORES")
        sys.exit(1)


def mode_models(agent: Agent, location: str, department: str, assigned_to: str):
    """
    Modo: Usar modelos validados
    """
    print("\n📦 MODO: RECOLECCIÓN CON MODELOS VALIDADOS\n")
    
    print("Recolectando inventario con modelos...")
    print(f"  • Ubicación: {location or 'No especificada'}")
    print(f"  • Departamento: {department or 'No especificado'}")
    print(f"  • Asignado a: {assigned_to or 'No asignado'}")
    print()
    
    success = agent.send_inventory_with_models(
        location=location,
        department=department,
        assigned_to=assigned_to
    )
    
    if success:
        print("\n✅ INVENTARIO ENVIADO EXITOSAMENTE CON MODELOS VALIDADOS")
        if agent.asset_id:
            print(f"   Asset ID: {agent.asset_id}")
    else:
        print("\n❌ ERROR AL ENVIAR INVENTARIO")
        sys.exit(1)


def mode_export_models(agent: Agent, location: str, department: str, assigned_to: str, output_file: str):
    """
    Modo: Exportar modelos a JSON
    """
    print("\n💾 MODO: EXPORTAR INVENTARIO CON MODELOS\n")
    
    print("Recolectando inventario con modelos...")
    print(f"  • Ubicación: {location or 'No especificada'}")
    print(f"  • Departamento: {department or 'No especificado'}")
    print(f"  • Asignado a: {assigned_to or 'No asignado'}")
    print()
    
    try:
        # Recolectar usando modelos
        asset, hardware, software_list, raw_data = agent.collect_as_models(
            location=location,
            department=department,
            assigned_to=assigned_to
        )
        
        print("="*70)
        print("📊 RESUMEN DEL INVENTARIO")
        print("="*70)
        
        # Mostrar resumen
        print(f"\n📋 Asset:")
        print(f"   • Tag: {asset.asset_tag}")
        print(f"   • Nombre: {asset.name}")
        print(f"   • Tipo: {asset.asset_type.value}")
        print(f"   • Estado: {asset.status.value}")
        if asset.location:
            print(f"   • Ubicación: {asset.location.building}")
        
        print(f"\n💻 Hardware:")
        print(f"   • Fabricante: {hardware.manufacturer}")
        print(f"   • Modelo: {hardware.model}")
        print(f"   • Tipo: {hardware.type.value}")
        print(f"   • Procesador: {hardware.processor}")
        print(f"   • RAM: {hardware.ram_gb} GB")
        print(f"   • Almacenamiento: {hardware.storage_gb} GB")
        print(f"   • Componentes: {len(hardware.components)}")
        
        print(f"\n📦 Software:")
        print(f"   • Total programas: {len(software_list)}")
        
        # Contar por tipo
        software_by_type = {}
        for sw in software_list:
            sw_type = sw.software_type.value
            software_by_type[sw_type] = software_by_type.get(sw_type, 0) + 1
        
        print(f"   • Por tipo:")
        for sw_type, count in sorted(software_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {sw_type}: {count}")
        
        # Top 10 programas
        if software_list:
            print(f"\n   • Top 10 programas:")
            for i, sw in enumerate(software_list[:10], 1):
                version = f"v{sw.version}" if sw.version else "sin versión"
                print(f"     {i:2d}. {sw.name} ({version})")
        
        print(f"\n🔧 Datos adicionales:")
        for key in raw_data.keys():
            print(f"   • {key}: ✓")
        
        # Convertir a diccionarios
        inventory_data = {
            'metadata': {
                'export_date': agent.collect_all_data()['timestamp'],
                'agent_version': agent.VERSION,
                'hostname': agent.hostname
            },
            'asset': asset.to_dict(),
            'hardware': hardware.to_dict(),
            'software': [sw.to_dict() for sw in software_list],
            'additional_data': raw_data
        }
        
        # Guardar en archivo
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print(f"✅ INVENTARIO EXPORTADO EXITOSAMENTE")
        print(f"   Archivo: {output_path.absolute()}")
        print(f"   Tamaño: {output_path.stat().st_size / 1024:.2f} KB")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR AL EXPORTAR INVENTARIO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def mode_service(agent: Agent):
    """
    Modo: Servicio continuo (default)
    """
    print("\n⚙️  MODO: SERVICIO CONTINUO\n")
    agent.run()


def main():
    """
    Función principal
    """
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Imprimir banner
        print_banner()
        
        # Cargar configuración
        print(f"📂 Cargando configuración desde: {args.config}")
        config = Config(args.config)
        print("✓ Configuración cargada\n")
        
        # Crear agente
        print("🚀 Inicializando agente...")
        agent = Agent(config)
        print("✓ Agente inicializado\n")
        
        # Ejecutar según el modo
        if args.debug or args.validate:
            mode_debug(agent)
        
        elif args.register:
            mode_register(agent)
        
        elif args.test:
            mode_test(agent)
        
        elif args.once:
            mode_once(agent)
        
        elif args.models:
            mode_models(agent, args.location, args.department, args.assigned_to)
        
        elif args.export_models:
            mode_export_models(agent, args.location, args.department, args.assigned_to, args.output)
        
        else:
            # Modo servicio continuo (default)
            mode_service(agent)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción de usuario detectada")
        print("👋 Cerrando agente...")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()