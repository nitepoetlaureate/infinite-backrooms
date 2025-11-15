.PHONY: help install install-dev test lint format type-check security clean run run-log-viewer docker-build docker-up docker-down pre-commit

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:  ## Run tests with coverage
	pytest --cov=. --cov-report=term-missing --cov-report=html

test-verbose:  ## Run tests with verbose output
	pytest -v --cov=. --cov-report=term-missing

lint:  ## Run linting checks
	ruff check .

format:  ## Format code with ruff
	ruff format .
	ruff check --fix .

type-check:  ## Run type checking
	mypy streamlit_backroom.py log_viewer.py --ignore-missing-imports

security:  ## Run security checks
	bandit -r . -c pyproject.toml

clean:  ## Clean up generated files
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

run:  ## Run the main Streamlit app
	streamlit run streamlit_backroom.py

run-log-viewer:  ## Run the log viewer app
	streamlit run log_viewer.py

docker-build:  ## Build Docker images
	docker-compose build

docker-up:  ## Start Docker containers
	docker-compose up -d

docker-down:  ## Stop Docker containers
	docker-compose down

docker-logs:  ## View Docker container logs
	docker-compose logs -f

pre-commit:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

check-all: lint type-check security test  ## Run all checks (lint, type-check, security, test)

dev-setup: install-dev pre-commit  ## Complete development setup
	@echo "Development environment setup complete!"
	@echo "Run 'make run' to start the application"
