"""
Script: Demo completo del agente cosecha_urbana_ai.

Simula el flujo completo: crear alerta -> disparar agente -> ver resultado.

USO:
    python scripts/run_demo.py
"""
import asyncio
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from cosecha_urbana_ai.elasticsearch.client import get_es_client
from cosecha_urbana_ai.elasticsearch.repositories.alert_repo import AlertRepository
from cosecha_urbana_ai.models.food_alert import FoodAlert, FoodCategory, GeoPoint
from cosecha_urbana_ai.agent.graph import create_agent_graph
from cosecha_urbana_ai.models.agent_state import AgentState
from cosecha_urbana_ai.utils.logging import setup_logging
import structlog

setup_logging()
logger = structlog.get_logger()


async def run_demo() -> None:
    print("\n" + "="*60)
    print("cosecha_urbana_ai -- FULL DEMO")
    print("   Elasticsearch Agent Builder Hackathon 2026")
    print("="*60)

    es = get_es_client()
    alert_repo = AlertRepository(es)

    # 1. Create test alert
    print("\n[STEP 1] Creating food surplus alert...")
    alert = FoodAlert(
        donor_id="demo-donor-001",
        donor_name="Plaza Fiesta San Agustin -- Food Court",
        food_category=FoodCategory.PREPARED,
        description="Comida preparada: arroz con pollo, 50 porciones listas para servir. Urgente.",
        quantity_kg=15.0,
        expiry_datetime=datetime.now(timezone.utc) + timedelta(hours=2, minutes=30),
        location=GeoPoint(lat=25.6531, lon=-100.3679),
        address="Av. Gomez Morin 444, San Agustin, San Pedro",
        special_requirements=["refrigeration"],
        contact_phone="+528112000001",
    )
    alert.urgency_level = alert.compute_urgency()

    try:
        created = await alert_repo.create(alert)
        print(f"  [OK] Alert created: ID={created.id}")
        print(f"       Donor:    {created.donor_name}")
        print(f"       Food:     {created.food_category.value} -- {created.quantity_kg}kg")
        print(f"       Urgency:  {created.urgency_level.value.upper()}")
        print(f"       Expires:  {created.hours_until_expiry:.1f} hours")
        alert_id = created.id
    except Exception as exc:
        print(f"  [ERROR] Failed to create alert: {exc}")
        print("  [TIP] Run 'make setup-indices' and 'make seed' first")
        await es.close()
        return

    # 2. Trigger the agent
    print(f"\n[STEP 2] Triggering LangGraph agent...")
    print(f"         Alert ID: {alert_id}")

    initial_state: AgentState = {
        "alert_id": alert_id,
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
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "messages": [],
    }

    start = time.time()
    graph = create_agent_graph()
    final_state = await graph.ainvoke(initial_state)
    elapsed = time.time() - start

    # 3. Show results
    print(f"\n[RESULT] Agent completed in {elapsed:.1f}s")
    print("-" * 40)

    steps = final_state.get("steps_taken", [])
    print(f"\n  Steps executed ({len(steps)}):")
    for step in steps:
        mark = "[OK]" if "completed" in step else ("[FAIL]" if "failed" in step else "[->]")
        print(f"     {mark} {step}")

    print(f"\n  Analysis:")
    print(f"     Urgency Score: {final_state.get('urgency_score', 0):.3f}/1.0")
    print(f"     Priority Rank: #{final_state.get('priority_rank', '?')}")
    reasoning_preview = (final_state.get('analysis_reasoning', 'N/A') or 'N/A')[:100]
    print(f"     Reasoning:     {reasoning_preview}...")

    recipient = final_state.get("selected_recipient")
    if recipient:
        print(f"\n  Selected Recipient:")
        print(f"     Name:          {recipient.name}")
        print(f"     Type:          {recipient.organization_type}")
        print(f"     Distance:      {final_state.get('distance_km', 0):.2f} km")
        print(f"     Beneficiaries: {recipient.beneficiaries_count} people")
        print(f"     Need level:    {recipient.current_need_level}")
        print(f"     Match Score:   {final_state.get('match_score', 0):.3f}/1.0")
        print(f"\n  LLM Reasoning:")
        print(f"     {final_state.get('match_reasoning', 'N/A')}")
    else:
        print(f"\n  [WARN] No recipient was matched.")

    if final_state.get("notifications_sent"):
        print(f"\n  Notifications sent ({len(final_state['notifications_sent'])}):")
        for n in final_state["notifications_sent"]:
            print(f"     -> {n}")

    validation_passed = final_state.get("validation_passed", False)
    status_label = "PASSED" if validation_passed else "FAILED"
    print(f"\n  Validation: {status_label}")
    print(f"     {final_state.get('validation_notes', '')}")

    if final_state.get("errors"):
        print(f"\n  Errors:")
        for e in final_state["errors"]:
            print(f"     - {e}")

    print(f"\n  Coordination time: {elapsed:.2f} seconds")
    print(f"     (vs 2-4 hours manually)")

    print(f"\n{'='*60}")
    print(f"Demo complete.")
    print(f"   API docs:  http://localhost:8000/docs")
    print(f"   Trigger:   POST /api/v1/agent/trigger  alert_id={alert_id}")
    print(f"{'='*60}\n")

    await es.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
