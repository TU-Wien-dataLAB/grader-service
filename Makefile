.PHONY: help sync test-service test-labextension test-all test-integration lint-service lint-labextension lint-all build-service build-labextension build-all docs docs-clean docs-live dev-up dev-down dev-logs dev-local clean run-service run-hub watch-labextension

SHELL := /bin/bash
GRADER_API_TOKEN ?= $(shell openssl rand -hex 16)
COMPOSE_PROJECT = grader-dev

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

sync: ## Install all dev and test dependencies for the entire project
	uv sync --all-packages --all-groups

run-service: ## Run service locally with token config
	uv run grader-service -f dev/local/token/grader_service_config.py

run-hub: ## Run JupyterHub locally with token config
	uv run jupyterhub -f dev/local/token/jupyterhub_config.py

watch-labextension: ## Watch labextension for changes and rebuild
	cd packages/labextension && jlpm watch

test-service: ## Run service tests
	uv run --package grader-service pytest packages/service/grader_service/tests --cov

test-labextension: ## Run labextension tests
	uv run --package grader-labextension pytest packages/labextension/grader_labextension/tests

test: ## Run all tests
	make test-service
	make test-labextension

test-integration: ## Create dev env, run integration tests, then down dev env
	@export GRADER_API_TOKEN=$(GRADER_API_TOKEN) && \
	echo "Using GRADER_API_TOKEN: $$GRADER_API_TOKEN" && \
	docker-compose -f dev/docker-compose/docker-compose.yml up -d && \
	sleep 5 && \
	uv run pytest tests/integration -vvv && \
	docker-compose -f dev/docker-compose/docker-compose.yml down

lint-service: ## Lint service code
	uv run --package grader-service ruff check packages/service
	uv run --package grader-service ruff format --check packages/service

lint-labextension: ## Lint labextension code
	uv run --package grader-labextension ruff check packages/labextension
	uv run --package grader-labextension ruff format --check packages/labextension

lint: ## Lint all code
	uv run ruff check packages/
	uv run ruff format --check packages/

build-service: ## Build service package
	uv build --package grader-service

build-labextension: ## Build labextension package
	uv build --package grader-labextension

build: ## Build all packages
	uv build --package grader-service
	uv build --package grader-labextension

docs: ## Build Sphinx documentation
	uv run --no-sync make -C docs html

docs-clean: ## Clean Sphinx documentation
	uv run --no-sync make -C docs clean

docs-live: ## Build and serve Sphinx documentation with live reload
	uv run --no-sync sphinx-autobuild docs/source docs/_build

dev-up: ## Start development docker-compose environment
	docker-compose -f dev/docker-compose/docker-compose.yml up -d --build

dev-down: ## Stop development docker-compose environment
	docker-compose -f dev/docker-compose/docker-compose.yml down -v

dev-logs: ## Show development environment logs
	docker-compose -f dev/docker-compose/docker-compose.yml logs -f

clean: ## Remove build artifacts
	rm -rf packages/service/dist/
	rm -rf packages/service/build/
	rm -rf packages/service/*.egg-info
	rm -rf packages/service/htmlcov/
	rm -rf packages/service/.coverage
	rm -rf packages/labextension/dist/
	rm -rf packages/labextension/build/
	rm -rf packages/labextension/*.egg-info
	rm -rf packages/labextension/htmlcov/
	rm -rf packages/labextension/.coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
