.PHONY: up down dev-backend dev-frontend install-backend install-frontend test-backend seed-demo migrate

# Docker Compose
up:
	docker-compose up -d

down:
	docker-compose down

rebuild:
	docker-compose up -d --build

logs:
	docker-compose logs -f

# Local development
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info

dev-frontend:
	cd frontend && npm run dev

# Installation
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

# Database
migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# Testing
test-backend:
	cd backend && pytest -v

# Demo
seed-demo:
	curl -s http://localhost:8000/api/demo/seed | python3 -m json.tool

# Setup .env
setup-env:
	cp .env.example backend/.env
	@echo "Edit backend/.env with your configuration"
