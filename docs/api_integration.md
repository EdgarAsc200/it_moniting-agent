# 🔌 API Integration Guide

Guía para integrar el IT Monitoring Agent con tu sistema backend.

---

## 📡 Endpoints Requeridos

El agente espera que tu servidor implemente los siguientes endpoints:

### 1. Registro de Agente

**Endpoint:** `POST /api/agents/register`

**Request:**
```json
{
  "hostname": "LAPTOP-USER-01",
  "os_type": "Windows",
  "os_version": "10.0.19045",
  "agent_version": "1.0.0"
}
```

**Response:**
```json
{
  "success": true,
  "agent_id": 123,
  "message": "Agent registered successfully"
}
```

---

### 2. Envío de Inventario

**Endpoint:** `POST /api/inventory`

**Headers:**
```
Content-Type: application/json
X-Agent-ID: 123
X-Agent-Version: 1.0.0
```

**Request:**
```json
{
  "agent_id": 123,
  "timestamp": "2025-11-01T12:00:00",
  "hostname": "LAPTOP-USER-01",
  "hardware": {
    "processor": "Intel Core i7",
    "ram_gb": 16,
    "total_disk_gb": 512
  },
  "software": {
    "total_software": 150,
    "installed_software": [...]
  },
  "domain": {
    "is_domain_joined": true,
    "domain_name": "EMPRESA.LOCAL"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Inventory received",
  "next_report_in": 300
}
```

---

### 3. Verificación de Actualizaciones

**Endpoint:** `GET /api/updates/check`

**Headers:**
```
X-Agent-ID: 123
X-Agent-Version: 1.0.0
```

**Response:**
```json
{
  "update_available": true,
  "latest_version": "1.1.0",
  "download_url": "https://cdn.example.com/agent-1.1.0.zip",
  "changelog": "- Nueva funcionalidad\n- Correcciones de bugs"
}
```

---

### 4. Health Check

**Endpoint:** `GET /api/agents/{agent_id}/health`

**Response:**
```json
{
  "status": "ok",
  "server_time": "2025-11-01T12:00:00Z",
  "message": "Agent is healthy"
}
```

---

## 🔐 Autenticación

### Opción 1: API Key
```ini
[api]
api_key = your-secret-api-key-here
```

Headers:
```
Authorization: Bearer your-secret-api-key-here
```

### Opción 2: JWT Token
```ini
[api]
auth_type = jwt
jwt_token = eyJhbGciOiJIUzI1NiIs...
```

Headers:
```
Authorization: JWT eyJhbGciOiJIUzI1NiIs...
```

---

## 📊 Formato de Datos

### Hardware Data
```json
{
  "report_date": "2025-11-01T12:00:00",
  "hostname": "LAPTOP-01",
  "operating_system": "Windows",
  "os_version": "10.0.19045",
  "architecture": "AMD64",
  "processor": "Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz",
  "processor_cores": 8,
  "processor_threads": 16,
  "processor_speed": 2.9,
  "total_ram_gb": 16.0,
  "available_ram_gb": 8.5,
  "total_disk_gb": 512.0,
  "available_disk_gb": 256.0,
  "system_info": {
    "manufacturer": "Dell Inc.",
    "model": "OptiPlex 7090",
    "serial_number": "XXXXX123"
  }
}
```

### Software Data
```json
{
  "report_date": "2025-11-01T12:00:00",
  "total_software": 150,
  "installed_software": [
    {
      "software_name": "Google Chrome",
      "version": "120.0.6099.109",
      "vendor": "Google LLC",
      "install_date": "20240115",
      "install_location": "C:\\Program Files\\Google\\Chrome"
    }
  ]
}
```

### Domain Data
```json
{
  "report_date": "2025-11-01T12:00:00",
  "is_domain_joined": true,
  "domain_name": "EMPRESA.LOCAL",
  "domain_user": "username",
  "workgroup": null,
  "domain_controller": "DC01.EMPRESA.LOCAL"
}
```

---

## 🔄 Flujo de Comunicación
```
┌─────────┐                  ┌─────────┐
│  Agent  │                  │  Server │
└────┬────┘                  └────┬────┘
     │                            │
     │  POST /agents/register     │
     │──────────────────────────>│
     │                            │
     │  {agent_id: 123}           │
     │<──────────────────────────│
     │                            │
     │  POST /inventory           │
     │  (every 5 minutes)         │
     │──────────────────────────>│
     │                            │
     │  {success: true}           │
     │<──────────────────────────│
     │                            │
     │  GET /updates/check        │
     │  (daily)                   │
     │──────────────────────────>│
     │                            │
     │  {update_available: false} │
     │<──────────────────────────│
     │                            │
```

---

## 🚀 Ejemplo de Backend (FastAPI)
```python
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class AgentRegistration(BaseModel):
    hostname: str
    os_type: str
    os_version: str
    agent_version: str

class InventoryData(BaseModel):
    agent_id: int
    timestamp: str
    hostname: str
    hardware: dict
    software: dict
    domain: dict

@app.post("/api/agents/register")
async def register_agent(data: AgentRegistration):
    # Crear nuevo agente en base de datos
    agent_id = create_agent_in_db(data)
    
    return {
        "success": True,
        "agent_id": agent_id,
        "message": "Agent registered successfully"
    }

@app.post("/api/inventory")
async def receive_inventory(
    data: InventoryData,
    x_agent_id: int = Header(None),
    x_agent_version: str = Header(None)
):
    # Validar agente
    if not validate_agent(x_agent_id):
        raise HTTPException(status_code=401, detail="Invalid agent")
    
    # Guardar inventario
    save_inventory_to_db(data)
    
    return {
        "success": True,
        "message": "Inventory received",
        "next_report_in": 300
    }

@app.get("/api/updates/check")
async def check_updates(
    x_agent_id: int = Header(None),
    x_agent_version: str = Header(None)
):
    latest_version = get_latest_version()
    
    if latest_version > x_agent_version:
        return {
            "update_available": True,
            "latest_version": latest_version,
            "download_url": f"https://cdn.example.com/agent-{latest_version}.zip"
        }
    
    return {
        "update_available": False
    }
```

---

## 🗄️ Ejemplo de Base de Datos

### Schema SQL
```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    os_type VARCHAR(50),
    os_version VARCHAR(100),
    agent_version VARCHAR(20),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_snapshots (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    snapshot_date TIMESTAMP NOT NULL,
    hardware_data JSONB,
    software_data JSONB,
    domain_data JSONB,
    network_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE software_inventory (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    software_name VARCHAR(255),
    version VARCHAR(100),
    vendor VARCHAR(255),
    install_date DATE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📝 Webhooks (Opcional)

El servidor puede enviar webhooks al agente para acciones específicas:

### Force Update Check
```
POST http://agent-host:5000/api/webhook/update
```

### Force Data Collection
```
POST http://agent-host:5000/api/webhook/collect
```

---

## 🧪 Testing del API
```bash
# Registrar agente
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "TEST-LAPTOP",
    "os_type": "Windows",
    "os_version": "10.0.19045",
    "agent_version": "1.0.0"
  }'

# Enviar inventario
curl -X POST http://localhost:8000/api/inventory \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: 123" \
  -H "X-Agent-Version: 1.0.0" \
  -d @test_inventory.json
```

---

## 📞 Soporte

- 📧 Email: api-support@tuempresa.com
- 📚 API Docs: https://api-docs.tuempresa.com
- 💬 Swagger: https://api.tuempresa.com/docs
