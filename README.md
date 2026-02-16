# AI Beauty Shopping Concierge

A production-grade multi-agent AI system for personalized beauty and skincare recommendations, featuring safety-first design, long-term memory, and persona monitoring.

## Architecture

```
                    ┌─────────────┐
                    │   Frontend  │  React 18 + TypeScript + Tailwind
                    │  (port 3000)│
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │    Nginx    │  Reverse Proxy
                    │  (port 80)  │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   FastAPI   │  Backend API
                    │  (port 8080)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────┴──┐  ┌─────┴─────┐  ┌──┴─────────┐
    │  LangGraph │  │  Safety   │  │  Persona   │
    │   Agents   │  │   Gate    │  │  Monitor   │
    └─────────┬──┘  └─────┬─────┘  └──┬─────────┘
              │            │            │
    ┌─────────┴──┐  ┌─────┴─────┐  ┌──┴─────────┐
    │ PostgreSQL │  │   Redis   │  │  ChromaDB  │
    │ (pgvector) │  │           │  │  (vectors) │
    └────────────┘  └───────────┘  └────────────┘
```

## Key Features

- **Multi-Agent Architecture** — LangGraph state machine with triage, product discovery, safety constraint, and response synthesis nodes
- **Safety-First Design** — Dual-gate safety architecture (rule-based + LLM) that refuses to override allergen constraints
- **Long-Term Memory** — Persistent user memories across sessions with memory inspector
- **Persona Monitoring** — Hidden state activation analysis via raw transformers (Llama 3.1 8B) to detect sycophancy, hallucination, and safety bypass
- **Real Product Catalog** — Seeded from Open Beauty Facts with ingredient parsing and safety scoring

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 20+

### Development Setup

```bash
# Clone and enter the project
cd ai-shopping-concierge

# Start infrastructure services
make infra-up

# Install backend dependencies
cd backend && pip install -e ".[dev]" && cd ..

# Run database migrations
make migrate

# Seed product catalog
make seed

# Start backend (terminal 1)
make backend-dev

# Start frontend (terminal 2)
make frontend-dev
```

### Full Stack with Docker

```bash
docker compose up --build
```

Then visit `http://localhost` (nginx), or `http://localhost:3000` (frontend direct), or `http://localhost:8080/health` (backend API).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Zustand, React Query, Recharts |
| Backend | FastAPI, LangGraph, SQLAlchemy (async), Pydantic v2 |
| LLM Gateway | OpenRouter (provider-agnostic) |
| Database | PostgreSQL 16 (pgvector) |
| Cache | Redis 7 |
| Vector Store | ChromaDB |
| Persona | PyTorch + HuggingFace Transformers (Llama 3.1 8B) |
| CI/CD | GitHub Actions |
| Infrastructure | Docker Compose (6 services) |

## Agent Graph

```
User Message
     │
     ▼
┌─────────────┐
│   Triage    │ ──── Classify intent
│   Router    │
└──────┬──────┘
       │
       ├── product_search ──┐
       ├── ingredient_check ─┤
       ├── routine_advice ───┤
       │                     ▼
       │              ┌────────────┐
       │              │  Safety    │ Pre-filter by allergens
       │              │ Pre-Gate   │
       │              └─────┬──────┘
       │                    ▼
       │              ┌────────────┐
       │              │  Product   │ Semantic search + ranking
       │              │ Discovery  │
       │              └─────┬──────┘
       │                    ▼
       │              ┌────────────┐
       │              │  Safety    │ LLM post-validation
       │              │ Post-Gate  │
       │              └─────┬──────┘
       │                    │
       └── general_chat ────┤
                            ▼
                     ┌────────────┐
                     │  Response  │ Natural language synthesis
                     │  Synth     │
                     └────────────┘
```

## Project Structure

```
ai-shopping-concierge/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes (triage, discovery, safety, response)
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── catalog/         # Product catalog, ingredients, safety scoring
│   │   ├── core/            # Database, Redis, LLM configuration
│   │   ├── memory/          # Long-term memory management
│   │   ├── models/          # SQLAlchemy models
│   │   └── persona/         # Persona monitoring (traits, vectors, monitor)
│   ├── tests/
│   └── scripts/
├── frontend/
│   └── src/
│       ├── components/      # React components (chat, products, profile, persona)
│       ├── stores/          # Zustand state management
│       ├── hooks/           # React Query hooks
│       └── api/             # API client
├── infra/                   # Postgres init, Nginx config
├── docker-compose.yml       # 6-service Docker stack
└── Makefile
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (DB + Redis) |
| POST | `/api/v1/chat` | Send chat message |
| POST | `/api/v1/chat/stream` | SSE streaming chat |
| POST | `/api/v1/users` | Create user |
| GET | `/api/v1/users/{id}` | Get user profile |
| PATCH | `/api/v1/users/{id}` | Update user profile |
| GET | `/api/v1/products/search` | Search products |
| GET | `/api/v1/products/{id}` | Get product details |
| GET | `/api/v1/conversations` | List conversations |
| GET | `/api/v1/users/{id}/memory` | Get user memories |
| GET | `/api/v1/persona/scores` | Get persona scores |
| GET | `/api/v1/persona/history` | Get persona history |

## Testing

```bash
# Run all backend tests
make test

# Run with coverage report
cd backend && python -m pytest tests/ -v --cov=app --cov-report=html

# Lint
make lint
```

## License

MIT
