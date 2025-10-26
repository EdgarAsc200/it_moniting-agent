# IT Monitoring Agent

Agente de monitoreo de activos de TI multiplataforma.

## Requisitos

- Python 3.8+
- pip

## Instalación

1. Clonar el repositorio
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno: `source venv/bin/activate` (Linux/Mac) o `.\venv\Scripts\activate` (Windows)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Copiar config: `cp config/agent.ini.example config/agent.ini`
6. Configurar `config/agent.ini` con tus datos

## Uso
```bash
python src/main.py
```

## Desarrollo

En desarrollo...