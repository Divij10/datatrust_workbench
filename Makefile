.PHONY: dev backend frontend test lint typecheck demo

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	docker compose up --build

test:
	cd backend && pytest

lint:
	cd backend && ruff format --check . && ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && mypy app
	cd frontend && npm run typecheck

demo:
	curl -F "file=@sample_data/messy_customers.csv" http://localhost:8000/api/v1/datasets

