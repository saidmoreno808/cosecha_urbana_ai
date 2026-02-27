# cosecha_urbana_ai

**AI Agent for food surplus redistribution from malls to shelters**

> Elasticsearch Agent Builder Hackathon 2026 — Built in Monterrey, Mexico

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-9.x-yellow.svg)](https://elastic.co)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--step-blue.svg)](https://langchain-ai.github.io/langgraph/)

---

## The Problem

Every day, **tons of food are wasted** in shopping malls, restaurants, and supermarkets across Latin America. At the same time, migrant shelters, elderly homes, orphanages, and food banks struggle to feed their beneficiaries. The coordination between donors and recipients is manual, slow (2–4 hours), and chaotic — resulting in food expiring before it reaches those who need it most.

## The Solution

`cosecha_urbana_ai` is a **5-step AI agent** built on Elasticsearch that fully automates the food redistribution cycle: from surplus alert to confirmed delivery. The agent processes incoming food surplus webhooks, analyzes urgency in real time using ES|QL, finds the optimal recipient through Vector Search + Geo Search, coordinates logistics, and records every donation for impact analytics.

---

## Agent Architecture

```
STEP 1: INGEST   → Receives surplus alert via webhook, validates & enriches data
STEP 2: ANALYZE  → ES|QL calculates urgency score + priority rank vs active alerts
STEP 3: MATCH    → Vector Search + Geo Search + LLM selects optimal recipient
STEP 4: EXECUTE  → Creates route, notifies donor & recipient, records donation
STEP 5: VALIDATE → Verifies outcome, updates analytics, marks alert resolved
```

```
┌─────────────────────────────────────────────────────────┐
│                  cosecha_urbana_ai                       │
│                                                         │
│   [Donor Webhook] ──► [LangGraph StateGraph]            │
│                          │                              │
│                    INGEST → ANALYZE → MATCH             │
│                                ↓         ↓              │
│                           EXECUTE → VALIDATE            │
│                                                         │
│   ┌──────────────────────────────────────────────────┐  │
│   │              ELASTICSEARCH LAYER                 │  │
│   │  donors · recipients · food_alerts · donations   │  │
│   │  ES|QL · Vector Search · Geo Search · Analytics  │  │
│   └──────────────────────────────────────────────────┘  │
│                                                         │
│   FastAPI REST API  ·  Kibana Dashboard  ·  Groq LLM    │
└─────────────────────────────────────────────────────────┘
```

---

## Elasticsearch Features Used

| Feature | Where Used | Purpose |
|---------|-----------|---------|
| **ES\|QL** | `analyze_node` | Real-time urgency scoring, priority ranking vs concurrent alerts |
| **Vector Search (kNN)** | `match_node` | Semantic matching between food descriptions and recipient needs |
| **Geo Search** | `match_node` | Filter recipients within configurable radius (default 15 km) |
| **Dense Vectors** | `donors`, `recipients` indices | 1536-dim embeddings for semantic food matching |
| **Geo Point fields** | All indices | Location-based queries and distance sorting |
| **Aggregations** | Kibana dashboard | Impact analytics: KG rescued, beneficiaries served, time metrics |
| **Index Mappings** | `indices.py` | Strict typed mappings for all 4 indices |

---

## Tech Stack

- **Elasticsearch Serverless** — Vector Search, ES|QL, Geo Search, Analytics
- **LangGraph** — Multi-step agent StateGraph orchestration
- **Groq** (llama-3.3-70b-versatile) — LLM reasoning for recipient matching
- **FastAPI** — Async REST API with Pydantic v2 models
- **Kibana** — Real-time impact dashboard (13 panels)
- **Python 3.11** + `uv` package manager

---

## Quick Start

### Prerequisites

- Python 3.11+
- Elasticsearch Serverless account ([Free trial at elastic.co](https://elastic.co))
- Groq API key ([Free at console.groq.com](https://console.groq.com))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/saidmoreno808/cosecha_urbana_ai
cd cosecha_urbana_ai

# 2. Install dependencies
pip install uv
uv sync --dev

# 3. Configure credentials
cp .env.example .env
# Edit .env — add your Elasticsearch and Groq API keys

# 4. Create Elasticsearch indices
make setup-indices

# 5. Load sample data (Monterrey, Mexico)
make seed

# 6. Start the API server
make run
# API docs: http://localhost:8000/docs
```

### Run the Agent

```bash
# Trigger the agent for a food surplus alert
curl -X POST http://localhost:8000/api/v1/agent/trigger \
  -H "Content-Type: application/json" \
  -d '{"alert_id": "YOUR_ALERT_ID"}'
```

### Import Kibana Dashboard

```bash
# Add KIBANA_URL to .env first, then:
make kibana-import
```

---

## Project Structure

```
cosecha_urbana_ai/
├── src/cosecha_urbana_ai/
│   ├── agent/
│   │   ├── graph.py              # LangGraph StateGraph (5 nodes)
│   │   ├── nodes/                # ingest, analyze, match, execute, validate
│   │   └── tools/                # ES Search, ES|QL, Geo, Notify tools
│   ├── elasticsearch/
│   │   ├── indices.py            # All index mappings + settings
│   │   ├── client.py             # Async ES singleton
│   │   └── repositories/         # Repository pattern per entity
│   ├── api/
│   │   ├── main.py               # FastAPI app with lifespan
│   │   └── routers/              # donors, recipients, alerts, agent
│   └── models/                   # Pydantic v2 models
├── kibana/dashboards/            # Kibana dashboard NDJSON
├── scripts/                      # setup_indices, seed, import_kibana
└── tests/                        # 15 unit tests
```

---

## Available Commands

```bash
make run                 # Start FastAPI server (hot reload)
make test                # Run all tests with coverage
make test-unit           # Unit tests only
make lint                # Ruff linter
make format              # Ruff formatter
make seed                # Load Monterrey sample data
make setup-indices       # Create Elasticsearch indices
make kibana-import       # Import Kibana dashboard
make demo                # Run full agent demo
```

---

## Environment Variables

```bash
# Required
ELASTICSEARCH_URL=https://your-cluster.es.region.gcp.elastic.cloud:443
ELASTICSEARCH_API_KEY=your_api_key_base64
GROQ_API_KEY=gsk_your_groq_key
API_SECRET_KEY=your_secret_key

# Optional
KIBANA_URL=https://your-cluster.kb.region.gcp.elastic.cloud
MAX_DISTANCE_KM=15           # Redistribution radius (default: 15km)
FOOD_URGENCY_THRESHOLD_HOURS=4
LLM_MODEL=groq               # groq (default) or anthropic
```

See `.env.example` for the full list.

---

## Measured Impact

| Metric | Before (manual) | With cosecha_urbana_ai |
|--------|----------------|------------------------|
| Coordination time | 2–4 hours | < 15 minutes |
| Match accuracy | Human judgment | Multi-criteria AI scoring |
| Coverage radius | Ad-hoc phone calls | 15 km geo-optimized |
| Analytics | None | Real-time Kibana dashboard |

Pilot estimate: **50–100 kg/day** rescued per participating mall · **300+ beneficiaries** in Monterrey

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/agent/trigger` | Trigger the 5-step redistribution agent |
| `POST` | `/api/v1/alerts/` | Create a food surplus alert (donor webhook) |
| `GET` | `/api/v1/alerts/active` | Get active alerts near a location |
| `GET` | `/api/v1/donors/` | List all verified donors |
| `GET` | `/api/v1/recipients/` | List all active recipients |
| `GET` | `/api/v1/donations/` | Donation history with analytics |
| `GET` | `/health` | Service health check |

Full interactive docs at `/docs` (Swagger UI).

---

## License

[MIT License](LICENSE) — open source as required by the hackathon.

---

## Built with

Elasticsearch · LangGraph · Groq · FastAPI · Kibana · Python 3.11

> Built with purpose in Monterrey, Mexico for the Elasticsearch Agent Builder Hackathon 2026.
