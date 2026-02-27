"""Router de receptores."""
import structlog
from fastapi import APIRouter, HTTPException, Query

from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.recipient_repo import RecipientRepository
from ...models.food_alert import FoodCategory
from ...models.recipient import Recipient

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=Recipient, status_code=201)
async def create_recipient(recipient: Recipient):
    """Registra un nuevo receptor."""
    repo = RecipientRepository(get_es_client())
    return await repo.create(recipient)


@router.get("/", response_model=list[Recipient])
async def list_recipients(
    size: int = Query(default=50, le=200),
):
    """Lista todos los receptores activos."""
    repo = RecipientRepository(get_es_client())
    return await repo.get_all_active(size=size)


@router.get("/near", response_model=list[Recipient])
async def find_recipients_near(
    lat: float = Query(...),
    lon: float = Query(...),
    max_km: float = Query(default=15.0),
    food_category: FoodCategory = Query(default=FoodCategory.PREPARED),
):
    """Busca receptores compatibles cercanos a una ubicación."""
    repo = RecipientRepository(get_es_client())
    return await repo.find_compatible_recipients(
        lat=lat,
        lon=lon,
        max_km=max_km,
        food_category=food_category,
        quantity_kg=0,
    )


@router.get("/{recipient_id}", response_model=Recipient)
async def get_recipient(recipient_id: str):
    """Obtiene un receptor por ID."""
    repo = RecipientRepository(get_es_client())
    recipient = await repo.get_by_id(recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    return recipient
