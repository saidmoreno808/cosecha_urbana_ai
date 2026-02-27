"""
Script: Create a Slack connector in Kibana (Elastic-native notifications).

This creates a Kibana Actions connector of type ".slack" (Incoming Webhook)
so the agent can fire Slack notifications through the Elastic stack
without calling the Slack API directly.

USO:
    python scripts/setup_kibana_connector.py

REQUISITOS en .env:
    KIBANA_URL=https://your-project.kb.region.gcp.elastic.cloud
    ELASTICSEARCH_API_KEY=your_api_key
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

RESULTADO:
    Prints the connector ID to add as KIBANA_SLACK_CONNECTOR_ID in .env
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import httpx
from cosecha_urbana_ai.config import get_settings


async def main() -> None:
    settings = get_settings()

    print("")
    print("cosecha_urbana_ai -- Setup Kibana Slack Connector")
    print("=" * 55)

    if not settings.kibana_url:
        print("ERROR: KIBANA_URL not set in .env")
        sys.exit(1)

    if not settings.slack_webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL not set in .env")
        print("Get it from: api.slack.com/apps -> Incoming Webhooks -> Add Webhook")
        sys.exit(1)

    kibana_url = settings.kibana_url.rstrip("/")
    print(f"Kibana:        {kibana_url}")
    print(f"Webhook URL:   {settings.slack_webhook_url[:50]}...")

    headers = {
        "kbn-xsrf": "true",
        "Authorization": f"ApiKey {settings.elasticsearch_api_key}",
        "Content-Type": "application/json",
    }

    # Kibana .slack connector: webhookUrl must be in secrets (not config)
    payload = {
        "name": "cosecha_urbana_ai - Slack Notifications",
        "connector_type_id": ".slack",
        "config": {},
        "secrets": {
            "webhookUrl": settings.slack_webhook_url,
        },
    }

    async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
        # Check existing connectors first
        print("\nChecking existing connectors...")
        resp = await client.get(f"{kibana_url}/api/actions/connectors", headers=headers)
        if resp.status_code == 200:
            existing = resp.json()
            for c in existing:
                if "cosecha_urbana" in c.get("name", "").lower():
                    print(f"  Found existing: {c['name']} (id: {c['id']})")
                    print(f"\nConnector already exists! Add to .env:")
                    print(f"  KIBANA_SLACK_CONNECTOR_ID={c['id']}")
                    return

        # Create connector
        print("Creating Slack connector in Kibana...")
        response = await client.post(
            f"{kibana_url}/api/actions/connector",
            json=payload,
            headers=headers,
        )

    if response.status_code in (200, 201):
        data = response.json()
        connector_id = data["id"]
        connector_name = data["name"]
        connector_type = data["connector_type_id"]

        print("")
        print("=" * 55)
        print("CONNECTOR CREATED SUCCESSFULLY")
        print("=" * 55)
        print(f"Name:    {connector_name}")
        print(f"Type:    {connector_type}")
        print(f"ID:      {connector_id}")
        print("")
        print("Add to .env:")
        print(f"  KIBANA_SLACK_CONNECTOR_ID={connector_id}")
        print("")
        print("Then test it:")
        print("  uv run python scripts/test_notifications.py")

        # Auto-test the connector
        print("\nTesting connector with a sample message...")
        test_payload = {
            "params": {
                "message": (
                    "*cosecha_urbana_ai* - Kibana connector working!\n"
                    "Slack notifications are now Elastic-native. "
                    "The agent will post here when donations are coordinated."
                ),
            }
        }
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            test_resp = await client.post(
                f"{kibana_url}/api/actions/connector/{connector_id}/_execute",
                json=test_payload,
                headers=headers,
            )

        if test_resp.status_code in (200, 204):
            print("Test message sent to Slack! Check your channel.")
        else:
            print(f"Test failed: HTTP {test_resp.status_code} - {test_resp.text[:200]}")
            print("The connector was created but check your webhook URL.")

    else:
        print(f"ERROR: HTTP {response.status_code}")
        print(response.text[:500])
        print("")
        print("Common causes:")
        print("  - Invalid SLACK_WEBHOOK_URL (must start with https://hooks.slack.com/)")
        print("  - KIBANA_URL wrong (use .kb. not .es.)")
        print("  - API key lacks Kibana permissions")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
