.PHONY: dev-api dev-web test seed docker-up docker-down

dev-api:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && pnpm dev

test:
	cd backend && pytest -q

seed:
	cd backend && python -m app.cli seed

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

