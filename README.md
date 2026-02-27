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
    │ PostgreSQL │  │   Redis   │  │    zvec    │
    │ (pgvector) │  │           │  │ (embedded) │
    └────────────┘  └───────────┘  └────────────┘
```

## Key Features

- **Multi-Agent Architecture** — LangGraph state machine with triage, product discovery, safety constraint, and response synthesis nodes
- **Safety-First Design** — Dual-gate safety (rule-based + LLM) that refuses to override allergen constraints, with ingredient interaction warnings
- **Long-Term Memory** — LangMem SDK-backed persistent memories with conflict detection, background extraction, and user consent controls
- **Persona Monitoring** — Shadow scoring for 5 behavioral traits (sycophancy, hallucination, over-confidence, safety bypass, sales pressure) with threshold interventions
- **Real Product Catalog** — Seeded from Open Beauty Facts with ingredient parsing, safety scoring, and interaction checking
- **Ingredient Interactions** — 10 known incompatible ingredient pairs flagged with severity levels

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.12 (3.13 not yet supported by zvec)
- Node.js 20+

### Development Setup

```bash
# Start infrastructure services
make infra-up

# Install backend dependencies
cd backend && pip install -e ".[dev]" && cd ..

# Run database migrations
make migrate

# Seed product catalog (optional — requires running infra)
make seed

# Start backend (terminal 1)
make backend-dev

# Start frontend (terminal 2)
make frontend-dev

# Generate demo users (optional)
make demo-users

# Run full demo scenario
make demo
```

### Full Stack with Docker

```bash
docker compose up --build
```

Then visit `http://localhost` (nginx), `http://localhost:3000` (frontend), or `http://localhost:8080/health` (backend API).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Zustand, React Query, Recharts |
| Backend | FastAPI, LangGraph, SQLAlchemy (async), Pydantic v2 |
| LLM Gateway | OpenRouter (provider-agnostic) |
| Memory | LangMem SDK + AsyncPostgresStore |
| Database | PostgreSQL 16 (pgvector) |
| Cache | Redis 7 |
| Vector Store | zvec (embedded, Alibaba Proxima) |
| Persona | MockPersonaScorer (default) or PyTorch + Llama 3.1 8B (optional) |
| CI/CD | GitHub Actions |
| Infrastructure | Docker Compose (5 services) |

## Agent Graph

```
User Message
     │
     ▼
┌─────────────┐
│   Triage    │ ── Classify intent + load memory
│   Router    │
└──────┬──────┘
       │
       ├── product_search ──┐
       ├── ingredient_check ─┤
       ├── routine_advice ───┤
       │                     ▼
       │              ┌────────────┐
       │              │  Product   │ Hybrid search + interaction check
       │              │ Discovery  │
       │              └─────┬──────┘
       │                    ▼
       │              ┌────────────┐
       │              │  Safety    │ Dual-gate (rule + LLM)
       │              │ Validator  │
       │              └─────┬──────┘
       │                    │
       ├── memory_query ────┤
       └── general_chat ────┤
                            ▼
                     ┌────────────┐
                     │  Response  │ Natural language + memory acks
                     │  Synth     │
                     └────────────┘
                            │
                     ┌──────┴──────┐
                     │  Persona    │ Fire-and-forget scoring
                     │  Monitor    │
                     └─────────────┘
```

## Project Structure

```
ai-shopping-concierge/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes (triage, discovery, safety, response)
│   │   ├── api/routes/      # FastAPI endpoints (chat, users, products, memory, persona)
│   │   ├── catalog/         # Product catalog, ingredients, safety scoring, interactions
│   │   ├── core/            # Database, Redis, LLM configuration
│   │   ├── memory/          # LangMem config, conflict detection, background extraction
│   │   ├── models/          # SQLAlchemy models (user, product, conversation, persona)
│   │   └── persona/         # Traits, monitor, vector extractor, mock scorer
│   ├── tests/
│   │   ├── unit/            # Unit tests (174 tests)
│   │   ├── integration/     # Pipeline and API integration tests
│   │   └── eval/            # Evaluation suite (safety, memory, persona)
│   └── scripts/             # Seed catalog, compute vectors, migrate memory
├── frontend/
│   └── src/
│       ├── components/      # React components (chat, products, profile, persona)
│       ├── stores/          # Zustand (chatStore, userStore, personaStore)
│       ├── hooks/           # React Query + SSE hooks
│       └── api/             # API client (chat, users, products, persona)
├── scripts/                 # Demo scenario, test user generation
├── docs/                    # Architecture, API, decisions, persona vectors
├── infra/                   # Postgres init, Nginx config
├── docker-compose.yml       # 5-service Docker stack
├── Makefile                 # Development commands
└── CHANGELOG.md             # Version history
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
| GET | `/api/v1/conversations/{id}/messages` | Get messages |
| GET | `/api/v1/users/{id}/memory` | Get user memories |
| DELETE | `/api/v1/users/{id}/memory/{mid}` | Delete memory |
| GET | `/api/v1/users/{id}/memory/constraints` | Get constraints |
| POST | `/api/v1/users/{id}/memory/constraints` | Add constraint |
| GET | `/api/v1/persona/scores` | Get persona scores |
| GET | `/api/v1/persona/history` | Get persona history |
| GET | `/api/v1/persona/alerts` | Get persona alerts |
| GET | `/api/v1/persona/stream` | SSE persona updates |

## Testing

```bash
make test              # All tests with coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-eval         # Evaluation suite
make lint              # Code quality (black + isort + flake8)
```

## Demo

```bash
# Generate 5 demo users with varied profiles
make demo-users

# Run 10-step comprehensive demo
make demo
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design and data flow
- [API Reference](docs/API.md) — Endpoint documentation
- [Decisions](docs/DECISIONS.md) — Architectural decision records
- [Persona Vectors](docs/PERSONA_VECTORS.md) — Persona monitoring details
- [Changelog](CHANGELOG.md) — Version history

## License

MIT
