# =================================================================================================
# Moxfield Analyzer - Makefile (Windows/Linux/Mac compatible)
# =================================================================================================

# VARIABLES
VENV_DIR := .venv

UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

.PHONY: help dev setup install install-playwright lint format typecheck pre-commit test sync docker-up docker-down docker-logs docker-rebuild venv clean

# =================================================================================================
# HELP
# =================================================================================================
help:
	@echo ""
	@echo "Moxfield Analyzer - Available commands:"
	@echo ""
	@echo "  make setup            # Complete project setup (install + playwright)"
	@echo "  make dev              # Start FastAPI server (http://0.0.0.0:3000)"
	@echo "  make lint             # Lint + auto-fix (ruff)"
	@echo "  make format           # Format code (ruff)"
	@echo "  make typecheck        # Static type checking (mypy)"
	@echo "  make pre-commit       # Run lint + format + typecheck"
	@echo "  make test             # Run tests (pytest)"
	@echo "  make sync             # Install/update dependencies"
	@echo "  make docker-up        # Start Docker Compose services"
	@echo "  make docker-down      # Stop Docker Compose services"
	@echo "  make docker-logs      # Tail Docker Compose logs"
	@echo "  make docker-rebuild   # Rebuild and start Docker Compose services"
	@echo "  make venv             # Create virtual environment"
	@echo "  make clean            # Clean caches + virtual environment"
	@echo "  make help             # Show this help"
	@echo ""

# =================================================================================================
# DEVELOPMENT
# =================================================================================================
install:
	uv sync

install-playwright:
	uv run playwright install chromium --with-deps

setup: install install-playwright

dev:
	uv run uvicorn src.main:app --port 3000 --host 0.0.0.0

# =================================================================================================
# CODE QUALITY
# =================================================================================================
lint:
	uv run ruff check src/ tests/ --fix
	@echo "Lint completed!"

format:
	uv run ruff format src/ tests/
	@echo "Code formatted!"

typecheck:
	uv run mypy src/
	@echo "Type check completed!"

pre-commit: lint format typecheck
	@echo "Pre-commit: lint + format + typecheck OK!"

# =================================================================================================
# TESTS
# =================================================================================================
test:
	uv run pytest -v

# =================================================================================================
# MANAGEMENT
# =================================================================================================
sync:
	uv sync --dev
	@echo "Dependencies synced!"

# =================================================================================================
# DOCKER
# =================================================================================================
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-rebuild:
	docker compose up -d --build

# =================================================================================================
# VIRTUAL ENVIRONMENT
# =================================================================================================
venv:
	@echo "Creating virtual environment..."
	@if [ -d "$(VENV_DIR)" ]; then \
		echo ".venv already exists! Run 'make clean' first."; \
	else \
		uv venv; \
		if [ -d "$(VENV_DIR)" ]; then \
			echo ""; \
			echo "SUCCESS: Virtual environment created: $(VENV_DIR)"; \
			echo ""; \
			echo "Activate with one of these commands:"; \
			echo "  Unix/Mac: source $(VENV_DIR)/bin/activate"; \
			echo "  Windows:  $(VENV_DIR)\\Scripts\\activate"; \
			echo ""; \
		else \
			echo "ERROR: .venv not created. Check uv installation."; \
		fi; \
	fi

# =================================================================================================
# CLEAN
# =================================================================================================
clean:
	uv cache clean
	rm -rf .coverage htmlcov/ dist/ build/ .pytest_cache/ .ruff_cache/ $(VENV_DIR)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "Project cleaned!"
