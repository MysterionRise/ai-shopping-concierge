.PHONY: infra-up infra-down backend-dev frontend-dev test lint seed seed-catalog migrate-memory

infra-up:
	docker compose up -d postgres redis chromadb
	@echo "Waiting for services to be healthy..."
	@docker compose ps

infra-down:
	docker compose down

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

frontend-dev:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-unit:
	cd backend && python -m pytest tests/unit -v --cov=app --cov-report=term-missing

lint:
	cd backend && black --check app tests && isort --check-only app tests && flake8 app tests

format:
	cd backend && black app tests && isort app tests

seed: seed-catalog

seed-catalog:
	cd backend && python -m scripts.seed_catalog

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-memory:
	cd backend && python -m scripts.migrate_redis_to_langmem
