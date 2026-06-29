# 🚀 PersonaAI

> **One AI Brain. Multiple Connectors. Infinite Possibilities.**

![Version](https://img.shields.io/badge/version-v1.0--alpha-blue)
![Python](https://img.shields.io/badge/Python-3.12+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-success)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue)
![License](https://img.shields.io/badge/license-MIT-orange)

---

# 📖 Overview

PersonaAI is a production-grade AI Communication Operating System designed to understand, organize, summarize, and search information across multiple communication platforms.

Unlike traditional AI assistants that focus on a single platform, PersonaAI introduces a connector-based architecture where every communication source is normalized into a common format before being processed by a central AI engine.

The goal is to create a platform capable of understanding conversations, emails, documents, meetings, and future communication channels while remaining modular and extensible.

---

# 🎯 Vision

Build an AI that acts like a personal communication intelligence system.

Instead of opening five different applications to understand what happened today, PersonaAI should answer questions such as:

* What happened while I was away?
* Summarize today's discussions.
* What tasks are assigned to me?
* What meetings are scheduled this week?
* What did my manager ask yesterday?
* Show conversations related to Project X.

The AI should understand information instead of simply storing it.

---

# ✨ Core Features

## Communication Connectors

* Gmail
* WhatsApp
* Slack
* Discord
* Telegram
* Google Calendar
* Google Drive
* Microsoft Teams (Future)
* Zoom Transcripts (Future)

---

## AI Features

* AI Summarization
* Semantic Search
* Task Extraction
* Deadline Detection
* Meeting Extraction
* Decision Extraction
* Priority Classification
* Conversational Memory
* Daily AI Digest
* Weekly Reports
* Question Answering

---

## Backend Features

* FastAPI
* PostgreSQL
* pgvector
* SQLAlchemy
* Alembic
* Docker
* Google OAuth
* JWT Authentication
* Async Architecture
* Plugin System
* Repository Pattern
* Clean Architecture

---

# 🧠 Project Philosophy

PersonaAI is designed around one simple principle:

> **The AI should never know where information came from.**

Every connector converts its platform-specific data into a common communication model.

Example:

```text
Gmail
  ↓
Communication Object
  ↓
PersonaAI Engine
  ↓
Summary
Task Extraction
Search
Memory
```

The AI processes standardized communication instead of platform-specific data.

This allows new connectors to be added without modifying the AI core.

---

# 🏗 High-Level Architecture

```text
                    PersonaAI

                AI Intelligence Core

                         │

      ┌──────────────────┼──────────────────┐

      │                  │                  │

   Gmail            WhatsApp             Slack

      │                  │                  │

      └──────────────────┼──────────────────┘

                 Communication Layer

                         │

                AI Processing Engine

                         │

      ┌───────────────────────────────────┐

      │ Summaries                         │

      │ Tasks                             │

      │ Meetings                          │

      │ Deadlines                         │

      │ Semantic Search                   │

      │ Conversational Memory             │

      └───────────────────────────────────┘

                         │

               PostgreSQL + pgvector
```

---

# ⚙ Technology Stack

## Backend

* FastAPI
* Python 3.12+
* SQLAlchemy 2.x
* Alembic

---

## Database

* PostgreSQL
* pgvector

---

## AI

* Ollama
* Llama 3
* Mistral
* Sentence Transformers

---

## Authentication

* Google OAuth2
* JWT

---

## Infrastructure

* Docker
* Docker Compose

---

## Development

* Git
* GitHub
* Pytest
* Ruff
* Black
* MyPy

---

# 📂 Project Structure

```text
PersonaAI/

backend/

frontend/

docs/

docker/

tests/

tasks/

README.md

LICENSE

docker-compose.yml

.env.example
```

Detailed documentation is available inside the **docs/** directory.

---

# 🚧 Development Roadmap

## Phase 0

Project Foundation

* Repository
* Docker
* Documentation
* Project Structure

---

## Phase 1

Core Backend

* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Configuration
* Logging
* Health Check API

---

## Phase 2

Authentication

* Google OAuth
* JWT
* User Management
* Session Management

---

## Phase 3

Communication Layer

* Gmail Connector
* Message Synchronization
* Email Parsing
* Communication Model

---

## Phase 4

AI Engine

* Ollama Integration
* Embeddings
* Semantic Search
* Summarization

---

## Phase 5

Intelligence

* Task Extraction
* Deadline Detection
* Meeting Detection
* Conversational Memory

---

## Phase 6

Plugin Architecture

* Connector SDK
* WhatsApp Connector
* Slack Connector
* Discord Connector

---

## Phase 7

Production

* Docker Deployment
* Monitoring
* Security
* Performance Optimization

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone <repository-url>

cd PersonaAI
```

---

## Configure Environment

```bash
cp .env.example .env
```

---

## Start Services

```bash
docker compose up --build
```

---

## Run Backend Locally

```bash
cd backend

uvicorn app.main:app --reload
```

---

## API Documentation

Swagger

```text
http://localhost:8000/docs
```

ReDoc

```text
http://localhost:8000/redoc
```

Health Check

```text
http://localhost:8000/health
```

---

# 📚 Documentation

Project documentation is located inside the `docs/` directory.

It includes:

* Project Vision
* System Architecture
* Backend Architecture
* Database Design
* API Design
* Development Roadmap
* Coding Standards
* Architecture Decisions

---

# 🤝 Contributing

This project follows a documentation-first development workflow.

Before implementing new features:

1. Design
2. Document
3. Review
4. Implement
5. Test
6. Deploy

Every feature must include appropriate documentation and tests.

---

# 📜 License

This project is released under the MIT License.

---

# 🌟 Long-Term Goal

PersonaAI aims to become an extensible AI platform capable of understanding and organizing information from multiple communication systems through a unified intelligence engine.

Rather than building separate AI assistants for Gmail, WhatsApp, Slack, or future platforms, PersonaAI focuses on building one reusable AI core that can process communication from any source through a standardized connector architecture.

---

## "One AI Brain. Multiple Connectors. Infinite Possibilities."
