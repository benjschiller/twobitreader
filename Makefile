.PHONY: help install test docs build clean lint format check

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	python -m pip install -e ".[dev,docs]"

test:  ## Run tests
	python -m unittest discover -s tests
	python test_package.py

docs:  ## Build documentation
	sphinx-build -W --keep-going -b html doc doc/_build/html

build:  ## Build the package
	python -m build

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:  ## Run linting checks
	pre-commit run --all-files

format:  ## Format code with black and isort
	black twobitreader tests doc

check:  ## Run all checks (lint, format check, build test)
	pre-commit run --all-files
	python -m unittest discover -s tests
	python test_package.py
	sphinx-build -W --keep-going -b html doc doc/_build/html
	python -m build
	twine check dist/*

ci-test:  ## Run tests similar to CI
	python -m pip install --upgrade pip
	pip install build
	python -m build
	pip install dist/twobitreader-*.whl
	python test_package.py
