"""
Script: Crear índices en Elasticsearch Serverless.

USO:
    python scripts/setup_indices.py          # Crear índices
    python scripts/setup_indices.py --reset  # Borrar y recrear
"""
import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog
from dotenv import load_dotenv

load_dotenv()

from cosecha_urbana_ai.elasticsearch.client import get_es_client
from cosecha_urbana_ai.elasticsearch.indices import ALL_INDICES
from cosecha_urbana_ai.utils.logging import setup_logging

logger = structlog.get_logger()


async def setup_indices(reset: bool = False) -> None:
    setup_logging()
    es = get_es_client()

    logger.info("Setting up Elasticsearch indices", reset=reset)

    # Verificar conexión
    try:
        info = await es.info()
        logger.info(
            "Connected to Elasticsearch",
            cluster=info.get("cluster_name", "serverless"),
        )
    except Exception as exc:
        logger.error("Cannot connect to Elasticsearch", error=str(exc))
        sys.exit(1)

    created = 0
    skipped = 0
    deleted = 0

    for index_name, mapping in ALL_INDICES.items():
        try:
            exists = await es.indices.exists(index=index_name)

            if exists and reset:
                logger.warning("Deleting index", index=index_name)
                await es.indices.delete(index=index_name)
                exists = False
                deleted += 1

            if not exists:
                # Serverless: solo mappings (sin settings de shards/replicas)
                body = {"mappings": mapping["mappings"]}
                await es.indices.create(index=index_name, body=body)
                logger.info("Created index", index=index_name)
                created += 1
            else:
                logger.info("Index exists, skipping", index=index_name)
                skipped += 1

        except Exception as exc:
            logger.error("Failed to create index", index=index_name, error=str(exc))

    await es.close()

    logger.info(
        "Setup complete",
        created=created,
        skipped=skipped,
        deleted=deleted,
        total=len(ALL_INDICES),
    )
    print(f"\ncosecha_urbana_ai indices ready!")
    print(f"   Created: {created} | Skipped: {skipped} | Deleted: {deleted}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Elasticsearch indices")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate all indices")
    args = parser.parse_args()
    asyncio.run(setup_indices(reset=args.reset))
