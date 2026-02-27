"""Router de donaciones coordinadas."""
import structlog
from fastapi import APIRouter, HTTPException, Query

from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.donation_repo import DonationRepository
from ...models.donation import Donation

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=list[Donation])
async def list_donations(size: int = Query(default=20, le=100)):
    """Lista las donaciones más recientes."""
    repo = DonationRepository(get_es_client())
    return await repo.get_recent(size=size)


@router.get("/{donation_id}", response_model=Donation)
async def get_donation(donation_id: str):
    """Obtiene una donación por ID."""
    repo = DonationRepository(get_es_client())
    donation = await repo.get_by_id(donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


@router.get("/stats/summary")
async def get_donation_stats():
    """Estadísticas globales de donaciones usando ES|QL."""
    es = get_es_client()
    try:
        query = """
FROM cosecha_urbana_donations_history
| WHERE status == "completed"
| STATS
    total_kg = SUM(quantity_kg),
    total_donations = COUNT(*),
    total_beneficiaries = SUM(beneficiaries_served),
    avg_distance_km = AVG(distance_km)
"""
        result = await es.esql.query(body={"query": query})
        columns = [c["name"] for c in result.get("columns", [])]
        rows = result.get("rows", [])
        if rows:
            return dict(zip(columns, rows[0]))
        return {"message": "No completed donations yet"}
    except Exception as exc:
        logger.error("Stats query failed", error=str(exc))
        return {"error": str(exc)}
