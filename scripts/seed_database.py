"""
Script: Cargar datos de prueba (Monterrey, Nuevo Leon).
Crea donantes y receptores reales de Monterrey para el demo del hackathon.

USO:
    python scripts/seed_database.py
"""
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import structlog

from cosecha_urbana_ai.elasticsearch.client import get_es_client
from cosecha_urbana_ai.elasticsearch.repositories.donor_repo import DonorRepository
from cosecha_urbana_ai.elasticsearch.repositories.recipient_repo import RecipientRepository
from cosecha_urbana_ai.elasticsearch.repositories.alert_repo import AlertRepository
from cosecha_urbana_ai.models.donor import Donor, OperatingHours
from cosecha_urbana_ai.models.recipient import Recipient, StorageCapacity
from cosecha_urbana_ai.models.food_alert import FoodAlert, FoodCategory, GeoPoint, UrgencyLevel
from cosecha_urbana_ai.utils.logging import setup_logging

logger = structlog.get_logger()


DONORS_DATA = [
    {
        "name": "Plaza Fiesta San Agustin - Food Court",
        "business_type": "food_court",
        "contact_name": "Gerencia de Sustentabilidad",
        "contact_phone": "+528112000001",
        "contact_email": "sustentabilidad@plazafiesta.com.mx",
        "location": {"lat": 25.6531, "lon": -100.3679},
        "address": "Av. Gomez Morin 444, San Agustin, San Pedro Garza Garcia",
        "typical_food_categories": ["prepared", "bakery"],
        "operating_hours": {"open": "10:00", "close": "22:00", "days": ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]},
        "has_refrigeration": True,
        "average_kg_per_donation": 25.0,
    },
    {
        "name": "Walmart Supercenter - Valle Oriente",
        "business_type": "supermarket",
        "contact_name": "Coordinador de Donaciones",
        "contact_phone": "+528113000001",
        "contact_email": "donaciones@walmart.com.mx",
        "location": {"lat": 25.6456, "lon": -100.3123},
        "address": "Av. Revolucion 2703, Valle Oriente, San Pedro Garza Garcia",
        "typical_food_categories": ["produce", "dairy", "bakery", "dry_goods"],
        "operating_hours": {"open": "07:00", "close": "23:00", "days": ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]},
        "has_refrigeration": True,
        "average_kg_per_donation": 40.0,
    },
    {
        "name": "Galerias Monterrey - Restaurantes",
        "business_type": "mall_restaurants",
        "contact_name": "Admin Galerias",
        "contact_phone": "+528114000001",
        "contact_email": "admin@galeriasmonterrey.com",
        "location": {"lat": 25.6667, "lon": -100.3456},
        "address": "Av. Lazaro Cardenas 1000, Residencial San Agustin",
        "typical_food_categories": ["prepared", "bakery"],
        "operating_hours": {"open": "11:00", "close": "21:00", "days": ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]},
        "has_refrigeration": False,
        "average_kg_per_donation": 18.0,
    },
    {
        "name": "Chedraui Premium - Cumbres",
        "business_type": "supermarket",
        "contact_name": "Responsable RSE",
        "contact_phone": "+528115000001",
        "contact_email": "rse@chedraui.com.mx",
        "location": {"lat": 25.7234, "lon": -100.3789},
        "address": "Av. Cumbres 5to Sector, Monterrey",
        "typical_food_categories": ["produce", "meat", "dairy", "dry_goods"],
        "operating_hours": {"open": "07:00", "close": "22:00", "days": ["monday","tuesday","wednesday","thursday","friday","saturday"]},
        "has_refrigeration": True,
        "average_kg_per_donation": 35.0,
    },
    {
        "name": "Liverpool - Cafeteria de empleados",
        "business_type": "department_store_cafeteria",
        "contact_name": "RRHH Liverpool",
        "contact_phone": "+528116000001",
        "contact_email": "rrhh@liverpool.com.mx",
        "location": {"lat": 25.6789, "lon": -100.3234},
        "address": "Av. Gonzalez Caballero 2000, Valle Oriente",
        "typical_food_categories": ["prepared"],
        "operating_hours": {"open": "09:00", "close": "18:00", "days": ["monday","tuesday","wednesday","thursday","friday"]},
        "has_refrigeration": False,
        "average_kg_per_donation": 12.0,
    },
]

RECIPIENTS_DATA = [
    {
        "name": "Casa del Migrante San Pedro",
        "organization_type": "migrant_house",
        "contact_name": "Hermana Maria Garcia",
        "contact_phone": "+528112100001",
        "contact_email": "contacto@casamigrante.org",
        "location": {"lat": 25.6511, "lon": -100.3589},
        "address": "Calle Padre Mier 100, Centro, Monterrey",
        "beneficiaries_count": 120,
        "accepted_food_categories": ["prepared", "dairy", "bakery", "produce"],
        "dietary_restrictions": [],
        "storage_capacity": {"refrigerated_kg": 50.0, "frozen_kg": 0.0, "dry_kg": 200.0},
        "current_need_level": "high",
        "needs_description": "Alimentos listos para servir, especialmente comida caliente para familias migrantes",
    },
    {
        "name": "Asilo Casa de los Abuelos A.C.",
        "organization_type": "elderly_shelter",
        "contact_name": "Directora Ana Robledo",
        "contact_phone": "+528112200002",
        "contact_email": "director@casaabuelos.org",
        "location": {"lat": 25.6789, "lon": -100.3456},
        "address": "Av. Constitucion 750, Centro, Monterrey",
        "beneficiaries_count": 85,
        "accepted_food_categories": ["prepared", "dairy", "produce", "dry_goods"],
        "dietary_restrictions": ["low_sodium", "diabetic_friendly"],
        "storage_capacity": {"refrigerated_kg": 30.0, "frozen_kg": 20.0, "dry_kg": 150.0},
        "current_need_level": "high",
        "needs_description": "Alimentos blandos y de facil digestion para adultos mayores, bajos en sodio",
    },
    {
        "name": "Orfanato Corazon de Ninos",
        "organization_type": "orphanage",
        "contact_name": "Director Carlos Mendoza",
        "contact_phone": "+528112300003",
        "contact_email": "director@corazondeninos.org",
        "location": {"lat": 25.6234, "lon": -100.2987},
        "address": "Av. Eugenio Garza Sada 150, Monterrey",
        "beneficiaries_count": 65,
        "accepted_food_categories": ["prepared", "dairy", "produce", "bakery"],
        "dietary_restrictions": ["nut_free"],
        "storage_capacity": {"refrigerated_kg": 40.0, "frozen_kg": 15.0, "dry_kg": 100.0},
        "current_need_level": "critical",
        "needs_description": "Nutricion variada para ninos y jovenes, sin nueces por alergias",
    },
    {
        "name": "Banco de Alimentos de Monterrey",
        "organization_type": "food_bank",
        "contact_name": "Coordinadora Logistica Sara Lopez",
        "contact_phone": "+528112400004",
        "contact_email": "logistica@bamx.org",
        "location": {"lat": 25.7123, "lon": -100.3678},
        "address": "Carretera Nacional km 12, Monterrey",
        "beneficiaries_count": 500,
        "accepted_food_categories": ["prepared", "dairy", "produce", "meat", "bakery", "dry_goods"],
        "dietary_restrictions": [],
        "storage_capacity": {"refrigerated_kg": 500.0, "frozen_kg": 300.0, "dry_kg": 2000.0},
        "current_need_level": "medium",
        "needs_description": "Acepta todo tipo de alimentos para redistribucion en colonias vulnerables de Monterrey",
    },
    {
        "name": "Comedor Comunitario San Bernabe",
        "organization_type": "community_kitchen",
        "contact_name": "Senora Esperanza Ruiz",
        "contact_phone": "+528112500005",
        "contact_email": "comedorsanbernabe@gmail.com",
        "location": {"lat": 25.7456, "lon": -100.3901},
        "address": "Calle Roble 45, Col. San Bernabe, Monterrey",
        "beneficiaries_count": 200,
        "accepted_food_categories": ["prepared", "produce", "dry_goods", "bakery"],
        "dietary_restrictions": [],
        "storage_capacity": {"refrigerated_kg": 20.0, "frozen_kg": 0.0, "dry_kg": 80.0},
        "current_need_level": "critical",
        "needs_description": "Comedor que sirve 200 comidas diarias a familias de escasos recursos en zona periferica",
    },
]


async def seed_database() -> None:
    setup_logging(log_format="console")
    es = get_es_client()

    donor_repo = DonorRepository(es)
    recipient_repo = RecipientRepository(es)
    alert_repo = AlertRepository(es)

    print("")
    print("cosecha_urbana_ai -- Seed Database")
    print("=" * 50)

    # Crear donantes
    print("\n[DONANTES] Creando donantes...")
    donor_ids = []
    for d in DONORS_DATA:
        try:
            donor = Donor(
                name=d["name"],
                business_type=d["business_type"],
                contact_name=d["contact_name"],
                contact_phone=d["contact_phone"],
                contact_email=d["contact_email"],
                location=GeoPoint(**d["location"]),
                address=d["address"],
                typical_food_categories=[FoodCategory(c) for c in d["typical_food_categories"]],
                operating_hours=OperatingHours(**d["operating_hours"]),
                has_refrigeration=d["has_refrigeration"],
                average_kg_per_donation=d["average_kg_per_donation"],
                is_verified=True,
            )
            created = await donor_repo.create(donor)
            donor_ids.append(created.id)
            print(f"  [OK] {created.name} (ID: {created.id[:8]}...)")
        except Exception as exc:
            print(f"  [ERR] Error creando donante: {exc}")

    # Crear receptores
    print("\n[RECEPTORES] Creando receptores...")
    recipient_ids = []
    for r in RECIPIENTS_DATA:
        try:
            recipient = Recipient(
                name=r["name"],
                organization_type=r["organization_type"],
                contact_name=r["contact_name"],
                contact_phone=r["contact_phone"],
                contact_email=r["contact_email"],
                location=GeoPoint(**r["location"]),
                address=r["address"],
                beneficiaries_count=r["beneficiaries_count"],
                accepted_food_categories=[FoodCategory(c) for c in r["accepted_food_categories"]],
                dietary_restrictions=r.get("dietary_restrictions", []),
                storage_capacity=StorageCapacity(**r["storage_capacity"]),
                current_need_level=r["current_need_level"],
                needs_description=r["needs_description"],
                is_verified=True,
            )
            created = await recipient_repo.create(recipient)
            recipient_ids.append(created.id)
            print(f"  [OK] {created.name} ({created.beneficiaries_count} beneficiarios)")
        except Exception as exc:
            print(f"  [ERR] Error creando receptor: {exc}")

    # Crear alertas de prueba
    print("\n[ALERTAS] Creando alertas de prueba...")
    now = datetime.now(timezone.utc)
    alerts_data = [
        {
            "donor_id": donor_ids[0] if donor_ids else "donor-001",
            "donor_name": "Plaza Fiesta San Agustin - Food Court",
            "food_category": FoodCategory.PREPARED,
            "description": "Arroz con pollo preparado, 50 porciones individuales listas para servir",
            "quantity_kg": 15.0,
            "expiry_datetime": now + timedelta(hours=3),
            "location": GeoPoint(lat=25.6531, lon=-100.3679),
            "address": "Av. Gomez Morin 444, San Agustin",
            "special_requirements": ["refrigeration"],
            "contact_phone": "+528112000001",
        },
        {
            "donor_id": donor_ids[1] if len(donor_ids) > 1 else "donor-002",
            "donor_name": "Walmart Supercenter - Valle Oriente",
            "food_category": FoodCategory.PRODUCE,
            "description": "Frutas y verduras frescas: manzanas, jitomate, lechuga, calabaza",
            "quantity_kg": 30.0,
            "expiry_datetime": now + timedelta(hours=8),
            "location": GeoPoint(lat=25.6456, lon=-100.3123),
            "address": "Av. Revolucion 2703, Valle Oriente",
            "special_requirements": [],
            "contact_phone": "+528113000001",
        },
        {
            "donor_id": donor_ids[2] if len(donor_ids) > 2 else "donor-003",
            "donor_name": "Galerias Monterrey - Restaurantes",
            "food_category": FoodCategory.BAKERY,
            "description": "Pan artesanal del dia: bolillos, conchas y cuernitos frescos",
            "quantity_kg": 8.0,
            "expiry_datetime": now + timedelta(hours=5),
            "location": GeoPoint(lat=25.6667, lon=-100.3456),
            "address": "Av. Lazaro Cardenas 1000",
            "special_requirements": [],
            "contact_phone": "+528114000001",
        },
    ]

    alert_ids = []
    for a in alerts_data:
        try:
            alert = FoodAlert(**a)
            alert.urgency_level = alert.compute_urgency()
            created = await alert_repo.create(alert)
            alert_ids.append(created.id)
            print(
                f"  [OK] {created.donor_name}: {created.food_category.value} "
                f"({created.quantity_kg}kg, urgency={created.urgency_level.value}, "
                f"ID: {created.id[:8]}...)"
            )
        except Exception as exc:
            print(f"  [ERR] Error creando alerta: {exc}")

    await es.close()

    print("")
    print("=" * 50)
    print("SEED COMPLETADO:")
    print(f"  Donantes:   {len(donor_ids)}")
    print(f"  Receptores: {len(recipient_ids)}")
    print(f"  Alertas:    {len(alert_ids)}")
    print("")
    print("ALERT IDs para probar el agente:")
    for aid in alert_ids:
        print(f"  {aid}")
    print("")
    print("Ejecuta: python -m uv run uvicorn src.cosecha_urbana_ai.api.main:app --reload --port 8000")
    print("Docs:    http://localhost:8000/docs")
    print("")


if __name__ == "__main__":
    asyncio.run(seed_database())
