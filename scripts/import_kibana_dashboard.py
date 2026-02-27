"""
Script: Importar dashboard de Cosecha Urbana AI a Kibana.

Usa la API de Saved Objects de Kibana para importar el NDJSON completo
con todas las visualizaciones, index patterns y el dashboard principal.

USO:
    python scripts/import_kibana_dashboard.py

REQUISITOS:
    - KIBANA_URL en .env (o variable de entorno)
    - ELASTICSEARCH_API_KEY en .env (misma API key de ES Serverless)
    - El archivo kibana/dashboards/cosecha_urbana_dashboard.ndjson debe existir

KIBANA_URL ejemplos:
    - Local Docker:   http://localhost:5601
    - Elastic Cloud:  https://my-deployment.kb.us-central1.gcp.elastic-cloud.com
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
from dotenv import load_dotenv

load_dotenv()

import os

DASHBOARD_NDJSON = (
    Path(__file__).parent.parent / "kibana" / "dashboards" / "cosecha_urbana_dashboard.ndjson"
)


def get_kibana_config() -> dict:
    """Lee la configuracion de Kibana desde variables de entorno."""
    kibana_url = os.getenv("KIBANA_URL", "").rstrip("/")
    es_api_key = os.getenv("ELASTICSEARCH_API_KEY", "")

    if not kibana_url:
        print("")
        print("ERROR: KIBANA_URL no esta configurada.")
        print("")
        print("Agrega en tu .env:")
        print("  KIBANA_URL=https://tu-deployment.kb.us-central1.gcp.elastic-cloud.com")
        print("")
        print("Para Elastic Cloud Serverless, la URL de Kibana es diferente a la de ES.")
        print("Puedes encontrarla en: https://cloud.elastic.co -> tu proyecto -> Kibana endpoint")
        sys.exit(1)

    return {
        "kibana_url": kibana_url,
        "api_key": es_api_key,
    }


async def check_kibana_status(client: httpx.AsyncClient, kibana_url: str) -> bool:
    """Verifica que Kibana este disponible y autenticado."""
    try:
        response = await client.get(f"{kibana_url}/api/status")
        if response.status_code == 200:
            data = response.json()
            overall = data.get("status", {}).get("overall", {}).get("level", "unknown")
            version = data.get("version", {}).get("number", "unknown")
            print(f"Kibana conectado: v{version} | estado: {overall}")
            return True
        else:
            print(f"Kibana responde con status {response.status_code}: {response.text[:200]}")
            return False
    except httpx.ConnectError as e:
        print(f"No se puede conectar a Kibana: {e}")
        return False


async def import_saved_objects(
    client: httpx.AsyncClient,
    kibana_url: str,
    ndjson_path: Path,
    overwrite: bool = True,
) -> dict:
    """
    Importa el NDJSON usando la API de Saved Objects de Kibana.
    Endpoint: POST /api/saved_objects/_import
    """
    print(f"\nImportando: {ndjson_path.name}")
    print(f"Tamano: {ndjson_path.stat().st_size:,} bytes")

    ndjson_content = ndjson_path.read_bytes()

    params = {"overwrite": "true"} if overwrite else {}

    files = {
        "file": (ndjson_path.name, ndjson_content, "application/ndjson"),
    }

    response = await client.post(
        f"{kibana_url}/api/saved_objects/_import",
        params=params,
        files=files,
        timeout=60.0,
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error HTTP {response.status_code}:")
        print(response.text[:500])
        return {"success": False, "errors": [response.text]}


def print_import_results(result: dict) -> None:
    """Muestra los resultados del import de forma legible."""
    success = result.get("success", False)
    success_count = result.get("successCount", 0)
    errors = result.get("errors", [])
    success_results = result.get("successResults", [])

    print("")
    print("=" * 60)
    print("RESULTADO DE IMPORTACION")
    print("=" * 60)

    if success:
        print(f"Estado: EXITO - {success_count} objetos importados")
    else:
        print(f"Estado: PARCIAL/ERROR - {success_count} importados, {len(errors)} errores")

    if success_results:
        print("\nObjetos importados:")
        for obj in success_results:
            obj_type = obj.get("type", "unknown")
            obj_id = obj.get("id", "unknown")
            obj_title = obj.get("meta", {}).get("title", "")
            print(f"  [OK] {obj_type}: {obj_title or obj_id}")

    if errors:
        print("\nErrores:")
        for err in errors:
            err_type = err.get("type", "unknown")
            err_id = err.get("id", "unknown")
            err_msg = err.get("error", {}).get("message", str(err))
            print(f"  [ERR] {err_type}/{err_id}: {err_msg}")


def print_dashboard_url(kibana_url: str) -> None:
    """Muestra la URL directa al dashboard importado."""
    dashboard_id = "cosecha-urbana-main-dashboard"
    url = f"{kibana_url}/app/dashboards#/view/{dashboard_id}"
    print("")
    print("=" * 60)
    print("ACCESO AL DASHBOARD")
    print("=" * 60)
    print(f"URL: {url}")
    print("")
    print("Si el dashboard no carga, verifica:")
    print("  1. Que los indices tienen datos (ejecuta: make seed)")
    print("  2. Que el time range sea correcto (ajusta a 'Last 30 days')")
    print("  3. Que el index pattern coincida con los indices de ES")


async def main() -> None:
    config = get_kibana_config()
    kibana_url = config["kibana_url"]
    api_key = config["api_key"]

    print("")
    print("cosecha_urbana_ai -- Importar Dashboard Kibana")
    print("=" * 60)
    print(f"Kibana URL: {kibana_url}")
    print(f"NDJSON:     {DASHBOARD_NDJSON}")

    if not DASHBOARD_NDJSON.exists():
        print(f"\nERROR: No existe el archivo {DASHBOARD_NDJSON}")
        print("Asegurate de ejecutar desde la raiz del proyecto.")
        sys.exit(1)

    # Configurar headers de autenticacion
    headers = {
        "kbn-xsrf": "true",
        "Authorization": f"ApiKey {api_key}",
    }

    async with httpx.AsyncClient(headers=headers, verify=False) as client:
        # 1. Verificar conexion
        kibana_ok = await check_kibana_status(client, kibana_url)
        if not kibana_ok:
            print("\nNo se puede conectar a Kibana. Verifica KIBANA_URL y tu conexion.")
            sys.exit(1)

        # 2. Importar saved objects
        result = await import_saved_objects(
            client=client,
            kibana_url=kibana_url,
            ndjson_path=DASHBOARD_NDJSON,
            overwrite=True,
        )

        # 3. Mostrar resultados
        print_import_results(result)

        # 4. Mostrar URL del dashboard
        if result.get("success") or result.get("successCount", 0) > 0:
            print_dashboard_url(kibana_url)
        else:
            print("\nEl import fallo. Revisa los errores arriba.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
