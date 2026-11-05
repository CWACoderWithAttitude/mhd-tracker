.DEFAULT_GOAL := help

# ANSI color codes
CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
RESET  := \033[0m

.PHONY: help install install-backend install-frontend build run dev-backend dev-frontend test test-v seed clean clean-db

help: ## Show this help message
	@echo ""
	@echo "  $(CYAN)MHD Tracker$(RESET) - Build & Execution Targets"
	@echo "  -------------------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ""

install: install-backend install-frontend ## Install all backend (uv) and frontend (npm) dependencies
	@echo "$(GREEN)✓ All dependencies installed successfully!$(RESET)"

install-backend: ## Install Python dependencies using uv
	@echo "$(CYAN)Syncing Python virtualenv with uv...$(RESET)"
	uv sync

install-frontend: ## Install frontend npm packages
	@echo "$(CYAN)Installing npm packages for frontend...$(RESET)"
	cd frontend && npm install

build: ## Build frontend assets into frontend/dist for production
	@echo "$(CYAN)Building frontend with Vite...$(RESET)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend assets compiled to frontend/dist$(RESET)"

run: build ## Build frontend & run unified server (http://0.0.0.0:8000)
	@echo "$(GREEN)=====================================================$(RESET)"
	@echo "$(GREEN) Starting MHD Tracker on http://0.0.0.0:8000 $(RESET)"
	@echo "$(GREEN) Accessible on your local Wi-Fi from mobile devices  $(RESET)"
	@echo "$(GREEN)=====================================================$(RESET)"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

dev-backend: ## Run FastAPI backend with live reload (http://localhost:8000)
	@echo "$(CYAN)Starting FastAPI backend with live reload...$(RESET)"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Run Vite frontend development server (http://localhost:5173)
	@echo "$(CYAN)Starting Vite frontend dev server with HMR...$(RESET)"
	cd frontend && npm run dev

test: ## Run unit and integration tests with pytest
	@echo "$(CYAN)Running pytest test suite...$(RESET)"
	uv run pytest

test-v: ## Run pytest with verbose output
	@echo "$(CYAN)Running pytest with verbose details...$(RESET)"
	uv run pytest -v

seed: ## Populate SQLite database with sample groceries
	@echo "$(CYAN)Seeding sample grocery data...$(RESET)"
	uv run python seed_demo.py

clean: ## Clean build artifacts, temporary cache files
	@echo "$(YELLOW)Cleaning caches and temporary files...$(RESET)"
	rm -rf frontend/dist
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "$(GREEN)✓ Workspace cleaned.$(RESET)"

clean-db: ## Reset SQLite database (removes mhd_tracker.db)
	@echo "$(YELLOW)Removing mhd_tracker.db...$(RESET)"
	rm -f mhd_tracker.db
	@echo "$(GREEN)✓ Database reset. Next run will initialize a fresh database.$(RESET)"
