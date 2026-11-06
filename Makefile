.DEFAULT_GOAL := help

# ANSI color codes
CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
RESET  := \033[0m

.PHONY: help install install-backend install-frontend build run run-ssl cert dev-backend dev-frontend test test-v seed clean clean-db ci ci-local ci-act

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

cert: ## Generate self-signed SSL certificate for local HTTPS (certs/)
	@echo "$(CYAN)Checking / generating SSL certificate...$(RESET)"
	@mkdir -p certs
	@if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then \
		openssl req -x509 -newkey rsa:2048 -nodes -keyout certs/key.pem -out certs/cert.pem -days 365 -subj "/CN=mhd-tracker" 2>/dev/null; \
		echo "$(GREEN)✓ New SSL certificate generated in certs/$(RESET)"; \
	else \
		echo "$(GREEN)✓ SSL certificates already exist in certs/$(RESET)"; \
	fi

run: build ## Build frontend & run HTTP server (http://0.0.0.0:8000)
	@echo "$(GREEN)=====================================================$(RESET)"
	@echo "$(GREEN) Starting MHD Tracker on http://0.0.0.0:8000 $(RESET)"
	@echo "$(GREEN) Accessible on your local Wi-Fi from mobile devices  $(RESET)"
	@echo "$(GREEN)=====================================================$(RESET)"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

run-ssl: build cert ## Build frontend & run HTTPS server (https://0.0.0.0:8000) for mobile live camera
	@echo "$(GREEN)=====================================================$(RESET)"
	@echo "$(GREEN) Starting HTTPS MHD Tracker on https://0.0.0.0:8000 $(RESET)"
	@echo "$(GREEN) Unlocks live camera scanning on iPhone & Android   $(RESET)"
	@echo "$(GREEN) (Accept self-signed certificate in mobile browser) $(RESET)"
	@echo "$(GREEN)=====================================================$(RESET)"
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
	#uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem


dev-backend: ## Run FastAPI backend with live reload (http://localhost:8000)
	@echo "$(CYAN)Starting FastAPI backend with live reload...$(RESET)"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Run Vite frontend development server (http://localhost:5173)
	@echo "$(CYAN)Starting Vite frontend dev server with HMR...$(RESET)"
	cd frontend && npm run dev

test: ## Run unit and integration tests with pytest and vitest
	@echo "$(CYAN)Running backend tests with pytest...$(RESET)"
	uv run pytest
	@echo "$(CYAN)Running frontend tests with vitest...$(RESET)"
	cd frontend && npm run test


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
	rm -rf .coverage coverage frontend/coverage site
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "$(GREEN)✓ Workspace cleaned.$(RESET)"

clean-db: ## Reset SQLite database (removes mhd_tracker.db)
	@echo "$(YELLOW)Removing mhd_tracker.db...$(RESET)"
	rm -f mhd_tracker.db
	@echo "$(GREEN)✓ Database reset. Next run will initialize a fresh database.$(RESET)"

ci: ci-local ## Alias for ci-local

ci-local: ## Run complete CI pipeline locally (lint, tests, coverage, build, site)
	@echo "$(CYAN)Running local CI pipeline...$(RESET)"
	uv run python scripts/run_ci_local.py

ci-act: ## Run GitHub Actions workflow locally via nektos/act in Docker
	@if command -v act >/dev/null 2>&1; then \
		echo "$(CYAN)Running GitHub Actions locally with act...$(RESET)"; \
		TOKEN_ARG=""; \
		if [ -n "$$GITHUB_TOKEN" ]; then \
			TOKEN_ARG="-s GITHUB_TOKEN=$$GITHUB_TOKEN"; \
		fi; \
		act pull_request $$TOKEN_ARG --container-architecture linux/amd64; \
	else \
		echo "$(YELLOW)act is not installed.$(RESET)"; \
		echo "To run GitHub Actions locally with Docker, install 'act':"; \
		echo "  macOS (Homebrew): brew install act"; \
		echo "  Linux: curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"; \
		echo "  Windows (Scoop): scoop install act"; \
		echo "Or run the fast local native pipeline with:"; \
		echo "  make ci-local"; \
		exit 1; \
	fi
