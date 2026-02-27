"""FastAPI application entry point."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from ..elasticsearch.client import close_es_client, get_es_client
from ..utils.logging import setup_logging
from .routers import agent, alerts, donations, donors, health, recipients

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: startup y shutdown del servidor."""
    setup_logging()
    settings = get_settings()

    logger.info(
        "Starting cosecha_urbana_ai",
        version="0.1.0",
        debug=settings.api_debug,
        es_url=settings.elasticsearch_url,
    )

    # Verificar conexión a ES
    try:
        es = get_es_client()
        info = await es.info()
        logger.info(
            "Elasticsearch connected",
            cluster=info.get("cluster_name", "serverless"),
        )
    except Exception as exc:
        logger.warning("Elasticsearch connection check failed", error=str(exc))

    yield

    await close_es_client()
    logger.info("cosecha_urbana_ai shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="cosecha_urbana_ai API",
        description="AI Agent for food waste redistribution - Elasticsearch Hackathon 2026",
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
