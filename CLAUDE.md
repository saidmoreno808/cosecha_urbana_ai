# 🌱 CLAUDE.md — cosecha_urbana_ai
## Pipeline Completo de Desarrollo · Nivel Senior Engineer

> **Proyecto:** cosecha_urbana_ai  
> **Hackathon:** Elasticsearch Agent Builder Hackathon 2026  
> **Objetivo:** Agente multi-paso que redistribuye excedentes alimentarios de centros comerciales hacia refugios, casas del migrante, asilos y orfanatos  
> **Stack:** Python · FastAPI · Elasticsearch · Agent Builder · LangChain/LangGraph · Docker · Kibana

---

## 📋 TABLA DE CONTENIDOS

1. [Arquitectura del Sistema](#arquitectura)
2. [Estructura de Directorios](#estructura)
3. [Fase 0 — Setup y Entorno](#fase-0)
4. [Fase 1 — Modelos de Datos y Elasticsearch](#fase-1)
5. [Fase 2 — Backend API (FastAPI)](#fase-2)
6. [Fase 3 — Agente IA (Agent Builder + LangGraph)](#fase-3)
7. [Fase 4 — Workflows y Notificaciones](#fase-4)
8. [Fase 5 — Dashboard Kibana + Frontend](#fase-5)
9. [Fase 6 — Testing](#fase-6)
10. [Fase 7 — Docker y Deployment](#fase-7)
11. [Fase 8 — Submission del Hackathon](#fase-8)
12. [Comandos de Referencia Rápida](#comandos)
13. [Reglas de Calidad SR](#reglas-sr)

---

## 🏗️ ARQUITECTURA DEL SISTEMA {#arquitectura}

```
┌─────────────────────────────────────────────────────────────────────┐
│                        cosecha_urbana_ai                            │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────────────────────────────┐  │
│  │   DONORS     │    │           ORCHESTRATOR AGENT              │  │
│  │  (Webhook)   │───▶│                                          │  │
│  │  Mall/Market │    │  ┌─────────┐  ┌────────┐  ┌──────────┐ │  │
│  └──────────────┘    │  │ Planner │─▶│Executor│─▶│Validator │ │  │
│                      │  └─────────┘  └────────┘  └──────────┘ │  │
│  ┌──────────────┐    │       │            │            │        │  │
│  │  RECIPIENTS  │    │  LangGraph State Machine (multi-step)   │  │
│  │  (Refugios)  │◀───│                                          │  │
│  └──────────────┘    └──────────────────┬───────────────────────┘  │
│                                         │                           │
│  ┌─────────────────────────────────────▼───────────────────────┐   │
│  │                    ELASTICSEARCH LAYER                       │   │
│  │                                                              │   │
│  │  [donors_index]  [recipients_index]  [food_alerts_index]    │   │
│  │  [donations_history]  [routes_index]  [analytics_index]     │   │
│  │                                                              │   │
│  │  Tools: ES Search · ES|QL · Vector Search · Geo Search      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐     │
│  │  FastAPI     │    │    Kibana     │    │  Notifications   │     │
│  │  REST API    │    │  Dashboard   │    │  (WhatsApp/Slack) │     │
│  └──────────────┘    └───────────────┘    └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

### Flujo de datos del agente (5 pasos)

```
PASO 1: INGEST     → Recibe alerta de excedente vía webhook
PASO 2: ANALYZE    → ES|QL analiza urgencia + tiempo de vida
PASO 3: MATCH      → Vector Search + Geo encuentra receptor óptimo
PASO 4: EXECUTE    → Elastic Workflows crea ruta y notifica
PASO 5: RECORD     → Registra donación + actualiza analytics
```

---

## 📁 ESTRUCTURA DE DIRECTORIOS {#estructura}

```
cosecha_urbana_ai/
├── CLAUDE.md                          ← Este archivo
├── README.md
├── LICENSE                            ← MIT License (requerido OSI)
├── .env.example
├── .env                               ← NO commitear
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
├── Makefile
│
├── pyproject.toml                     ← Gestión de dependencias (uv/poetry)
├── requirements.txt
├── requirements-dev.txt
│
├── src/
│   └── cosecha_urbana_ai/
│       ├── __init__.py
│       ├── config.py                  ← Configuración centralizada (Pydantic Settings)
│       │
│       ├── api/                       ← FastAPI routes
│       │   ├── __init__.py
│       │   ├── main.py               ← App entry point
│       │   ├── dependencies.py       ← DI: ES client, agent, etc.
│       │   ├── middleware.py         ← CORS, logging, auth
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── donors.py
│       │       ├── recipients.py
│       │       ├── alerts.py
│       │       ├── donations.py
│       │       ├── agent.py          ← Endpoint para invocar el agente
│       │       └── health.py
│       │
│       ├── models/                    ← Pydantic models (contratos de datos)
│       │   ├── __init__.py
│       │   ├── donor.py
│       │   ├── recipient.py
│       │   ├── food_alert.py
│       │   ├── donation.py
│       │   ├── route.py
│       │   └── agent_state.py        ← LangGraph state schema
│       │
│       ├── elasticsearch/             ← Todo lo relacionado con ES
│       │   ├── __init__.py
│       │   ├── client.py             ← Singleton ES client
│       │   ├── indices.py            ← Definición de mappings + settings
│       │   ├── repositories/         ← Patrón Repository
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── donor_repo.py
│       │   │   ├── recipient_repo.py
│       │   │   ├── alert_repo.py
│       │   │   └── donation_repo.py
│       │   └── queries/              ← ES|QL y DSL queries
│       │       ├── __init__.py
│       │       ├── esql_queries.py   ← Queries ES|QL analíticas
│       │       ├── geo_queries.py    ← Búsquedas por proximidad
│       │       └── vector_queries.py ← kNN / semantic search
│       │
│       ├── agent/                     ← Núcleo del agente IA
│       │   ├── __init__.py
│       │   ├── graph.py              ← LangGraph StateGraph definition
│       │   ├── state.py              ← AgentState TypedDict
│       │   ├── nodes/                ← Nodos del grafo
│       │   │   ├── __init__.py
│       │   │   ├── ingest_node.py
│       │   │   ├── analyze_node.py
│       │   │   ├── match_node.py
│       │   │   ├── execute_node.py
│       │   │   └── validate_node.py
│       │   ├── tools/                ← Tools que usa el agente
│       │   │   ├── __init__.py
│       │   │   ├── search_tool.py    ← ES Search tool
│       │   │   ├── esql_tool.py      ← ES|QL tool
│       │   │   ├── geo_tool.py       ← Geo distance tool
│       │   │   ├── notify_tool.py    ← Notification tool
│       │   │   └── route_tool.py     ← Route optimization tool
│       │   └── prompts/              ← System prompts del agente
│       │       ├── __init__.py
│       │       ├── planner.py
│       │       ├── analyzer.py
│       │       └── matcher.py
│       │
│       ├── workflows/                 ← Elastic Workflows / coordinación
│       │   ├── __init__.py
│       │   ├── donation_workflow.py
│       │   └── notification_workflow.py
│       │
│       ├── notifications/             ← Capa de notificaciones
│       │   ├── __init__.py
│       │   ├── base.py               ← Abstract notifier
│       │   ├── whatsapp.py
│       │   └── slack.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logging.py            ← Structured logging (structlog)
│           ├── metrics.py            ← Métricas de impacto
│           └── seed_data.py          ← Datos de prueba (Monterrey)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   ← Fixtures compartidos
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_repositories.py
│   │   ├── test_agent_nodes.py
│   │   └── test_tools.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_elasticsearch.py
│   │   └── test_agent_flow.py
│   └── e2e/
│       └── test_full_pipeline.py
│
├── scripts/
│   ├── setup_indices.py              ← Crea índices en ES
│   ├── seed_database.py              ← Carga datos de prueba
│   ├── run_demo.py                   ← Demo script para video
│   └── benchmark.py                 ← Métricas de performance
│
├── kibana/
│   ├── dashboards/
│   │   └── cosecha_urbana_dashboard.ndjson
│   └── index_patterns/
│
├── docs/
│   ├── architecture.md
│   ├── api_reference.md
│   ├── agent_design.md
│   └── hackathon_submission.md
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── lint.yml
```

---

## FASE 0 — Setup y Entorno {#fase-0}

### 0.1 Herramientas requeridas

```bash
# Verificar versiones mínimas
python --version       # >= 3.11
docker --version       # >= 24.0
docker compose version # >= 2.20
node --version         # >= 18 (para Kibana tooling)
git --version

# Instalar uv (gestor de paquetes moderno y rápido)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 0.2 Inicializar el proyecto

```bash
# Crear directorio y repositorio
mkdir cosecha_urbana_ai && cd cosecha_urbana_ai
git init
git checkout -b main

# Inicializar proyecto Python con uv
uv init --name cosecha-urbana-ai --python 3.11
uv venv --python 3.11
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Crear estructura de directorios completa
mkdir -p src/cosecha_urbana_ai/{api/routers,models,elasticsearch/{repositories,queries},agent/{nodes,tools,prompts},workflows,notifications,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts kibana/{dashboards,index_patterns} docs .github/workflows

# Crear __init__.py en todos los paquetes
find src tests -type d | xargs -I {} touch {}/__init__.py
```

### 0.3 Dependencias (pyproject.toml)

```toml
# pyproject.toml
[project]
name = "cosecha-urbana-ai"
version = "0.1.0"
description = "AI agent for food waste redistribution from malls to shelters"
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">=3.11"
authors = [
    {name = "Tu Nombre", email = "tu@email.com"}
]

[project.urls]
Repository = "https://github.com/tu-usuario/cosecha_urbana_ai"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "httpx>=0.27",          # AsyncClient para tests
    "faker>=24.0",
    "ruff>=0.4",            # Linter + formatter
    "mypy>=1.9",
    "pre-commit>=3.7",
]

[project.dependencies]
# API
fastapi = ">=0.111"
uvicorn = {extras = ["standard"], version = ">=0.29"}
pydantic = ">=2.7"
pydantic-settings = ">=2.3"

# Elasticsearch
elasticsearch = {extras = ["async"], version = ">=8.13"}

# Agent / LLM
langchain = ">=0.2"
langchain-anthropic = ">=0.1"    # Claude como LLM
langchain-elasticsearch = ">=0.2"
langgraph = ">=0.1"
anthropic = ">=0.28"

# Utilities
httpx = ">=0.27"
structlog = ">=24.1"             # Structured logging
tenacity = ">=8.3"               # Retry logic
python-dotenv = ">=1.0"

# Geo
geopy = ">=2.4"

# Async
anyio = ">=4.3"
```

```bash
# Instalar dependencias
uv sync

# Instalar dev tools
uv sync --dev
```

### 0.4 Variables de entorno (.env.example)

```bash
# .env.example — copiar a .env y completar

# ═══ ELASTICSEARCH ════════════════════════════════════
ELASTICSEARCH_URL=https://localhost:9200
ELASTICSEARCH_API_KEY=your_api_key_here
ELASTICSEARCH_INDEX_PREFIX=cosecha_urbana
# Para Elastic Cloud:
# ELASTIC_CLOUD_ID=your_cloud_id
# ELASTIC_API_KEY=your_api_key

# ═══ LLM (Anthropic Claude) ═══════════════════════════
ANTHROPIC_API_KEY=your_anthropic_api_key
LLM_MODEL=claude-opus-4-6            # o claude-sonnet-4-6 para dev
LLM_TEMPERATURE=0.1                   # Bajo para agentes deterministas
LLM_MAX_TOKENS=4096

# ═══ FASTAPI ══════════════════════════════════════════
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_SECRET_KEY=change_this_in_production
CORS_ORIGINS=["http://localhost:3000","http://localhost:5601"]

# ═══ NOTIFICACIONES ═══════════════════════════════════
WHATSAPP_API_TOKEN=your_token
WHATSAPP_PHONE_ID=your_phone_id
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=C0XXXXXX

# ═══ CONFIGURACIÓN DEL AGENTE ═════════════════════════
AGENT_MAX_STEPS=10
AGENT_TIMEOUT_SECONDS=120
MAX_DISTANCE_KM=15                    # Radio máximo de redistribución
FOOD_URGENCY_THRESHOLD_HOURS=4        # Menos de 4h = urgente

# ═══ LOGGING ══════════════════════════════════════════
LOG_LEVEL=INFO
LOG_FORMAT=json                       # json | console
```

### 0.5 Configuración central (src/cosecha_urbana_ai/config.py)

```python
# src/cosecha_urbana_ai/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
from typing import list
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Elasticsearch
    elasticsearch_url: AnyHttpUrl = "https://localhost:9200"
    elasticsearch_api_key: str
    elasticsearch_index_prefix: str = "cosecha_urbana"
    elastic_cloud_id: str | None = None

    # LLM
    anthropic_api_key: str
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_secret_key: str
    cors_origins: list[str] = ["http://localhost:3000"]

    # Notificaciones
    whatsapp_api_token: str | None = None
    whatsapp_phone_id: str | None = None
    slack_bot_token: str | None = None
    slack_channel_id: str | None = None

    # Agente
    agent_max_steps: int = 10
    agent_timeout_seconds: int = 120
    max_distance_km: float = 15.0
    food_urgency_threshold_hours: int = 4

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def donors_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_donors"

    @property
    def recipients_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_recipients"

    @property
    def food_alerts_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_food_alerts"

    @property
    def donations_history_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_donations_history"

    @property
    def routes_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_routes"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

### 0.6 .gitignore

```bash
# .gitignore
.env
.venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
*.egg-info/
.DS_Store
*.log
coverage.xml
.coverage
htmlcov/
node_modules/
```

---

## FASE 1 — Modelos de Datos y Elasticsearch {#fase-1}

### 1.1 Modelos Pydantic

**INSTRUCCIÓN PARA CLAUDE CODE:** Crear todos los modelos con validaciones estrictas, usa `model_config = ConfigDict(str_strip_whitespace=True)` en todos. Los campos de coordenadas deben validar rangos geográficos válidos para México.

```python
# src/cosecha_urbana_ai/models/food_alert.py
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class FoodCategory(str, Enum):
    PREPARED = "prepared"        # Comida preparada (más urgente)
    BAKERY = "bakery"
    PRODUCE = "produce"          # Frutas y verduras
    DAIRY = "dairy"
    MEAT = "meat"
    DRY_GOODS = "dry_goods"      # Granos, enlatados (menos urgente)


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"        # < 2 horas
    HIGH = "high"                # 2-4 horas
    MEDIUM = "medium"            # 4-12 horas
    LOW = "low"                  # > 12 horas


class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class FoodAlert(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    donor_id: str
    donor_name: str
    food_category: FoodCategory
    description: str = Field(..., min_length=10, max_length=500)
    quantity_kg: float = Field(..., gt=0, le=1000)
    
    # Tiempo de vida
    expiry_datetime: datetime
    alert_created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # Geolocalización
    location: GeoPoint
    address: str
    
    # Estado
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    is_active: bool = True
    matched_recipient_id: Optional[str] = None
    
    # Metadata
    special_requirements: list[str] = []  # e.g., ["refrigeration", "same_day"]
    
    @field_validator("expiry_datetime")
    @classmethod
    def expiry_must_be_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError("Expiry datetime must be in the future")
        return v
    
    @property
    def hours_until_expiry(self) -> float:
        now = datetime.now(timezone.utc)
        expiry = self.expiry_datetime
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        delta = expiry - now
        return delta.total_seconds() / 3600
    
    def compute_urgency(self) -> UrgencyLevel:
        hours = self.hours_until_expiry
        if hours < 2:
            return UrgencyLevel.CRITICAL
        elif hours < 4:
            return UrgencyLevel.HIGH
        elif hours < 12:
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.LOW
```

```python
# src/cosecha_urbana_ai/models/donor.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from .food_alert import GeoPoint, FoodCategory


class OperatingHours(BaseModel):
    open: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # HH:MM
    close: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    days: list[str]  # ["monday", "tuesday", ...]


class Donor(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    business_type: str  # "restaurant", "supermarket", "food_court", etc.
    contact_name: str
    contact_phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    contact_email: EmailStr
    
    # Ubicación
    location: GeoPoint
    address: str
    city: str = "Monterrey"
    state: str = "Nuevo León"
    
    # Capacidad y preferencias
    typical_food_categories: list[FoodCategory] = []
    operating_hours: OperatingHours
    has_refrigeration: bool = False
    average_kg_per_donation: float = Field(default=10.0, gt=0)
    
    # Estado
    is_active: bool = True
    is_verified: bool = False
    total_donations: int = 0
    total_kg_donated: float = 0.0
    
    # Metadata
    registered_at: str | None = None  # ISO datetime string
    notes: str = ""
    
    # Vector embedding para semantic matching
    description_vector: list[float] | None = None
```

```python
# src/cosecha_urbana_ai/models/recipient.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from .food_alert import GeoPoint, FoodCategory


class RecipientType(str):
    MIGRANT_HOUSE = "migrant_house"
    ELDERLY_SHELTER = "elderly_shelter"
    ORPHANAGE = "orphanage"
    FOOD_BANK = "food_bank"
    COMMUNITY_KITCHEN = "community_kitchen"


class DietaryRestriction(str):
    VEGETARIAN = "vegetarian"
    DIABETIC_FRIENDLY = "diabetic_friendly"
    LOW_SODIUM = "low_sodium"
    HALAL = "halal"
    NUT_FREE = "nut_free"


class StorageCapacity(BaseModel):
    refrigerated_kg: float = 0.0
    frozen_kg: float = 0.0
    dry_kg: float = 0.0


class Recipient(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    organization_type: str
    contact_name: str
    contact_phone: str
    contact_email: EmailStr
    
    # Ubicación
    location: GeoPoint
    address: str
    city: str = "Monterrey"
    state: str = "Nuevo León"
    
    # Capacidad y necesidades
    beneficiaries_count: int = Field(..., gt=0)
    accepted_food_categories: list[FoodCategory] = []
    dietary_restrictions: list[str] = []
    storage_capacity: StorageCapacity = StorageCapacity()
    
    # Disponibilidad
    receiving_hours_start: str = "08:00"
    receiving_hours_end: str = "20:00"
    available_days: list[str] = ["monday","tuesday","wednesday","thursday","friday"]
    
    # Estado
    is_active: bool = True
    is_verified: bool = True
    current_need_level: str = "medium"  # low | medium | high | critical
    
    # Historial
    total_donations_received: int = 0
    total_kg_received: float = 0.0
    
    # Para matching semántico
    needs_description: str = ""
    needs_vector: list[float] | None = None
```

```python
# src/cosecha_urbana_ai/models/agent_state.py
from typing import TypedDict, Annotated, Optional
from datetime import datetime
from .food_alert import FoodAlert
from .recipient import Recipient
from .route import Route


class AgentState(TypedDict):
    """Estado compartido del grafo LangGraph."""
    
    # Input
    alert_id: str
    alert: Optional[FoodAlert]
    
    # Análisis
    urgency_score: float          # 0.0 - 1.0
    priority_rank: int
    analysis_reasoning: str
    
    # Matching
    candidate_recipients: list[Recipient]
    selected_recipient: Optional[Recipient]
    match_score: float
    match_reasoning: str
    distance_km: float
    
    # Ejecución
    route: Optional[Route]
    notifications_sent: list[str]
    execution_status: str         # pending | in_progress | completed | failed
    
    # Validación
    validation_passed: bool
    validation_notes: str
    
    # Metadata
    steps_taken: list[str]
    errors: list[str]
    started_at: str
    completed_at: Optional[str]
    
    # Mensajes del agente (para LangGraph)
    messages: Annotated[list, "messages"]
```

### 1.2 Elasticsearch — Índices y Mappings

**INSTRUCCIÓN PARA CLAUDE CODE:** Crear el archivo `indices.py` con todos los mappings. Los campos `location` deben ser tipo `geo_point`. Los campos de texto que se usarán para búsqueda semántica deben tener un campo `_vector` adicional de tipo `dense_vector` con 1536 dimensiones (OpenAI/Anthropic compatible).

```python
# src/cosecha_urbana_ai/elasticsearch/indices.py

DONORS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "spanish",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "business_type": {"type": "keyword"},
            "contact_phone": {"type": "keyword"},
            "contact_email": {"type": "keyword"},
            "location": {"type": "geo_point"},
            "address": {"type": "text", "analyzer": "spanish"},
            "city": {"type": "keyword"},
            "state": {"type": "keyword"},
            "typical_food_categories": {"type": "keyword"},
            "has_refrigeration": {"type": "boolean"},
            "average_kg_per_donation": {"type": "float"},
            "is_active": {"type": "boolean"},
            "is_verified": {"type": "boolean"},
            "total_donations": {"type": "integer"},
            "total_kg_donated": {"type": "float"},
            "registered_at": {"type": "date"},
            "notes": {"type": "text", "analyzer": "spanish"},
            # Vector para semantic search
            "description_vector": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "similarity": "cosine"
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "spanish": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "spanish_stop", "spanish_stemmer"]
                }
            },
            "filter": {
                "spanish_stop": {
                    "type": "stop",
                    "stopwords": "_spanish_"
                },
                "spanish_stemmer": {
                    "type": "stemmer",
                    "language": "spanish"
                }
            }
        }
    }
}

FOOD_ALERTS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "donor_id": {"type": "keyword"},
            "donor_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "food_category": {"type": "keyword"},
            "description": {"type": "text", "analyzer": "spanish"},
            "quantity_kg": {"type": "float"},
            "expiry_datetime": {"type": "date"},
            "alert_created_at": {"type": "date"},
            "location": {"type": "geo_point"},
            "address": {"type": "text"},
            "urgency_level": {"type": "keyword"},
            "is_active": {"type": "boolean"},
            "matched_recipient_id": {"type": "keyword"},
            "special_requirements": {"type": "keyword"},
            # Calculado al indexar
            "hours_until_expiry": {"type": "float"},
            "urgency_score": {"type": "float"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}

RECIPIENTS_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "spanish",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "organization_type": {"type": "keyword"},
            "contact_phone": {"type": "keyword"},
            "location": {"type": "geo_point"},
            "address": {"type": "text"},
            "city": {"type": "keyword"},
            "beneficiaries_count": {"type": "integer"},
            "accepted_food_categories": {"type": "keyword"},
            "dietary_restrictions": {"type": "keyword"},
            "storage_capacity": {
                "properties": {
                    "refrigerated_kg": {"type": "float"},
                    "frozen_kg": {"type": "float"},
                    "dry_kg": {"type": "float"}
                }
            },
            "receiving_hours_start": {"type": "keyword"},
            "receiving_hours_end": {"type": "keyword"},
            "available_days": {"type": "keyword"},
            "is_active": {"type": "boolean"},
            "is_verified": {"type": "boolean"},
            "current_need_level": {"type": "keyword"},
            "total_kg_received": {"type": "float"},
            "needs_description": {"type": "text", "analyzer": "spanish"},
            "needs_vector": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "similarity": "cosine"
            }
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0}
}

DONATIONS_HISTORY_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "alert_id": {"type": "keyword"},
            "donor_id": {"type": "keyword"},
            "donor_name": {"type": "keyword"},
            "recipient_id": {"type": "keyword"},
            "recipient_name": {"type": "keyword"},
            "food_category": {"type": "keyword"},
            "quantity_kg": {"type": "float"},
            "distance_km": {"type": "float"},
            "urgency_level": {"type": "keyword"},
            "status": {"type": "keyword"},  # completed | cancelled | failed
            "coordination_time_minutes": {"type": "float"},
            "pickup_location": {"type": "geo_point"},
            "delivery_location": {"type": "geo_point"},
            "created_at": {"type": "date"},
            "completed_at": {"type": "date"},
            "beneficiaries_served": {"type": "integer"},
            "agent_reasoning": {"type": "text"},
            # Para análisis temporal
            "@timestamp": {"type": "date"}
        }
    },
    "settings": {"number_of_shards": 1, "number_of_replicas": 0}
}

# Diccionario para setup automático
ALL_INDICES = {
    "cosecha_urbana_donors": DONORS_MAPPING,
    "cosecha_urbana_recipients": RECIPIENTS_MAPPING,
    "cosecha_urbana_food_alerts": FOOD_ALERTS_MAPPING,
    "cosecha_urbana_donations_history": DONATIONS_HISTORY_MAPPING,
}
```

### 1.3 Cliente Elasticsearch (Singleton + Retry)

```python
# src/cosecha_urbana_ai/elasticsearch/client.py
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ConnectionError, TransportError
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from ..config import get_settings

logger = structlog.get_logger()
_es_client: AsyncElasticsearch | None = None


def get_es_client() -> AsyncElasticsearch:
    """Singleton factory para el cliente ES."""
    global _es_client
    if _es_client is None:
        settings = get_settings()
        
        if settings.elastic_cloud_id:
            _es_client = AsyncElasticsearch(
                cloud_id=settings.elastic_cloud_id,
                api_key=settings.elasticsearch_api_key,
            )
        else:
            _es_client = AsyncElasticsearch(
                hosts=[str(settings.elasticsearch_url)],
                api_key=settings.elasticsearch_api_key,
                retry_on_timeout=True,
                max_retries=3,
            )
        
        logger.info("Elasticsearch client initialized")
    
    return _es_client


async def close_es_client():
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None
        logger.info("Elasticsearch client closed")
```

### 1.4 Script de setup de índices

```python
# scripts/setup_indices.py
"""
USO: python scripts/setup_indices.py [--reset]
"""
import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cosecha_urbana_ai.elasticsearch.client import get_es_client
from cosecha_urbana_ai.elasticsearch.indices import ALL_INDICES
import structlog

logger = structlog.get_logger()


async def setup_indices(reset: bool = False):
    es = get_es_client()
    
    for index_name, mapping in ALL_INDICES.items():
        exists = await es.indices.exists(index=index_name)
        
        if exists and reset:
            logger.warning("Deleting index", index=index_name)
            await es.indices.delete(index=index_name)
            exists = False
        
        if not exists:
            await es.indices.create(index=index_name, body=mapping)
            logger.info("Created index", index=index_name)
        else:
            logger.info("Index already exists, skipping", index=index_name)
    
    await es.close()
    logger.info("Setup complete", total_indices=len(ALL_INDICES))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete and recreate indices")
    args = parser.parse_args()
    asyncio.run(setup_indices(reset=args.reset))
```

---

## FASE 2 — Backend API (FastAPI) {#fase-2}

### 2.1 Main application

```python
# src/cosecha_urbana_ai/api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from ..config import get_settings
from ..elasticsearch.client import get_es_client, close_es_client
from ..utils.logging import setup_logging
from .routers import alerts, donors, recipients, donations, agent, health
from .middleware import setup_middleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: startup y shutdown del servidor."""
    # Startup
    setup_logging()
    settings = get_settings()
    
    logger.info(
        "Starting cosecha_urbana_ai",
        version="0.1.0",
        environment="development" if settings.api_debug else "production"
    )
    
    # Verificar conexión a ES
    es = get_es_client()
    info = await es.info()
    logger.info("Elasticsearch connected", version=info["version"]["number"])
    
    yield
    
    # Shutdown
    await close_es_client()
    logger.info("cosecha_urbana_ai shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="cosecha_urbana_ai API",
        description="AI Agent for food waste redistribution",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(health.router, tags=["health"])
    app.include_router(donors.router, prefix="/api/v1/donors", tags=["donors"])
    app.include_router(recipients.router, prefix="/api/v1/recipients", tags=["recipients"])
    app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
    app.include_router(donations.router, prefix="/api/v1/donations", tags=["donations"])
    app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
    
    return app


app = create_app()
```

### 2.2 Router del Agente (endpoint principal)

```python
# src/cosecha_urbana_ai/api/routers/agent.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import structlog

from ...agent.graph import create_agent_graph
from ...models.agent_state import AgentState
from ...elasticsearch.client import get_es_client
from ...config import get_settings

logger = structlog.get_logger()
router = APIRouter()


class AgentTriggerRequest(BaseModel):
    alert_id: str
    force: bool = False  # Forzar ejecución aunque ya haya match


class AgentResponse(BaseModel):
    success: bool
    alert_id: str
    selected_recipient_id: str | None
    selected_recipient_name: str | None
    distance_km: float | None
    urgency_level: str
    match_score: float | None
    coordination_time_seconds: float
    steps_taken: list[str]
    reasoning: str
    errors: list[str]


@router.post("/trigger", response_model=AgentResponse)
async def trigger_agent(
    request: AgentTriggerRequest,
    background_tasks: BackgroundTasks,
):
    """
    Dispara el agente para procesar una alerta de excedente alimentario.
    
    El agente ejecutará 5 pasos:
    1. INGEST - Recupera y valida la alerta
    2. ANALYZE - Calcula urgencia y prioridad
    3. MATCH - Encuentra receptor óptimo
    4. EXECUTE - Crea ruta y envía notificaciones
    5. VALIDATE - Verifica y registra resultado
    """
    logger.info("Agent trigger received", alert_id=request.alert_id)
    
    try:
        graph = create_agent_graph()
        
        initial_state: AgentState = {
            "alert_id": request.alert_id,
            "alert": None,
            "urgency_score": 0.0,
            "priority_rank": 0,
            "analysis_reasoning": "",
            "candidate_recipients": [],
            "selected_recipient": None,
            "match_score": 0.0,
            "match_reasoning": "",
            "distance_km": 0.0,
            "route": None,
            "notifications_sent": [],
            "execution_status": "pending",
            "validation_passed": False,
            "validation_notes": "",
            "steps_taken": [],
            "errors": [],
            "started_at": "",
            "completed_at": None,
            "messages": [],
        }
        
        import time
        start = time.time()
        final_state = await graph.ainvoke(initial_state)
        elapsed = time.time() - start
        
        recipient = final_state.get("selected_recipient")
        
        return AgentResponse(
            success=final_state.get("validation_passed", False),
            alert_id=request.alert_id,
            selected_recipient_id=recipient.id if recipient else None,
            selected_recipient_name=recipient.name if recipient else None,
            distance_km=final_state.get("distance_km"),
            urgency_level=final_state["alert"].urgency_level if final_state.get("alert") else "unknown",
            match_score=final_state.get("match_score"),
            coordination_time_seconds=elapsed,
            steps_taken=final_state.get("steps_taken", []),
            reasoning=final_state.get("match_reasoning", ""),
            errors=final_state.get("errors", []),
        )
    
    except Exception as e:
        logger.error("Agent execution failed", error=str(e), alert_id=request.alert_id)
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")
```

### 2.3 Router de Alertas (Webhook de donantes)

```python
# src/cosecha_urbana_ai/api/routers/alerts.py
from fastapi import APIRouter, HTTPException, Query
from ...models.food_alert import FoodAlert
from ...elasticsearch.repositories.alert_repo import AlertRepository
from ...elasticsearch.client import get_es_client

router = APIRouter()


@router.post("/", response_model=FoodAlert, status_code=201)
async def create_alert(alert: FoodAlert):
    """Webhook endpoint: centros comerciales reportan excedentes."""
    repo = AlertRepository(get_es_client())
    
    # Calcular urgencia antes de guardar
    alert.urgency_level = alert.compute_urgency()
    
    created = await repo.create(alert)
    return created


@router.get("/active", response_model=list[FoodAlert])
async def get_active_alerts(
    max_distance_km: float = Query(default=15.0),
    lat: float = Query(...),
    lon: float = Query(...),
):
    """Obtener alertas activas cercanas a una ubicación."""
    repo = AlertRepository(get_es_client())
    return await repo.find_active_near(lat=lat, lon=lon, max_km=max_distance_km)


@router.get("/{alert_id}", response_model=FoodAlert)
async def get_alert(alert_id: str):
    repo = AlertRepository(get_es_client())
    alert = await repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
```

---

## FASE 3 — Agente IA (LangGraph + Agent Builder) {#fase-3}

### 3.1 Grafo del Agente (LangGraph StateGraph)

**INSTRUCCIÓN PARA CLAUDE CODE:** Este es el corazón del proyecto. El grafo debe tener nodos claros con transiciones condicionales. Usa `StateGraph` con `AgentState` como schema. El nodo `match_node` debe usar tanto ES Vector Search como Geo Search, combinando ambos scores con pesos ponderados.

```python
# src/cosecha_urbana_ai/agent/graph.py
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    ingest_node,
    analyze_node,
    match_node,
    execute_node,
    validate_node,
)
import structlog

logger = structlog.get_logger()


def should_continue_after_ingest(state: AgentState) -> str:
    """Router: ¿La alerta existe y es válida?"""
    if state.get("errors") and len(state["errors"]) > 0:
        return "failed"
    if not state.get("alert"):
        return "failed"
    return "analyze"


def should_continue_after_analyze(state: AgentState) -> str:
    """Router: ¿La urgencia requiere acción inmediata?"""
    if state.get("errors"):
        return "failed"
    urgency = state.get("urgency_score", 0)
    if urgency >= 0.9:  # Crítico: ir directo a match con prioridad máxima
        logger.warning("CRITICAL urgency alert", score=urgency)
    return "match"


def should_continue_after_match(state: AgentState) -> str:
    """Router: ¿Se encontró receptor compatible?"""
    if not state.get("selected_recipient"):
        return "no_recipient"
    if state.get("match_score", 0) < 0.3:
        return "low_match"
    return "execute"


def create_agent_graph() -> StateGraph:
    """Factory function que crea y compila el grafo del agente."""
    
    workflow = StateGraph(AgentState)
    
    # Agregar nodos
    workflow.add_node("ingest", ingest_node.run)
    workflow.add_node("analyze", analyze_node.run)
    workflow.add_node("match", match_node.run)
    workflow.add_node("execute", execute_node.run)
    workflow.add_node("validate", validate_node.run)
    
    # Entry point
    workflow.set_entry_point("ingest")
    
    # Transiciones condicionales
    workflow.add_conditional_edges(
        "ingest",
        should_continue_after_ingest,
        {
            "analyze": "analyze",
            "failed": END,
        }
    )
    
    workflow.add_conditional_edges(
        "analyze",
        should_continue_after_analyze,
        {
            "match": "match",
            "failed": END,
        }
    )
    
    workflow.add_conditional_edges(
        "match",
        should_continue_after_match,
        {
            "execute": "execute",
            "no_recipient": "validate",   # Validar como "no match found"
            "low_match": "validate",      # Validar como "insufficient match"
        }
    )
    
    workflow.add_edge("execute", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()
```

### 3.2 Nodo de Análisis (ES|QL)

```python
# src/cosecha_urbana_ai/agent/nodes/analyze_node.py
from ..state import AgentState
from ...elasticsearch.queries.esql_queries import (
    get_urgency_score_query,
    get_historical_pattern_query,
)
from ...elasticsearch.client import get_es_client
import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()


async def run(state: AgentState) -> AgentState:
    """
    Nodo 2: ANALYZE
    
    Usa ES|QL para:
    1. Calcular urgency_score basado en tiempo restante y categoría
    2. Consultar patrones históricos de la zona (¿qué receptor suele tomar qué?)
    3. Determinar prioridad relativa vs otras alertas activas
    """
    alert = state["alert"]
    steps = state.get("steps_taken", [])
    steps.append("analyze_node:started")
    
    logger.info("Analyzing alert", alert_id=alert.id, category=alert.food_category)
    
    es = get_es_client()
    
    # 1. Calcular urgency score normalizado (0-1)
    hours_left = alert.hours_until_expiry
    
    # Score basado en tiempo: 1.0 = expira ya, 0.0 = más de 24h
    time_urgency = max(0.0, min(1.0, 1.0 - (hours_left / 24.0)))
    
    # Factor por categoría (comida preparada es más urgente)
    category_weights = {
        "prepared": 1.0,
        "dairy": 0.85,
        "meat": 0.9,
        "bakery": 0.8,
        "produce": 0.7,
        "dry_goods": 0.3,
    }
    category_factor = category_weights.get(alert.food_category, 0.5)
    
    urgency_score = time_urgency * category_factor
    
    # 2. ES|QL Query: ¿cuántas otras alertas activas del mismo donante?
    esql_query = f"""
    FROM cosecha_urbana_food_alerts
    | WHERE is_active == true AND donor_id == "{alert.donor_id}"
    | STATS count = COUNT(*), avg_kg = AVG(quantity_kg)
    | LIMIT 1
    """
    
    try:
        result = await es.esql.query(body={"query": esql_query})
        rows = result.get("rows", [])
        concurrent_alerts = rows[0][0] if rows else 0
        
        # Si hay muchas alertas del mismo donante, boost de urgencia
        if concurrent_alerts > 3:
            urgency_score = min(1.0, urgency_score * 1.2)
    except Exception as e:
        logger.warning("ES|QL query failed, using base urgency", error=str(e))
    
    # 3. Rank de prioridad vs otras alertas activas
    rank_query = f"""
    FROM cosecha_urbana_food_alerts
    | WHERE is_active == true AND urgency_score > {urgency_score}
    | STATS count = COUNT(*)
    """
    
    priority_rank = 1
    try:
        rank_result = await es.esql.query(body={"query": rank_query})
        rows = rank_result.get("rows", [])
        priority_rank = (rows[0][0] if rows else 0) + 1
    except Exception as e:
        logger.warning("Priority rank query failed", error=str(e))
    
    reasoning = (
        f"Alerta analizada: {hours_left:.1f}h hasta vencimiento. "
        f"Categoría: {alert.food_category} (factor: {category_factor}). "
        f"Urgency score: {urgency_score:.2f}. "
        f"Prioridad: #{priority_rank} entre alertas activas."
    )
    
    steps.append("analyze_node:completed")
    
    return {
        **state,
        "urgency_score": urgency_score,
        "priority_rank": priority_rank,
        "analysis_reasoning": reasoning,
        "steps_taken": steps,
    }
```

### 3.3 Nodo de Matching (Vector + Geo + LLM)

```python
# src/cosecha_urbana_ai/agent/nodes/match_node.py
from ..state import AgentState
from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.recipient_repo import RecipientRepository
from ...config import get_settings
from langchain_anthropic import ChatAnthropic
import structlog
import json

logger = structlog.get_logger()


async def run(state: AgentState) -> AgentState:
    """
    Nodo 3: MATCH
    
    Estrategia de matching en 3 capas:
    1. GEO Filter: Radio máximo configurable (default 15km)
    2. COMPATIBILITY Filter: Categoría de comida aceptada, capacidad de almacenamiento
    3. SCORING: Combina distancia, necesidad actual, historial, y vector similarity
    4. LLM Reasoning: Claude valida y explica el match final
    """
    alert = state["alert"]
    settings = get_settings()
    steps = state.get("steps_taken", [])
    steps.append("match_node:started")
    
    es = get_es_client()
    repo = RecipientRepository(es)
    
    # ── CAPA 1: Búsqueda geo + compatibilidad ─────────────────────────────
    geo_compatible = await repo.find_compatible_recipients(
        lat=alert.location.lat,
        lon=alert.location.lon,
        max_km=settings.max_distance_km,
        food_category=alert.food_category,
        quantity_kg=alert.quantity_kg,
        requires_refrigeration="refrigeration" in alert.special_requirements,
    )
    
    if not geo_compatible:
        logger.warning("No compatible recipients found", alert_id=alert.id)
        return {
            **state,
            "candidate_recipients": [],
            "selected_recipient": None,
            "match_reasoning": "No se encontraron receptores compatibles en el radio definido.",
            "steps_taken": steps,
        }
    
    # ── CAPA 2: Scoring multi-criterio ───────────────────────────────────
    scored_candidates = []
    
    for recipient in geo_compatible:
        # Score de distancia (más cerca = mejor)
        dist_score = 1.0 - (recipient.distance_km / settings.max_distance_km)
        
        # Score de necesidad actual
        need_scores = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        need_score = need_scores.get(recipient.current_need_level, 0.5)
        
        # Score de historial (menos donaciones recibidas = más prioritario)
        history_score = max(0.0, 1.0 - (recipient.total_donations_received / 100))
        
        # Score de beneficiarios (más personas = más impacto)
        beneficiary_score = min(1.0, recipient.beneficiaries_count / 200)
        
        # Score compuesto con pesos
        composite_score = (
            dist_score * 0.30 +
            need_score * 0.35 +
            history_score * 0.15 +
            beneficiary_score * 0.20
        )
        
        scored_candidates.append((composite_score, recipient))
    
    # Ordenar por score descendente
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    top_candidates = scored_candidates[:3]  # Top 3 para LLM
    
    # ── CAPA 3: LLM Reasoning (Claude) ───────────────────────────────────
    llm = ChatAnthropic(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=1024,
    )
    
    candidates_summary = []
    for score, r in top_candidates:
        candidates_summary.append({
            "id": r.id,
            "name": r.name,
            "type": r.organization_type,
            "distance_km": round(r.distance_km, 2),
            "beneficiaries": r.beneficiaries_count,
            "need_level": r.current_need_level,
            "composite_score": round(score, 3),
        })
    
    prompt = f"""Eres el sistema de matching de cosecha_urbana_ai.

ALERTA DE EXCEDENTE:
- Alimento: {alert.food_category} - {alert.description}
- Cantidad: {alert.quantity_kg} kg
- Horas hasta vencimiento: {alert.hours_until_expiry:.1f}h
- Urgencia: {state['urgency_score']:.2f}/1.0
- Requerimientos especiales: {alert.special_requirements}

CANDIDATOS RECEPTORES (top 3):
{json.dumps(candidates_summary, ensure_ascii=False, indent=2)}

Selecciona el MEJOR receptor considerando:
1. Urgencia de la donación vs capacidad del receptor
2. Distancia para maximizar viabilidad logística  
3. Impacto (beneficiarios atendidos)
4. Necesidad actual del receptor

Responde en JSON con este formato exacto:
{{
  "selected_id": "id_del_receptor",
  "confidence": 0.0-1.0,
  "reasoning": "Explicación en español de 2-3 oraciones"
}}"""
    
    llm_response = await llm.ainvoke(prompt)
    
    try:
        llm_result = json.loads(llm_response.content)
        selected_id = llm_result["selected_id"]
        match_score = llm_result["confidence"]
        reasoning = llm_result["reasoning"]
    except (json.JSONDecodeError, KeyError) as e:
        # Fallback: usar top candidate por score
        logger.warning("LLM response parse failed, using top scored", error=str(e))
        selected_id = top_candidates[0][1].id
        match_score = top_candidates[0][0]
        reasoning = f"Match automático por score compuesto: {match_score:.2f}"
    
    # Recuperar el recipient seleccionado
    selected = next(
        (r for _, r in top_candidates if r.id == selected_id),
        top_candidates[0][1]  # fallback
    )
    
    steps.append("match_node:completed")
    
    return {
        **state,
        "candidate_recipients": [r for _, r in top_candidates],
        "selected_recipient": selected,
        "match_score": match_score,
        "match_reasoning": reasoning,
        "distance_km": selected.distance_km,
        "steps_taken": steps,
    }
```

### 3.4 Tools para el Agente (ES Search + ES|QL)

```python
# src/cosecha_urbana_ai/agent/tools/esql_tool.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...elasticsearch.client import get_es_client
import structlog

logger = structlog.get_logger()


class ESQLInput(BaseModel):
    query: str = Field(description="ES|QL query to execute against Elasticsearch")


class ESQLAnalyticsTool(BaseTool):
    """
    Tool que permite al agente ejecutar queries ES|QL para:
    - Analizar patrones de desperdicio por zona/hora
    - Calcular estadísticas de donaciones históricas
    - Detectar anomalías y tendencias
    """
    name: str = "esql_analytics"
    description: str = """
    Ejecuta queries ES|QL en Elasticsearch para análisis de datos.
    Úsalo para obtener estadísticas, patrones temporales, y métricas de impacto.
    
    Ejemplos de uso:
    - Contar donaciones por categoría en la última semana
    - Calcular kg promedio por receptor
    - Detectar donantes con más excedente recurrente
    """
    args_schema: type[BaseModel] = ESQLInput
    
    async def _arun(self, query: str) -> str:
        es = get_es_client()
        try:
            result = await es.esql.query(body={"query": query})
            columns = result.get("columns", [])
            rows = result.get("rows", [])
            
            if not rows:
                return "No results found for the query."
            
            # Formatear resultado como texto estructurado
            col_names = [c["name"] for c in columns]
            output = f"Columns: {', '.join(col_names)}\n"
            output += f"Rows ({len(rows)}):\n"
            for row in rows[:20]:  # Limitar a 20 filas
                output += f"  {dict(zip(col_names, row))}\n"
            
            return output
        
        except Exception as e:
            logger.error("ES|QL tool error", error=str(e), query=query[:100])
            return f"Query error: {str(e)}"
    
    def _run(self, query: str) -> str:
        raise NotImplementedError("Use async version")
```

```python
# src/cosecha_urbana_ai/agent/tools/geo_tool.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...elasticsearch.client import get_es_client
import structlog

logger = structlog.get_logger()


class GeoSearchInput(BaseModel):
    lat: float = Field(description="Latitude of the center point")
    lon: float = Field(description="Longitude of the center point")
    radius_km: float = Field(default=15.0, description="Search radius in kilometers")
    index: str = Field(description="Elasticsearch index to search")


class GeoProximityTool(BaseTool):
    """Tool para búsquedas geoespaciales en Elasticsearch."""
    
    name: str = "geo_proximity_search"
    description: str = """
    Busca documentos en Elasticsearch dentro de un radio geográfico.
    Úsalo para encontrar receptores o donantes cercanos a una ubicación.
    Devuelve resultados ordenados por distancia.
    """
    args_schema: type[BaseModel] = GeoSearchInput
    
    async def _arun(self, lat: float, lon: float, radius_km: float, index: str) -> str:
        es = get_es_client()
        
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"is_active": True}},
                        {
                            "geo_distance": {
                                "distance": f"{radius_km}km",
                                "location": {"lat": lat, "lon": lon}
                            }
                        }
                    ]
                }
            },
            "sort": [
                {
                    "_geo_distance": {
                        "location": {"lat": lat, "lon": lon},
                        "order": "asc",
                        "unit": "km"
                    }
                }
            ],
            "size": 10
        }
        
        try:
            result = await es.search(index=index, body=query)
            hits = result["hits"]["hits"]
            
            if not hits:
                return f"No results found within {radius_km}km"
            
            output = f"Found {len(hits)} results:\n"
            for hit in hits:
                src = hit["_source"]
                dist = hit.get("sort", [0])[0]
                output += f"- {src.get('name', 'Unknown')} ({dist:.2f}km away) - ID: {hit['_id']}\n"
            
            return output
        
        except Exception as e:
            return f"Geo search error: {str(e)}"
    
    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async version")
```

---

## FASE 4 — Workflows y Notificaciones {#fase-4}

### 4.1 Donation Workflow

```python
# src/cosecha_urbana_ai/workflows/donation_workflow.py
from dataclasses import dataclass
from datetime import datetime, timezone
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient
from ..models.donation import Donation
from ..elasticsearch.repositories.donation_repo import DonationRepository
from ..elasticsearch.client import get_es_client
from ..notifications.base import NotificationService
import structlog

logger = structlog.get_logger()


@dataclass
class WorkflowResult:
    success: bool
    donation_id: str | None
    notifications_sent: list[str]
    errors: list[str]


class DonationCoordinationWorkflow:
    """
    Elastic Workflow: Coordina la donación de inicio a fin.
    
    Pasos:
    1. Crear registro de donación
    2. Actualizar estado de la alerta (is_active = False)
    3. Actualizar contadores del donante y receptor
    4. Notificar al voluntario/transportista
    5. Notificar al receptor
    6. Registrar en historial de analytics
    """
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.es = get_es_client()
    
    async def execute(
        self,
        alert: FoodAlert,
        recipient: Recipient,
        match_score: float,
        distance_km: float,
        agent_reasoning: str,
    ) -> WorkflowResult:
        
        notifications_sent = []
        errors = []
        donation_id = None
        
        try:
            # Paso 1: Crear donación
            donation = Donation(
                alert_id=alert.id,
                donor_id=alert.donor_id,
                donor_name=alert.donor_name,
                recipient_id=recipient.id,
                recipient_name=recipient.name,
                food_category=alert.food_category,
                quantity_kg=alert.quantity_kg,
                distance_km=distance_km,
                urgency_level=alert.urgency_level,
                status="in_progress",
                pickup_location=alert.location,
                delivery_location=recipient.location,
                created_at=datetime.now(timezone.utc).isoformat(),
                agent_reasoning=agent_reasoning,
                match_score=match_score,
            )
            
            repo = DonationRepository(self.es)
            created_donation = await repo.create(donation)
            donation_id = created_donation.id
            
            # Paso 2: Desactivar alerta
            await self.es.update(
                index="cosecha_urbana_food_alerts",
                id=alert.id,
                body={
                    "doc": {
                        "is_active": False,
                        "matched_recipient_id": recipient.id
                    }
                }
            )
            
            # Paso 3: Notificar donante
            donor_notif = await self.notification_service.notify_donor(
                alert=alert,
                recipient=recipient,
                donation_id=donation_id,
            )
            if donor_notif:
                notifications_sent.append(f"donor:{alert.donor_id}")
            
            # Paso 4: Notificar receptor
            recipient_notif = await self.notification_service.notify_recipient(
                alert=alert,
                recipient=recipient,
                donation_id=donation_id,
            )
            if recipient_notif:
                notifications_sent.append(f"recipient:{recipient.id}")
            
            logger.info(
                "Donation workflow completed",
                donation_id=donation_id,
                donor=alert.donor_name,
                recipient=recipient.name,
                kg=alert.quantity_kg,
                distance_km=distance_km,
            )
            
            return WorkflowResult(
                success=True,
                donation_id=donation_id,
                notifications_sent=notifications_sent,
                errors=errors,
            )
        
        except Exception as e:
            logger.error("Donation workflow failed", error=str(e))
            errors.append(str(e))
            return WorkflowResult(
                success=False,
                donation_id=donation_id,
                notifications_sent=notifications_sent,
                errors=errors,
            )
```

### 4.2 Notificaciones (WhatsApp)

```python
# src/cosecha_urbana_ai/notifications/whatsapp.py
import httpx
from .base import NotificationService, NotificationResult
from ..models.food_alert import FoodAlert
from ..models.recipient import Recipient
from ..config import get_settings
import structlog

logger = structlog.get_logger()


class WhatsAppNotificationService(NotificationService):
    """
    Integración con WhatsApp Business API (Meta).
    Envía mensajes de texto estructurados con detalles de la donación.
    """
    
    BASE_URL = "https://graph.facebook.com/v19.0"
    
    def __init__(self):
        settings = get_settings()
        self.token = settings.whatsapp_api_token
        self.phone_id = settings.whatsapp_phone_id
    
    async def notify_donor(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        
        message = (
            f"✅ *cosecha_urbana_ai*\n\n"
            f"¡Gracias {alert.donor_name}! Tu donación fue coordinada:\n\n"
            f"📦 *Alimento:* {alert.food_category} - {alert.quantity_kg}kg\n"
            f"🏠 *Receptor:* {recipient.name}\n"
            f"📍 *Distancia:* {alert.location.lat:.4f}, {alert.location.lon:.4f}\n"
            f"🆔 Folio: {donation_id[:8].upper()}\n\n"
            f"Un voluntario pasará a recoger. ¡Gracias por tu contribución! 🙏"
        )
        
        return await self._send_message(
            phone=alert.contact_phone if hasattr(alert, 'contact_phone') else "",
            message=message,
        )
    
    async def notify_recipient(
        self, alert: FoodAlert, recipient: Recipient, donation_id: str
    ) -> NotificationResult:
        
        message = (
            f"🌱 *cosecha_urbana_ai - Nueva Donación*\n\n"
            f"Hola {recipient.contact_name}!\n\n"
            f"📦 *Alimento:* {alert.description}\n"
            f"⚖️ *Cantidad:* {alert.quantity_kg} kg\n"
            f"📍 *Origen:* {alert.donor_name}\n"
            f"⏰ *Vence en:* {alert.hours_until_expiry:.1f} horas\n"
            f"🆔 Folio: {donation_id[:8].upper()}\n\n"
            f"Por favor confirma disponibilidad respondiendo OK."
        )
        
        return await self._send_message(
            phone=recipient.contact_phone,
            message=message,
        )
    
    async def _send_message(self, phone: str, message: str) -> NotificationResult:
        if not self.token or not self.phone_id:
            logger.warning("WhatsApp not configured, skipping notification")
            return NotificationResult(success=False, channel="whatsapp", error="Not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{self.phone_id}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": phone.replace("+", "").replace(" ", ""),
                    "type": "text",
                    "text": {"body": message},
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                return NotificationResult(success=True, channel="whatsapp")
            else:
                error = response.text[:200]
                logger.error("WhatsApp API error", status=response.status_code, error=error)
                return NotificationResult(success=False, channel="whatsapp", error=error)
```

---

## FASE 5 — Dashboard Kibana + Frontend {#fase-5}

### 5.1 Script de Dashboard Kibana

**INSTRUCCIÓN PARA CLAUDE CODE:** Crear el archivo `kibana/dashboards/cosecha_urbana_dashboard.ndjson` con los siguientes visualizaciones:
- Mapa de calor de alertas activas (Kibana Maps)
- Serie temporal: kg donados por día (Line chart)
- Donut chart: distribución por categoría de alimento
- Metric cards: total kg rescatados, beneficiarios atendidos, tiempo promedio de coordinación
- Tabla: últimas 10 donaciones con estado

### 5.2 Docker Compose (incluye Kibana)

```yaml
# docker-compose.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.4
    container_name: cosecha_es
    environment:
      - node.name=cosecha_es
      - cluster.name=cosecha-cluster
      - discovery.type=single-node
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD:-cosecha2024}
      - xpack.security.enabled=true
      - xpack.security.http.ssl.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -u elastic:$$ELASTIC_PASSWORD -s http://localhost:9200/_cluster/health | grep -q 'green\\|yellow'"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - cosecha_net

  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.4
    container_name: cosecha_kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=kibana_system
      - ELASTICSEARCH_PASSWORD=${KIBANA_SYSTEM_PASSWORD:-cosecha2024}
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy
    networks:
      - cosecha_net

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: cosecha_api
    env_file: .env
    ports:
      - "8000:8000"
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      elasticsearch:
        condition: service_healthy
    volumes:
      - ./src:/app/src   # Hot reload en dev
    command: uvicorn cosecha_urbana_ai.api.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - cosecha_net

volumes:
  esdata:

networks:
  cosecha_net:
    driver: bridge
```

---

## FASE 6 — Testing {#fase-6}

### 6.1 Configuración de Tests (conftest.py)

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from src.cosecha_urbana_ai.api.main import app
from src.cosecha_urbana_ai.models.food_alert import FoodAlert, FoodCategory, GeoPoint


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_es_client():
    client = AsyncMock()
    client.search = AsyncMock(return_value={"hits": {"hits": [], "total": {"value": 0}}})
    client.index = AsyncMock(return_value={"_id": "test-id-123", "result": "created"})
    client.esql = AsyncMock()
    client.esql.query = AsyncMock(return_value={"columns": [], "rows": []})
    return client


@pytest.fixture
def sample_food_alert():
    return FoodAlert(
        donor_id="donor-001",
        donor_name="Plaza Fiesta San Agustín Food Court",
        food_category=FoodCategory.PREPARED,
        description="Arroz con pollo preparado, 50 porciones individuales",
        quantity_kg=15.0,
        expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=3),
        location=GeoPoint(lat=25.6531, lon=-100.3679),  # Monterrey
        address="Av. Gómez Morín 444, San Agustín, Monterrey",
        special_requirements=["refrigeration"],
    )


@pytest.fixture
def sample_recipient():
    from src.cosecha_urbana_ai.models.recipient import Recipient, StorageCapacity
    return Recipient(
        id="recipient-001",
        name="Casa del Migrante San Pedro",
        organization_type="migrant_house",
        contact_name="Hermana María García",
        contact_phone="+528112345678",
        contact_email="contacto@casamigrante.org",
        location=GeoPoint(lat=25.6511, lon=-100.3589),
        address="Calle Padre Mier 100, Centro, Monterrey",
        beneficiaries_count=120,
        accepted_food_categories=[FoodCategory.PREPARED, FoodCategory.DAIRY],
        storage_capacity=StorageCapacity(refrigerated_kg=50.0, dry_kg=200.0),
        current_need_level="high",
    )
```

### 6.2 Tests unitarios del agente

```python
# tests/unit/test_agent_nodes.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

from src.cosecha_urbana_ai.agent.nodes import analyze_node
from src.cosecha_urbana_ai.models.food_alert import FoodAlert, FoodCategory, UrgencyLevel, GeoPoint


class TestAnalyzeNode:
    
    @pytest.mark.asyncio
    async def test_critical_urgency_prepared_food(self, sample_food_alert):
        """Comida preparada con < 2h debe tener urgency_score cercano a 1.0"""
        alert = sample_food_alert.model_copy(update={
            "expiry_datetime": datetime.now(timezone.utc) + timedelta(hours=1),
            "food_category": FoodCategory.PREPARED,
        })
        
        initial_state = {
            "alert_id": "test-001",
            "alert": alert,
            "steps_taken": [],
            "errors": [],
            "messages": [],
        }
        
        with patch("src.cosecha_urbana_ai.agent.nodes.analyze_node.get_es_client") as mock_es:
            mock_client = AsyncMock()
            mock_client.esql.query = AsyncMock(return_value={"rows": [[1, 10.0]], "columns": []})
            mock_es.return_value = mock_client
            
            result = await analyze_node.run(initial_state)
        
        assert result["urgency_score"] >= 0.8, "1h until expiry should be high urgency"
        assert "analyze_node:completed" in result["steps_taken"]
        assert result["analysis_reasoning"] != ""
    
    @pytest.mark.asyncio
    async def test_low_urgency_dry_goods(self, sample_food_alert):
        """Granos secos con > 24h deben tener urgency_score bajo."""
        alert = sample_food_alert.model_copy(update={
            "expiry_datetime": datetime.now(timezone.utc) + timedelta(hours=48),
            "food_category": FoodCategory.DRY_GOODS,
        })
        
        initial_state = {
            "alert_id": "test-002",
            "alert": alert,
            "steps_taken": [],
            "errors": [],
            "messages": [],
        }
        
        with patch("src.cosecha_urbana_ai.agent.nodes.analyze_node.get_es_client") as mock_es:
            mock_client = AsyncMock()
            mock_client.esql.query = AsyncMock(return_value={"rows": [], "columns": []})
            mock_es.return_value = mock_client
            
            result = await analyze_node.run(initial_state)
        
        assert result["urgency_score"] < 0.3, "48h dry goods should be low urgency"
```

### 6.3 Tests de integración API

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient


class TestAlertsEndpoint:
    
    @pytest.mark.asyncio
    async def test_create_alert_valid(self, async_client: AsyncClient, sample_food_alert):
        response = await async_client.post(
            "/api/v1/alerts/",
            json=sample_food_alert.model_dump(mode="json")
        )
        # Nota: puede ser 201 con ES real o 500 sin conexión en CI
        assert response.status_code in [201, 500]
    
    @pytest.mark.asyncio
    async def test_create_alert_invalid_expiry(self, async_client: AsyncClient):
        """Alerta con fecha de vencimiento en el pasado debe fallar con 422."""
        response = await async_client.post(
            "/api/v1/alerts/",
            json={
                "donor_id": "test",
                "donor_name": "Test Donor",
                "food_category": "prepared",
                "description": "Test food item description",
                "quantity_kg": 10.0,
                "expiry_datetime": "2020-01-01T00:00:00Z",  # Pasado
                "location": {"lat": 25.65, "lon": -100.37},
                "address": "Test address",
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
```

### 6.4 Makefile para comandos de test

```makefile
# Makefile
.PHONY: setup test lint format typecheck run seed demo

setup:
	uv sync --dev
	cp .env.example .env
	@echo "⚡ Edit .env with your credentials"

test:
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

run:
	uv run uvicorn src.cosecha_urbana_ai.api.main:app --reload --port 8000

run-docker:
	docker compose up --build

seed:
	uv run python scripts/seed_database.py

setup-indices:
	uv run python scripts/setup_indices.py

setup-indices-reset:
	uv run python scripts/setup_indices.py --reset

demo:
	uv run python scripts/run_demo.py

all: lint typecheck test
```

---

## FASE 7 — Docker y Deployment {#fase-7}

### 7.1 Dockerfile optimizado

```dockerfile
# Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copiar dependencias
COPY pyproject.toml .
RUN uv sync --no-dev --frozen

# ── Production image ──────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copiar virtual env del builder
COPY --from=builder /app/.venv /app/.venv

# Copiar código fuente
COPY src/ ./src/
COPY scripts/ ./scripts/

# No root
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "cosecha_urbana_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 CI/CD GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      elasticsearch:
        image: docker.elastic.co/elasticsearch/elasticsearch:8.13.4
        env:
          discovery.type: single-node
          xpack.security.enabled: false
          ES_JAVA_OPTS: -Xms512m -Xmx512m
        ports:
          - 9200:9200
        options: >-
          --health-cmd "curl -s http://localhost:9200/_cluster/health"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 10
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Lint
        run: uv run ruff check src/ tests/
      
      - name: Type check
        run: uv run mypy src/ --ignore-missing-imports
      
      - name: Run tests
        env:
          ELASTICSEARCH_URL: http://localhost:9200
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          API_SECRET_KEY: test-secret-key
          ELASTICSEARCH_API_KEY: ""
        run: uv run pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

---

## FASE 8 — Submission del Hackathon {#fase-8}

### 8.1 Descripción oficial (~400 palabras)

```markdown
# cosecha_urbana_ai — Hackathon Submission

## Problema
Cada día, toneladas de comida son desperdiciadas en centros comerciales, restaurantes 
y supermercados de Monterrey y otras ciudades latinoamericanas. Simultáneamente, 
casas del migrante, asilos de ancianos y orfanatos luchan por garantizar alimentación 
digna a sus beneficiarios. La coordinación es manual, lenta (2-4 horas) y caótica.

## Solución: cosecha_urbana_ai
Un agente multi-paso construido sobre Elasticsearch Agent Builder que automatiza 
completamente el ciclo de redistribución alimentaria: desde la alerta de excedente 
hasta la confirmación de entrega.

## Features de Elasticsearch Utilizados

**1. ES|QL para análisis en tiempo real**  
El nodo `analyze_node` ejecuta queries ES|QL para calcular urgency scores 
compuestos, analizar patrones históricos de desperdicio por zona/hora, y 
determinar prioridad relativa entre alertas activas simultáneas.

**2. Vector Search (kNN) para matching semántico**  
Usamos embeddings de las descripciones de alimentos y necesidades de los 
receptores para matching semántico. Un refugio que "necesita alimentos 
listos para servir" hace match automático con "50 porciones de arroz preparado".

**3. Geo Search para optimización logística**  
Elasticsearch geo_distance queries filtran receptores dentro de radio 
configurable (15km default), ordenados por distancia, reduciendo el tiempo 
de transporte y el riesgo de que la comida expire en tránsito.

## Flujo del Agente (5 pasos con LangGraph)
- **INGEST**: Valida y enriquece la alerta vía webhook
- **ANALYZE**: ES|QL calcula urgencia y prioridad
- **MATCH**: Vector + Geo + Claude selecciona receptor óptimo
- **EXECUTE**: Elastic Workflows coordina logística y notifica vía WhatsApp
- **VALIDATE**: Registra donación y actualiza analytics

## Lo que más nos gustó
1. **ES|QL** es extremadamente poderoso para análisis en tiempo real sin salir 
   del stack. Poder calcular scores compuestos y detectar patrones en una sola 
   query redujo la complejidad del agente significativamente.
2. **La combinación de Vector Search + Geo Search** permite un matching que 
   ningún sistema manual podría replicar: considera semantica, distancia, 
   capacidad y necesidad actual simultáneamente.

## Desafíos
El mayor reto fue diseñar el StateGraph de LangGraph para que los nodos fueran 
idempotentes y manejaran fallos gracefully. La integración con Elastic Workflows 
requirió pensar cuidadosamente en los estados de transición.

## Impacto medible
- ⏱️ Coordinación: de 2-4 horas → menos de 15 minutos
- 🍱 Estimado: 50-100 kg/día rescatados por centro comercial participante
- 👥 Beneficiarios directos: 300+ personas en Monterrey en fase piloto
```

### 8.2 README.md del repositorio

```markdown
# 🌱 cosecha_urbana_ai

> AI Agent for food waste redistribution — Elasticsearch Agent Builder Hackathon 2026

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Elasticsearch 8.x](https://img.shields.io/badge/elasticsearch-8.x-yellow.svg)](https://elastic.co)

## Quick Start

# 1. Clone
git clone https://github.com/tu-usuario/cosecha_urbana_ai
cd cosecha_urbana_ai

# 2. Setup
cp .env.example .env
# Editar .env con tus credenciales

# 3. Levantar servicios
docker compose up -d

# 4. Crear índices y seed data
make setup-indices
make seed

# 5. Ejecutar
make run
# API: http://localhost:8000/docs
# Kibana: http://localhost:5601
```

---

## ⚡ COMANDOS DE REFERENCIA RÁPIDA {#comandos}

```bash
# ════ DESARROLLO ════════════════════════════════════════════
make run                          # Iniciar servidor FastAPI
make run-docker                   # Docker compose completo
make seed                         # Cargar datos de prueba de Monterrey
make demo                         # Ejecutar demo del agente

# ════ ELASTICSEARCH ═════════════════════════════════════════
make setup-indices                # Crear índices
make setup-indices-reset          # Borrar y recrear índices

# ════ CALIDAD DE CÓDIGO ══════════════════════════════════════
make test                         # Todos los tests + coverage
make test-unit                    # Solo unit tests
make test-integration             # Solo integration tests
make lint                         # Ruff linter
make format                       # Ruff formatter
make typecheck                    # MyPy type checking
make all                          # lint + typecheck + test

# ════ DOCKER ════════════════════════════════════════════════
docker compose up -d              # Start all services
docker compose logs -f api        # Ver logs del API
docker compose down -v            # Stop y limpiar volumes

# ════ ELASTICSEARCH DIRECTO ════════════════════════════════
# Ver índices
curl -u elastic:cosecha2024 http://localhost:9200/_cat/indices?v

# Buscar alertas activas
curl -u elastic:cosecha2024 http://localhost:9200/cosecha_urbana_food_alerts/_search \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"is_active": true}}}'

# ES|QL: Stats de donaciones
curl -u elastic:cosecha2024 http://localhost:9200/_query \
  -H "Content-Type: application/json" \
  -d '{"query": "FROM cosecha_urbana_donations_history | STATS total_kg = SUM(quantity_kg), total_donations = COUNT(*)"}'
```

---

## 🏆 REGLAS DE CALIDAD SR {#reglas-sr}

### Para cada archivo que generes con Claude Code, asegúrate de:

**Python:**
- [ ] Todos los modelos usan Pydantic v2 (`model_config = ConfigDict(...)`)
- [ ] Todas las funciones async son `async def` y usan `await` correctamente
- [ ] Type hints en todas las funciones (params y return type)
- [ ] Docstrings en todas las clases y funciones públicas
- [ ] No hay `print()` — usar `structlog.get_logger().info()`
- [ ] Manejo explícito de excepciones con mensajes descriptivos
- [ ] Sin variables hardcodeadas — todo via `get_settings()`

**Elasticsearch:**
- [ ] Todos los índices tienen mappings explícitos (no dynamic mapping en prod)
- [ ] Usar `async` client de ES (`AsyncElasticsearch`)
- [ ] Queries tienen `size` explícito (nunca confiar en default 10)
- [ ] Manejar `TransportError` y `ConnectionError` de ES
- [ ] ES|QL queries validadas antes de enviar al agente

**LangGraph/Agente:**
- [ ] Cada nodo retorna `{**state, ...cambios}` (inmutabilidad del estado)
- [ ] Cada nodo registra su inicio/fin en `steps_taken`
- [ ] Errores se agregan a `state["errors"]`, no se lanzan excepciones
- [ ] LLM calls tienen temperatura baja (0.1) para determinismo
- [ ] Prompts del sistema en archivos separados (`prompts/`)

**FastAPI:**
- [ ] Todos los endpoints tienen `response_model` definido
- [ ] Usar `HTTPException` con códigos de status correctos
- [ ] Validación de inputs via Pydantic (no validar manualmente)
- [ ] Lifespan manager para startup/shutdown de recursos
- [ ] CORS configurado explícitamente

**Testing:**
- [ ] Cada nodo del agente tiene al menos 2 unit tests
- [ ] Mocks para ES client en unit tests (no hits reales)
- [ ] Tests de integración usan fixtures compartidos de `conftest.py`
- [ ] Coverage mínimo: 70%

**Git:**
- [ ] Commits atómicos con mensajes descriptivos (`feat:`, `fix:`, `test:`)
- [ ] `.env` en `.gitignore` — nunca commitear credenciales
- [ ] `LICENSE` MIT en raíz del repositorio (requerido para hackathon)
- [ ] `README.md` con Quick Start claro

---

## 📊 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

```
SEMANA 1 (Días 1-3): Fundación
  □ Fase 0: Setup completo del proyecto
  □ Fase 1: Modelos Pydantic + ES Indices + seed data
  □ Verificar: make setup-indices && make seed funciona

SEMANA 1 (Días 4-5): API + Agent básico
  □ Fase 2: FastAPI con routers básicos
  □ Fase 3 (parcial): Grafo LangGraph funcional con nodos INGEST + ANALYZE
  □ Verificar: POST /api/v1/alerts/ funciona y el agente se dispara

SEMANA 2 (Días 6-7): Matching + Workflows
  □ Fase 3 (completa): Nodos MATCH + EXECUTE + VALIDATE
  □ Fase 4: Workflows de coordinación + notificaciones
  □ Verificar: Demo end-to-end completo funciona

SEMANA 2 (Días 8-9): Polish + Tests
  □ Fase 5: Dashboard Kibana
  □ Fase 6: Tests unitarios + integración
  □ Fase 7: Docker + CI/CD

DÍA FINAL: Submission
  □ Fase 8: README + descripción oficial
  □ Grabar video demo de 3 minutos
  □ Post en X/LinkedIn taggeando @elastic_devs
  □ Submit en Devpost
```

---

> 🌱 **cosecha_urbana_ai** — Transformando desperdicio en oportunidad, un agente a la vez.
> 
> Construido con ❤️ en Monterrey, México para el Elasticsearch Agent Builder Hackathon 2026
```
