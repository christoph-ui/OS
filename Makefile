.PHONY: help install dev test lint format clean build-base build-all docker-up docker-down logs

# Variables
PYTHON := python3.11
PIP := $(PYTHON) -m pip
REGISTRY := registry.0711.ai
VERSION := $(shell jq -r '.version' build/version.json)
DOCKER_COMPOSE := docker compose

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m  # No Color

help:  ## Show this help message
	@echo "$(CYAN)0711 Platform - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ========================================
# Development Setup
# ========================================

install:  ## Install Python dependencies
	@echo "$(CYAN)Installing 0711 Platform dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel uv
	uv pip install --system -e ".[dev]"
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-gpu:  ## Install with GPU support
	@echo "$(CYAN)Installing with GPU support...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel uv
	uv pip install --system -e ".[all]"
	@echo "$(GREEN)✓ GPU dependencies installed$(NC)"

dev:  ## Set up development environment
	@echo "$(CYAN)Setting up development environment...$(NC)"
	$(MAKE) install
	pre-commit install 2>/dev/null || echo "pre-commit not available"
	@echo "$(GREEN)✓ Development environment ready$(NC)"

# ========================================
# Code Quality
# ========================================

lint:  ## Run linters (ruff, mypy)
	@echo "$(CYAN)Running linters...$(NC)"
	ruff check ingestion/ lakehouse/ mcps/ orchestrator/ console/ provisioning/
	mypy ingestion/ lakehouse/ mcps/ orchestrator/ console/ provisioning/

format:  ## Format code with black and ruff
	@echo "$(CYAN)Formatting code...$(NC)"
	black ingestion/ lakehouse/ mcps/ orchestrator/ console/ provisioning/ tests/
	ruff check --fix ingestion/ lakehouse/ mcps/ orchestrator/ console/ provisioning/
	@echo "$(GREEN)✓ Code formatted$(NC)"

test:  ## Run tests
	@echo "$(CYAN)Running tests...$(NC)"
	pytest tests/ -v --cov --cov-report=html
	@echo "$(GREEN)✓ Tests complete. Coverage report: htmlcov/index.html$(NC)"

test-fast:  ## Run tests without coverage
	@echo "$(CYAN)Running tests (fast mode)...$(NC)"
	pytest tests/ -v -x

# ========================================
# Docker Build
# ========================================

build-base:  ## Build base Docker image
	@echo "$(CYAN)Building base image...$(NC)"
	docker build -t $(REGISTRY)/0711-base:$(VERSION) \
		-t $(REGISTRY)/0711-base:latest \
		-f build/Dockerfile.base .
	@echo "$(GREEN)✓ Base image built: $(REGISTRY)/0711-base:$(VERSION)$(NC)"

build-ingestion:  ## Build ingestion image
	@echo "$(CYAN)Building ingestion image...$(NC)"
	docker build -t $(REGISTRY)/0711-ingestion:$(VERSION) \
		-t $(REGISTRY)/0711-ingestion:latest \
		-f build/Dockerfile.ingestion \
		--build-arg BASE_IMAGE=$(REGISTRY)/0711-base:$(VERSION) .
	@echo "$(GREEN)✓ Ingestion image built$(NC)"

build-compute:  ## Build compute image (Ray + MCPs)
	@echo "$(CYAN)Building compute image...$(NC)"
	docker build -t $(REGISTRY)/0711-compute:$(VERSION) \
		-t $(REGISTRY)/0711-compute:latest \
		-f build/Dockerfile.compute \
		--build-arg BASE_IMAGE=$(REGISTRY)/0711-base:$(VERSION) .
	@echo "$(GREEN)✓ Compute image built$(NC)"

build-inference:  ## Build vLLM inference image
	@echo "$(CYAN)Building inference image...$(NC)"
	docker build -t $(REGISTRY)/0711-inference:$(VERSION) \
		-t $(REGISTRY)/0711-inference:latest \
		-f inference/Dockerfile .
	@echo "$(GREEN)✓ Inference image built$(NC)"

build-console:  ## Build console image
	@echo "$(CYAN)Building console images...$(NC)"
	docker build -t $(REGISTRY)/0711-console-backend:$(VERSION) \
		-f console/backend/Dockerfile console/backend/
	docker build -t $(REGISTRY)/0711-console-frontend:$(VERSION) \
		-f console/frontend/Dockerfile console/frontend/
	@echo "$(GREEN)✓ Console images built$(NC)"

build-wizard:  ## Build setup wizard image
	@echo "$(CYAN)Building wizard image...$(NC)"
	docker build -t $(REGISTRY)/0711-wizard:$(VERSION) \
		-f provisioning/Dockerfile provisioning/
	@echo "$(GREEN)✓ Wizard image built$(NC)"

build-all:  ## Build all Docker images
	@echo "$(CYAN)Building all images...$(NC)"
	$(MAKE) build-base
	$(MAKE) build-ingestion
	$(MAKE) build-compute
	$(MAKE) build-inference
	$(MAKE) build-console
	$(MAKE) build-wizard
	@echo "$(GREEN)✓ All images built successfully$(NC)"

# ========================================
# Docker Deployment
# ========================================

docker-up:  ## Start all services
	@echo "$(CYAN)Starting 0711 Platform...$(NC)"
	cd deployment && $(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Platform started$(NC)"
	@echo "  Console: http://localhost:3000"
	@echo "  API: http://localhost:8080"
	@echo "  Ray Dashboard: http://localhost:8265"

docker-up-wizard:  ## Start setup wizard only
	@echo "$(CYAN)Starting setup wizard...$(NC)"
	cd deployment && $(DOCKER_COMPOSE) --profile setup up -d wizard
	@echo "$(GREEN)✓ Wizard started: http://localhost:8090$(NC)"

docker-down:  ## Stop all services
	@echo "$(CYAN)Stopping platform...$(NC)"
	cd deployment && $(DOCKER_COMPOSE) down

docker-down-v:  ## Stop all services and remove volumes
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd deployment && $(DOCKER_COMPOSE) down -v; \
		echo "$(GREEN)✓ All services stopped and volumes removed$(NC)"; \
	fi

docker-restart:  ## Restart all services
	$(MAKE) docker-down
	$(MAKE) docker-up

logs:  ## Show logs from all services
	cd deployment && $(DOCKER_COMPOSE) logs -f

logs-ingestion:  ## Show ingestion logs
	cd deployment && $(DOCKER_COMPOSE) logs -f ingestion

logs-console:  ## Show console logs
	cd deployment && $(DOCKER_COMPOSE) logs -f console-backend console-frontend

logs-mcps:  ## Show MCP logs
	cd deployment && $(DOCKER_COMPOSE) logs -f ray-head ray-worker

# ========================================
# Database & Storage
# ========================================

init-lakehouse:  ## Initialize lakehouse storage
	@echo "$(CYAN)Initializing lakehouse...$(NC)"
	./deployment/scripts/init-lakehouse.sh
	@echo "$(GREEN)✓ Lakehouse initialized$(NC)"

backup:  ## Backup customer data
	@echo "$(CYAN)Creating backup...$(NC)"
	./deployment/scripts/backup.sh
	@echo "$(GREEN)✓ Backup complete$(NC)"

# ========================================
# Maintenance
# ========================================

clean:  ## Clean build artifacts and caches
	@echo "$(CYAN)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ dist/ build/ .eggs/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-docker:  ## Clean Docker images and build cache
	@echo "$(CYAN)Cleaning Docker artifacts...$(NC)"
	docker image prune -f
	docker builder prune -f
	@echo "$(GREEN)✓ Docker cleanup complete$(NC)"

health:  ## Check system health
	@echo "$(CYAN)Checking system health...$(NC)"
	./deployment/scripts/health-check.sh

# ========================================
# Utilities
# ========================================

shell-ingestion:  ## Open shell in ingestion container
	cd deployment && $(DOCKER_COMPOSE) exec ingestion /bin/bash

shell-compute:  ## Open shell in compute container
	cd deployment && $(DOCKER_COMPOSE) exec ray-head /bin/bash

shell-console:  ## Open shell in console container
	cd deployment && $(DOCKER_COMPOSE) exec console-backend /bin/bash

version:  ## Show current version
	@echo "$(CYAN)0711 Platform$(NC) v$(VERSION)"
	@jq . build/version.json

.DEFAULT_GOAL := help
