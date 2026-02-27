.PHONY: setup install test test-unit test-integration lint format typecheck run run-docker seed setup-indices setup-indices-reset kibana-import kibana-connector demo all

setup:
	pip install uv
	uv sync --dev
	cp .env.example .env 2>/dev/null || true
	@echo "⚡ Edit .env with your credentials"

install:
	uv sync --dev

test:
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/ --ignore-missing-imports

run:
	uv run uvicorn src.cosecha_urbana_ai.api.main:app --reload --port 8000 --host 0.0.0.0

run-docker:
	docker compose up --build

seed:
	uv run python scripts/seed_database.py

setup-indices:
	uv run python scripts/setup_indices.py

setup-indices-reset:
	uv run python scripts/setup_indices.py --reset

kibana-import:
	uv run python scripts/import_kibana_dashboard.py

kibana-connector:
	uv run python scripts/setup_kibana_connector.py

demo:
	uv run python scripts/run_demo.py

all: lint typecheck test
