.PHONY: help test demo triage eval api ui db db-reset migrate revision fmt

help:
	@echo "Local"
	@echo "  make test        Run the full test suite from the repo root"
	@echo "  make demo        Two poll cycles against the mock provider"
	@echo "  make triage      Classify failures that have no verdict yet"
	@echo "  make eval        Score Gemini against the golden set"
	@echo "  make eval-rules  Score the rule-based baseline"
	@echo "  make api         Serve the read-only API on :8000"
	@echo "  make ui          Serve the dashboard on :5173"
	@echo ""
	@echo "Database"
	@echo "  make db          Start Postgres"
	@echo "  make db-reset    Destroy and rebuild it from migrations"
	@echo "  make migrate     Apply migrations"
	@echo "  make revision m=\"...\"   Generate one (verify it before applying)"
	@echo ""
	@echo "Cloud commands live in docs/RUNBOOK.md."

# Every target runs from the directory holding this file, which is why
# pytest and alembic find their config no matter where you invoke it.

test:
	uv run pytest -q

demo:
	uv run court-alerts demo

triage:
	uv run court-alerts triage

eval:
	uv run court-alerts eval

eval-rules:
	uv run court-alerts eval --agent heuristic

api:
	uv run uvicorn court_alerts.api.app:app --reload --port 8000

ui:
	cd web && npm run dev

db:
	docker compose up -d

db-reset:
	docker compose down -v
	docker compose up -d
	sleep 8
	uv run alembic upgrade head

migrate:
	uv run alembic upgrade head
	uv run alembic current

revision:
	@test -n "$(m)" || (echo "usage: make revision m=\"describe the change\""; exit 1)
	uv run alembic revision --autogenerate -m "$(m)"
	@echo ""
	@echo "Now open the generated file and confirm it is not empty."

fmt:
	uv run ruff check --fix .
	uv run ruff format .