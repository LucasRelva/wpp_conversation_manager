.PHONY: help setup start stop logs rebuild test clean docs dev

help:
	@echo "Handoff Dashboard - Make Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup & Deployment:"
	@echo "  make setup          - Initial setup with Docker"
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make rebuild        - Rebuild all Docker images"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start services for development"
	@echo "  make logs           - Show logs from all services"
	@echo "  make logs-api       - Show API logs"
	@echo "  make logs-frontend  - Show frontend logs"
	@echo "  make logs-redis     - Show Redis logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo "  make test-api       - Test API endpoints"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-all      - Remove everything including volumes"
	@echo ""
	@echo "Utils:"
	@echo "  make ps             - Show running containers"
	@echo "  make docs           - Open API documentation"
	@echo "  make shell-api      - Open shell in API container"

setup:
	@echo "Setting up Handoff Dashboard..."
	@bash setup.sh

start:
	@echo "Starting services..."
	docker-compose up -d
	@echo "✅ Services started"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"

stop:
	@echo "Stopping services..."
	docker-compose down
	@echo "✅ Services stopped"

restart: stop start

rebuild:
	@echo "Rebuilding Docker images..."
	docker-compose down
	docker-compose up -d --build
	@echo "✅ Services rebuilt"

dev: start
	@echo "🚀 Development environment ready"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API: http://localhost:8000"
	@echo "   View logs: make logs"

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-frontend:
	docker-compose logs -f frontend

logs-redis:
	docker-compose logs -f redis

test:
	@echo "Running tests..."
	@bash test.sh

test-api:
	@echo "Testing API endpoints..."
	@bash test.sh

ps:
	docker-compose ps

clean:
	@echo "Removing containers..."
	docker-compose down
	@echo "✅ Containers removed"

clean-all:
	@echo "Removing everything..."
	docker-compose down -v
	@echo "✅ Everything removed"

docs:
	@echo "Opening API documentation at http://localhost:8000/docs"
	@which open && open http://localhost:8000/docs || echo "Please visit http://localhost:8000/docs"

shell-api:
	docker exec -it handoff_api bash

shell-redis:
	docker exec -it handoff_redis redis-cli

# Watch frontend
watch-frontend:
	@cd frontend && npm run start

# Watch backend
watch-backend:
	@cd backend && python run.py
