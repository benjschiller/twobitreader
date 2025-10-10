.PHONY: help install test build clean lint format check

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	pip install -e .

test:  ## Run basic tests
	python test_package.py

build:  ## Build the package
	python -m build

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:  ## Run linting checks
	flake8 twobitreader/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 twobitreader/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:  ## Format code with black and isort
	black twobitreader/
	isort twobitreader/

check:  ## Run all checks (lint, format check, build test)
	@echo "Running format check..."
	black --check twobitreader/
	isort --check-only twobitreader/
	@echo "Running linting..."
	flake8 twobitreader/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "Testing build..."
	python -m build
	@echo "Testing package..."
	python test_package.py
	@echo "All checks passed! ✅"

ci-test:  ## Run tests similar to CI
	python -m pip install --upgrade pip
	pip install build
	python -m build
	pip install dist/twobitreader-*.whl
	python test_package.py
