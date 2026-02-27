"""Router de alertas de excedente alimentario (webhook de donantes)."""
import structlog
from fastapi import APIRouter, HTTPException, Query

from ...elasticsearch.client import get_es_client
from ...elasticsearch.repositories.alert_repo import AlertRepository
from ...models.food_alert import FoodAlert

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=FoodAlert, status_code=201)
async def create_alert(alert: FoodAlert):
    """
    Webhook endpoint: centros comerciales y restaurantes reportan excedentes.

    El agente es disparado automáticamente al crear una alerta.
    """
    # Calcular urgencia antes de guardar
    alert.urgency_level = alert.compute_urgency()

    repo = AlertRepository(get_es_client())
    created = await repo.create(alert)

    logger.info(
        "Alert created via API",
        alert_id=created.id,
        donor=created.donor_name,
        urgency=created.urgency_level,
        hours_left=f"{created.hours_until_expiry:.1f}",
    )
    return created


@router.get("/", response_model=list[FoodAlert])
async def list_alerts(
    active_only: bool = Query(default=True, description="Filtrar solo alertas activas"),
    size: int = Query(default=20, le=100),
):
    """Lista alertas ordenadas por urgencia descendente."""
    repo = AlertRepository(get_es_client())
    if active_only:
        return await repo.find_active(size=size)

    # Todas las alertas
    docs = await repo.search(
        {"query": {"match_all": {}}, "sort": [{"alert_created_at": {"order": "desc"}}]},
        size=size,
    )
    return [FoodAlert(**d) for d in docs]


@router.get("/active/near", response_model=list[FoodAlert])
async def get_active_alerts_near(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    max_km: float = Query(default=15.0, description="Radio en km"),
):
    """Alertas activas cercanas a una ubicación geográfica."""
    repo = AlertRepository(get_es_client())
    return await repo.find_active_near(lat=lat, lon=lon, max_km=max_km)


@router.get("/{alert_id}", response_model=FoodAlert)
async def get_alert(alert_id: str):
    """Obtiene una alerta específica por ID."""
    repo = AlertRepository(get_es_client())
    alert = await repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


@router.delete("/{alert_id}", status_code=204)
async def deactivate_alert(alert_id: str):
    """Desactiva una alerta (sin eliminarla del historial)."""
    repo = AlertRepository(get_es_client())
    alert = await repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await repo.update(alert_id, {"is_active": False})
