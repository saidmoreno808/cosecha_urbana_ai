"""Router de donantes."""
import structlog
from fastapi import APIRouter, HTTPException, Query

from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.donor_repo import DonorRepository
from ...models.donor import Donor

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=Donor, status_code=201)
async def create_donor(donor: Donor):
    """Registra un nuevo donante en el sistema."""
    repo = DonorRepository(get_es_client())
    return await repo.create(donor)


@router.get("/", response_model=list[Donor])
async def list_donors(
    active_only: bool = Query(default=True),
    size: int = Query(default=50, le=200),
):
    """Lista todos los donantes activos."""
    repo = DonorRepository(get_es_client())
    return await repo.get_all_active(size=size)


@router.get("/{donor_id}", response_model=Donor)
async def get_donor(donor_id: str):
    """Obtiene un donante por ID."""
    repo = DonorRepository(get_es_client())
    donor = await repo.get_by_id(donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor
