.PHONY: install install-dev run dev test lint format typecheck check docker-build docker-up docker-down docker-logs clean

VENV_PYTHON ?= python

install:
	$(VENV_PYTHON) -m pip install -r requirements.txt

install-dev:
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

run:
	$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	$(VENV_PYTHON) -m pytest

lint:
	$(VENV_PYTHON) -m ruff check app tests
	$(VENV_PYTHON) -m isort --check-only app tests
	$(VENV_PYTHON) -m black --check app tests

format:
	$(VENV_PYTHON) -m isort app tests
	$(VENV_PYTHON) -m black app tests
	$(VENV_PYTHON) -m ruff check --fix app tests

typecheck:
	$(VENV_PYTHON) -m mypy app

check: lint typecheck test

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
