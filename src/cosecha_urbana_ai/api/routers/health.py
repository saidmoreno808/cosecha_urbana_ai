"""Health check endpoint."""
import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from ...elasticsearch.client import get_es_client

logger = structlog.get_logger()
router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    elasticsearch: str
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica el estado del servicio y conexión a Elasticsearch."""
    es_status = "disconnected"
    try:
        es = get_es_client()
        info = await es.info()
        es_status = f"connected ({info.get('cluster_name', 'serverless')})"
    except Exception as exc:
        logger.warning("ES health check failed", error=str(exc))
        es_status = f"error: {str(exc)[:100]}"

    return HealthResponse(
        status="ok",
        version="0.1.0",
        elasticsearch=es_status,
        message="cosecha_urbana_ai is running - food redistribution agent",
    )


@router.get("/")
async def root():
    return {
        "project": "cosecha_urbana_ai",
        "version": "0.1.0",
        "description": "AI Agent for food waste redistribution",
        "docs": "/docs",
        "hackathon": "Elasticsearch Agent Builder Hackathon 2026",
    }
