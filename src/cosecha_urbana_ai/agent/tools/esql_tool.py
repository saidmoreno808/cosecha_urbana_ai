"""Tool ES|QL para análisis analítico desde el agente."""
import structlog
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ...elasticsearch.client import get_es_client

logger = structlog.get_logger()


class ESQLInput(BaseModel):
    query: str = Field(description="ES|QL query to execute")


class ESQLAnalyticsTool(BaseTool):
    """Ejecuta queries ES|QL para análisis de datos en tiempo real."""

    name: str = "esql_analytics"
    description: str = (
        "Ejecuta queries ES|QL en Elasticsearch para análisis. "
        "Úsalo para estadísticas, patrones temporales y métricas de impacto. "
        "Ejemplo: 'FROM cosecha_urbana_donations_history | STATS total_kg = SUM(quantity_kg)'"
    )
    args_schema: type[BaseModel] = ESQLInput

    async def _arun(self, query: str) -> str:
        es = get_es_client()
        try:
            result = await es.esql.query(body={"query": query})
            columns = result.get("columns", [])
            rows = result.get("rows", [])

            if not rows:
                return "No results found."

            col_names = [c["name"] for c in columns]
            output = f"Columns: {', '.join(col_names)}\nRows ({len(rows)}):\n"
            for row in rows[:20]:
                output += f"  {dict(zip(col_names, row))}\n"
            return output

        except Exception as exc:
            logger.error("ES|QL tool error", error=str(exc))
            return f"Query error: {exc}"

    def _run(self, query: str) -> str:
        raise NotImplementedError("Use async version")
