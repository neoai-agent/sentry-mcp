.PHONY: help install install-dev test lint format clean build publish

help: ## Show this help message
	@echo "Sentry MCP Server - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run tests
	pytest tests/ -v

lint: ## Run linting checks
	ruff check sentry_mcp/
	mypy sentry_mcp/

format: ## Format code
	black sentry_mcp/
	isort sentry_mcp/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	python -m build

publish: build ## Publish to PyPI (requires twine)
	twine upload dist/*

check: lint test ## Run all checks (lint + test)

dev-setup: install-dev ## Set up development environment
	@echo "Development environment set up successfully!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to run linting"
	@echo "Run 'make format' to format code"
