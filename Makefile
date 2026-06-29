PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: install install-dev up down logs dev lint format test compile migrate

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload

lint:
	ruff check backend tests
	mypy backend/app

format:
	ruff format backend tests
	black backend tests
	isort backend tests

test:
	pytest

compile:
	$(PYTHON) -m compileall backend/app

migrate:
	alembic upgrade head
