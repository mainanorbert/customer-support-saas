# Repository task runner for consistent local workflows.
# Usage: make <target>

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Colored output for help (uses tput if available).
COLOR_BOLD := $(shell tput bold 2>/dev/null || true)
COLOR_RESET := $(shell tput sgr0 2>/dev/null || true)

.PHONY: help
help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_\-]+:.*##/ {printf "  %s%-20s%s %s\n", "$(COLOR_BOLD)", $$1, "$(COLOR_RESET)", $$2}' $(MAKEFILE_LIST)

# --- Backend ---
.PHONY: backend-dev
backend-dev: ## Start the FastAPI dev server
	cd backend; ./scripts/dev.sh

.PHONY: backend-migrate
backend-migrate: ## Run DB migrations
	cd backend; ./scripts/migrate.sh

.PHONY: backend-test
backend-test: ## Run backend tests
	cd backend; ./scripts/test.sh

.PHONY: backend-uv-sync
backend-uv-sync: ## Install backend dependencies with uv
	cd backend; uv sync --extra dev

# --- Frontend ---
.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	cd frontend; npm install

.PHONY: frontend-dev
frontend-dev: ## Start the Next.js dev server
	cd frontend; npm run dev

.PHONY: frontend-lint
frontend-lint: ## Run frontend lint
	cd frontend; npm run lint

# --- Docker ---
.PHONY: docker-up
docker-up: ## Build and run backend via Docker Compose
	docker compose up --build

.PHONY: docker-down
docker-down: ## Stop Docker Compose services
	docker compose down

# --- Convenience ---
.PHONY: dev
dev: ## Start backend and frontend dev servers (two terminals)
	@echo "Run 'make backend-dev' and 'make frontend-dev' in separate terminals."

.PHONY: test
test: backend-test ## Run test suite(s)
