# Development Guide

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
Set-Location backend
uvicorn app.main:app --reload
```

The API documentation is served at `http://localhost:8000/docs`.

## Docker Setup

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Docker Compose starts the API, PostgreSQL, pgAdmin, and Ollama on a shared bridge network with named volumes.

## Verification

Run syntax verification from the repository root:

```powershell
python -m compileall backend/app
```

Run an import check from the backend directory:

```powershell
Set-Location backend
python -c "from app.main import app; print(app.title)"
```
