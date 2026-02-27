# Dockerfile — cosecha_urbana_ai
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --frozen

# ── Production image ──────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
COPY scripts/ ./scripts/

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "cosecha_urbana_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
