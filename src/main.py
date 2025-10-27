#!/usr/bin/env python3
"""
IT Monitoring Agent - Main Entry Point
Version: 1.0.0
Description: Agente de monitoreo de activos de TI multiplataforma
"""

import sys
import os
import argparse
import signal
import time
from pathlib import Path

# Agregar el directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Imports del agente (los crearemos después)
try:
    from src.core.logger import setup_logger
    from src.core.config import Config
    from src.core.agent import Agent
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("⚠️  Asegúrate de tener la estructura correcta del proyecto")
    sys.exit(1)

# Versión del agente
VERSION = "1.0.0"

# Logger global
logger = None


def signal_handler(signum, frame):
    """
    Maneja las señales del sistema (Ctrl+C, etc.)
    """
    if logger:
        logger.info("🛑 Señal de terminación recibida. Deteniendo agente...")
    print("\n🛑 Deteniendo agente...")
    sys.exit(0)


def show_banner():
    """
    Muestra el banner de inicio del agente
    """
    banner = f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          🖥️  IT MONITORING AGENT v{VERSION}              ║
║                                                          ║
║          Agente de Monitoreo de Activos TI              ║
║          Multiplataforma: Windows | Linux | macOS       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
    """
    parser = argparse.ArgumentParser(
        description='IT Monitoring Agent - Agente de monitoreo de activos TI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                          Ejecutar en modo continuo
  %(prog)s --once                   Ejecutar una sola vez
  %(prog)s --config custom.ini      Usar archivo de configuración personalizado
  %(prog)s --register               Registrar agente en el servidor
  %(prog)s --test                   Probar recolección de datos (sin enviar)
  %(prog)s --version                Mostrar versión
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/agent.ini',
        help='Ruta al archivo de configuración (default: config/agent.ini)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Ejecutar una sola vez en lugar de modo continuo'
    )
    
    parser.add_argument(
        '--register',
        action='store_true',
        help='Registrar el agente en el servidor'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Modo prueba: recopilar datos sin enviarlos al servidor'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug (logging detallado)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'IT Monitoring Agent v{VERSION}'
    )
    
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='No mostrar el banner de inicio'
    )
    
    return parser.parse_args()


def check_requirements():
    """
    Verifica que se cumplan los requisitos básicos
    """
    errors = []
    
    # Verificar versión de Python
    if sys.version_info < (3, 8):
        errors.append(f"Python 3.8+ requerido. Versión actual: {sys.version}")
    
    # Verificar que existe el directorio de logs
    logs_dir = ROOT_DIR / "logs"
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(parents=True)
        except Exception as e:
            errors.append(f"No se pudo crear el directorio de logs: {e}")
    
    # Verificar que existe el directorio de configuración
    config_dir = ROOT_DIR / "config"
    if not config_dir.exists():
        errors.append("No existe el directorio 'config'. Por favor créalo.")
    
    if errors:
        print("❌ Errores de requisitos:\n")
        for error in errors:
            print(f"  • {error}")
        return False
    
    return True


def run_once_mode(agent):
    """
    Ejecuta el agente una sola vez
    """
    logger.info("🔄 Modo ejecución única activado")
    
    try:
        agent.run_once()
        logger.info("✅ Ejecución única completada exitosamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error en ejecución única: {e}", exc_info=True)
        return False


def run_continuous_mode(agent):
    """
    Ejecuta el agente en modo continuo
    """
    logger.info("🔄 Modo continuo activado")
    logger.info(f"📊 Reportando cada {agent.config.get('agent', 'report_interval')} segundos")
    
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("🛑 Agente detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en modo continuo: {e}", exc_info=True)
        return False
    
    return True


def run_test_mode(agent):
    """
    Ejecuta el agente en modo prueba (sin enviar datos)
    """
    logger.info("🧪 Modo prueba activado - NO se enviarán datos al servidor")
    
    try:
        data = agent.collect_all_data()
        
        print("\n" + "="*60)
        print("📊 DATOS RECOPILADOS (Modo Prueba)")
        print("="*60 + "\n")
        
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print("\n" + "="*60)
        print("✅ Recopilación exitosa - Datos NO enviados (modo prueba)")
        print("="*60 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en modo prueba: {e}", exc_info=True)
        return False


def run_register_mode(agent):
    """
    Registra el agente en el servidor
    """
    logger.info("📝 Registrando agente en el servidor...")
    
    try:
        result = agent.register()
        
        if result:
            logger.info("✅ Agente registrado exitosamente")
            logger.info(f"📋 ID del activo: {agent.asset_id}")
            print(f"\n✅ Agente registrado exitosamente")
            print(f"📋 ID del activo: {agent.asset_id}")
            print(f"💾 Configuración actualizada en: {agent.config.config_file}")
            return True
        else:
            logger.error("❌ No se pudo registrar el agente")
            print("\n❌ No se pudo registrar el agente. Revisa los logs para más detalles.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al registrar agente: {e}", exc_info=True)
        return False


def main():
    """
    Función principal
    """
    global logger
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Mostrar banner
    if not args.no_banner:
        show_banner()
    
    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Setup logger
        log_level = 'DEBUG' if args.debug else 'INFO'
        logger = setup_logger(level=log_level)
        
        logger.info("="*60)
        logger.info(f"🚀 Iniciando IT Monitoring Agent v{VERSION}")
        logger.info(f"🖥️  Sistema operativo: {sys.platform}")
        logger.info(f"🐍 Python: {sys.version.split()[0]}")
        logger.info("="*60)
        
        # Cargar configuración
        logger.info(f"📂 Cargando configuración desde: {args.config}")
        config = Config(args.config)
        
        if not config.validate():
            logger.error("❌ Configuración inválida. Revisa el archivo de configuración.")
            print("❌ Configuración inválida. Revisa el archivo de configuración.")
            sys.exit(1)
        
        logger.info("✅ Configuración cargada correctamente")
        
        # Crear instancia del agente
        logger.info("🔧 Inicializando agente...")
        agent = Agent(config)
        logger.info("✅ Agente inicializado correctamente")
        
        # Determinar modo de ejecución
        success = True
        
        if args.register:
            # Modo registro
            success = run_register_mode(agent)
        elif args.test:
            # Modo prueba
            success = run_test_mode(agent)
        elif args.once:
            # Modo ejecución única
            success = run_once_mode(agent)
        else:
            # Modo continuo (default)
            success = run_continuous_mode(agent)
        
        # Salir con código apropiado
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")
        if logger:
            logger.error(f"Archivo no encontrado: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        if logger:
            logger.error(f"Error inesperado: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()