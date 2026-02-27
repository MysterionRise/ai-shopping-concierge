# CLAUDE.md — AI Beauty Shopping Concierge

## Project Overview

Multi-agent AI system for personalized beauty/skincare product recommendations. Built as a portfolio project demonstrating LangGraph orchestration, safety-first architecture, long-term memory, and persona monitoring.

**Stack:** FastAPI + LangGraph (backend) | React 18 + TypeScript + Tailwind (frontend) | PostgreSQL + Redis + zvec (data)

---

## Quick Start

```bash
# 1. Infrastructure
make infra-up              # Starts postgres, redis

# 2. Backend
cp .env.example .env       # Configure (works without API key via demo mode)
cd backend && alembic upgrade head   # Create tables
make backend-dev           # Uvicorn on :8080

# 3. Frontend
cd frontend && npm install
make frontend-dev          # Vite on :3000 (proxies /api to :8080)

# 4. Verify
curl localhost:8080/health
python scripts/demo_scenario.py
python scripts/generate_test_users.py
```

---

## Architecture

### Agent Graph (LangGraph StateGraph)

```
User Message
     │
     ▼
triage_router ──── classify intent via LLM
     │
     ├─ product_search ──┐
     ├─ ingredient_check ─┤
     ├─ routine_advice ───┤
     │                    ▼
     │          safety_pre_filter ── rule-based allergen check
     │                    │
     │                    ▼
     │          product_discovery ── extract search intent, query DB/zvec embedded vectors
     │                    │
     │                    ▼
     │          safety_post_validate ── LLM synonym check
     │                    │
     │                    ▼
     └─ general_chat ──► response_synth ── generate conversational response
                                │
                                ▼
                          AI Response
```

### AgentState (TypedDict)

Defined in `backend/app/agents/state.py`. Key fields:
- `messages` — LangChain message list with `add_messages` reducer
- `user_id`, `conversation_id` — session tracking
- `user_profile` — skin_type, concerns from DB
- `hard_constraints` — allergies (absolute, cannot override)
- `soft_preferences` — preferences (flexible)
- `current_intent` — one of: `product_search`, `ingredient_check`, `routine_advice`, `general_chat`
- `product_results`, `safety_violations`, `safety_check_passed` — pipeline state
- `memory_context` — retrieved memories from prior sessions
- `persona_scores` — per-trait monitoring scores

### Safety Architecture (Dual-Gate)

1. **Gate 1 (Rule-based):** `ingredient_parser.find_allergen_matches()` — checks ingredients against user allergies with synonym expansion (e.g., "paraben" → methylparaben, ethylparaben, etc.)
2. **Gate 2 (LLM):** Post-check on remaining products for synonyms the rule engine missed
3. **Override protection:** `check_override_attempt()` in chat route detects phrases like "show it anyway" and returns `OVERRIDE_REFUSAL`

### LLM Configuration

- **Production:** OpenRouter via `langchain_openai.ChatOpenAI` (configurable model)
- **Demo mode:** `DemoChatModel` (deterministic, no API key needed) — automatically activated when `OPENROUTER_API_KEY` is empty or set to the placeholder value
- LLM factory: `app/core/llm.py:get_llm(**kwargs)`

---

## Project Structure

```
backend/
    app/
        agents/          # LangGraph nodes: state.py, graph.py, triage_router.py,
                         #   product_discovery.py, safety_constraint.py, response_synth.py
        api/routes/      # FastAPI routes: health, chat, users, products,
                         #   conversations, memory, persona
        catalog/         # Open Beauty Facts client, ingredient parser, safety index,
                         #   product service, auto_seed, ingredient_interactions
        core/            # database.py (async SQLAlchemy), redis.py, llm.py, rate_limit.py, vector_store.py
        memory/          # constraint_store.py, langmem_config.py, background_extractor.py,
                         #   conflict_detector.py
        models/          # SQLAlchemy: user, product, conversation, message, persona
        persona/         # monitor.py, traits.py, vector_extractor.py (optional, needs torch)
        config.py        # Pydantic Settings (loads .env)
        main.py          # FastAPI app factory + lifespan
        dependencies.py  # DI providers (get_db_session, get_redis, get_settings)
    alembic/             # Async Alembic migrations
    tests/
        unit/            # 38 test files — core logic, models, utilities
        integration/     # 2 test files — agent pipeline, chat API end-to-end
        eval/            # 3 test files — memory, persona, safety evaluation benchmarks
    scripts/             # seed_catalog.py, compute_persona_vectors.py

frontend/
    src/
        api/             # client.ts, chat.ts, users.ts, products.ts
        components/      # chat/, layout/, products/, profile/, persona/
        stores/          # Zustand: chatStore.ts, userStore.ts
        hooks/           # React Query: useChat.ts, useProducts.ts, useUser.ts
        types/           # TypeScript interfaces
    vite.config.ts       # Port 3000, proxy /api → :8080, alias @/ → src/

scripts/                 # demo_scenario.py, generate_test_users.py
infra/                   # postgres/init.sql, nginx/nginx.conf
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (postgres + redis status) |
| POST | `/api/v1/chat` | Chat with agent pipeline |
| POST | `/api/v1/chat/stream` | SSE streaming chat (with timeout + disconnect handling) |
| POST | `/api/v1/users` | Create user |
| GET | `/api/v1/users/{id}` | Get user profile |
| PATCH | `/api/v1/users/{id}` | Update user profile |
| GET | `/api/v1/products/search?q=` | Search products |
| GET | `/api/v1/products/{id}` | Get product |
| GET | `/api/v1/conversations?user_id=` | List conversations |
| GET | `/api/v1/conversations/{id}/messages` | Get messages |
| GET | `/api/v1/users/{id}/memory` | Get user memories |
| DELETE | `/api/v1/users/{id}/memory/{mid}` | Delete memory |
| GET | `/api/v1/users/{id}/memory/constraints` | Get constraints |
| POST | `/api/v1/users/{id}/memory/constraints` | Add constraint |
| GET | `/api/v1/persona/scores` | Get persona scores |
| GET | `/api/v1/persona/history` | Get persona history |
| GET | `/api/v1/persona/alerts` | Get persona alerts |
| GET | `/api/v1/persona/stream` | SSE persona updates |

---

## Database

### Tables (via Alembic)
- **users** — id (UUID), display_name, skin_type, skin_concerns (JSONB), allergies (JSONB), preferences (JSONB)
- **products** — id (UUID), openbf_code (unique), name, brand, categories (JSONB), ingredients (JSONB), ingredients_text, image_url, safety_score
- **conversations** — id (UUID), user_id (FK), langgraph_thread_id
- **messages** — id (UUID), conversation_id (FK), role, content, agent_name, metadata (JSONB)
- **persona_scores** — id (UUID), conversation_id, message_id, 5 float trait columns, timestamp

### Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"   # Generate
alembic upgrade head                                 # Apply
```

### Redis Usage
- Memory storage (namespaced: `memory:{user}:{category}:{id}`)
- Persona score caching (`persona:{conv}:{msg}`, 24h TTL)
- Persona history lists (`persona:history:{conv}`)

---

## Configuration

All config via environment variables, loaded by `app/config.py` (Pydantic Settings):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `""` | API key (empty = demo mode) |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | LLM gateway |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4-20250514` | Model to use |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async DB connection |
| `DATABASE_URL_SYNC` | `postgresql://...` | Sync DB (Alembic) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `ZVEC_COLLECTION_PATH` | `./data/zvec_products` | Path for zvec embedded vector store |
| `ZVEC_SPARSE_ENABLED` | `true` | Enable SPLADE sparse embedder for hybrid search |
| `PERSONA_ENABLED` | `false` | Enable persona monitoring (requires torch) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins |
| `LLM_TIMEOUT_SECONDS` | `60` | Timeout for LLM calls in streaming |
| `RATE_LIMIT_CHAT` | `"20/minute"` | Rate limit for chat endpoints |
| `CORS_METHODS` | `["GET","POST","PATCH","DELETE"]` | Allowed HTTP methods |
| `CORS_HEADERS` | `["Content-Type","X-User-ID"]` | Allowed request headers |
| `DB_STATEMENT_TIMEOUT_MS` | `30000` | PostgreSQL statement timeout |

---

## Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| postgres | pgvector/pgvector:pg16 | 5432 | Main DB with vector support |
| redis | redis:7-alpine | 6379 | Cache, memory, persona scores |
| backend | ./backend (Dockerfile) | 8080 | FastAPI application (zvec runs in-process) |
| frontend | ./frontend (Dockerfile) | 3000 (dev) / 80 (prod) | React SPA |
| nginx | nginx:alpine | 80 | Reverse proxy |

```bash
make infra-up    # Start postgres, redis only (zvec runs in-process)
make infra-down  # Stop everything
docker compose up --build   # Full stack (5 services)
```

---

## Development

### Commands
```bash
make backend-dev     # uvicorn --reload on :8080
make frontend-dev    # vite dev on :3000
make test            # pytest with coverage (all tests)
make test-unit       # unit tests only
make lint            # black --check + isort --check + flake8
make format          # black + isort (auto-fix)
make seed            # Seed product catalog from Open Beauty Facts
make migrate         # alembic upgrade head
```

### Code Quality
- **Formatter:** black (line-length=100)
- **Import sorting:** isort (profile=black)
- **Linter:** flake8 (max-line-length=100, ignores E203/W503)
- **Type checking:** mypy (ignore_missing_imports=true)
- **Security:** bandit
- **Pre-commit hooks:** all of the above + commitizen + trailing whitespace

### Testing
- **Framework:** pytest + pytest-asyncio (asyncio_mode=auto)
- **552 backend tests** across 41 test files (unit, integration, eval)
- **150 frontend tests** across 22 test files (vitest + @testing-library/react)
- **702 total tests**, all passing, ~17s execution time
- **Coverage:** 85% (threshold: 70%)
- **Coverage omissions:** persona/*, vector_store, openbf_client, product_service, prompt_optimizer
- **Mocking pattern:** `conftest.py` patches `get_llm` across all 5 agent modules, provides mock_db_session and mock_redis fixtures
- Tests use `unittest.mock.AsyncMock` for async operations

### Frontend
- **Build:** `tsc && vite build` (TypeScript strict, zero errors)
- **Dev server:** Vite on :3000 with proxy to backend
- **Testing:** vitest + @testing-library/react (22 test files covering all major components, stores, and API layer)
- **State:** Zustand stores (chatStore, userStore)
- **Data fetching:** React Query hooks (useChat, useProducts, useUser)
- **Styling:** Tailwind CSS with custom pink primary palette

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `backend/app/agents/state.py` | AgentState TypedDict — the single source of truth for graph state |
| `backend/app/agents/graph.py` | LangGraph StateGraph wiring — `compile_graph()` accepts checkpointer (AsyncPostgresSaver in prod, MemorySaver fallback) |
| `backend/app/agents/safety_constraint.py` | Dual-gate safety + override detection — the architectural centerpiece |
| `backend/app/core/llm.py` | LLM factory + DemoChatModel — all LLM access goes through `get_llm()` |
| `backend/app/config.py` | Pydantic Settings — all env vars |
| `backend/app/api/routes/chat.py` | Main chat endpoint — loads user, invokes graph, returns response |
| `backend/app/catalog/ingredient_parser.py` | INCI parser + allergen synonym dictionary (10 groups) + REVERSE_ALLERGEN_INDEX |
| `backend/app/core/rate_limit.py` | Rate limiting via slowapi (per-user key extraction) |
| `backend/app/memory/memory_manager.py` | Memory abstraction layer over Redis |
| `frontend/src/stores/chatStore.ts` | Chat state + message sending logic |
| `frontend/src/components/chat/ChatView.tsx` | Main chat UI component |

---

## Known Issues & Gotchas

- **zvec requires Python 3.12** (3.13 not yet supported)
- **Python version:** Must be 3.12+ (pyenv local 3.12.x set via `.python-version`)
- **pyproject.toml:** Requires `[tool.setuptools.packages.find] include = ["app*"]` to avoid flat-layout error with alembic dir
- **structlog:** Use simple config only (no `wrapper_class`/`context_class` — causes KeyError)
- **Demo mode:** When `OPENROUTER_API_KEY` is empty, `DemoChatModel` returns deterministic responses — good for demos but doesn't exercise real LLM behavior
- **Product catalog:** Auto-seeds from fixture on startup; full catalog via `make seed` (requires Postgres running)
- **Persona monitoring:** Optional, disabled by default. Requires `pip install -e ".[persona]"` + ~16GB RAM for Llama 3.1 8B model
- **Frontend bundle:** 720KB (single chunk warning) — could benefit from code splitting

---

## What's Implemented vs Planned

### Implemented (Working)
- Full LangGraph agent pipeline (triage → safety → discovery → response)
- Demo LLM mode (works without API key)
- User CRUD with allergies, skin type, concerns, preferences
- Safety dual-gate with override detection and refusal
- Ingredient parser with 10 allergen synonym groups
- Safety scoring (irritant DB + comedogenic DB)
- Memory manager (Redis-backed, 4 namespaces)
- Memory/constraint API (store, retrieve, delete)
- SSE streaming endpoint
- Complete React frontend (chat, profile, allergy manager, memory viewer, persona dashboard)
- Docker Compose (5 services)
- Alembic async migrations
- CI pipeline (GitHub Actions: lint, security, test)
- 702 tests (552 backend + 150 frontend), 85% coverage
- Demo scripts (scenario + test user generation)
- LangGraph checkpointing via `AsyncPostgresSaver` (auto-creates tables, MemorySaver fallback)
- Full Docker Compose E2E (5 services boot cleanly, backend runs alembic on startup, nginx reverse proxy with SSE support)
- Product discovery with hybrid search (keyword + vector via zvec), allergen filtering, and ingredient interaction checking
- Embedded vector store (zvec) with dense + sparse hybrid search and RRF re-ranking
- Conversation persistence (auto-saves user and assistant messages to DB after each chat)
- Persona monitoring frontend (SSE streaming, historical tracking, drift charts, alerts)
- Memory viewer frontend (real data from backend API, delete support, privacy consent toggle)
- Rate limiting on chat endpoints (slowapi, configurable per-user limits)
- User ownership validation on sensitive endpoints (conversations, memory)
- Override detection with 19 regex patterns and whitespace normalization
- Integration tests (agent pipeline + chat API)

### Partially Implemented (Stubs/Placeholders)
- **Catalog seeding:** Auto-seeds from fixture on startup; full Open Beauty Facts import via `make seed`
- **WebSocket chat:** Removed (SSE is sufficient for this project)

### Not Yet Implemented
- Prompt optimization (prompt_optimizer.py is a placeholder)
- Real persona vector computation (requires torch + model download)
- API authentication (JWT or session-based — endpoints currently rely on rate limiting + user ownership validation only)
- Monitoring/observability (Prometheus metrics, Sentry error tracking, request tracing)

---

## CI/CD

**GitHub Actions** (`.github/workflows/ci.yml`):
1. `code-quality` — black, isort, flake8, mypy
2. `security` — bandit scan
3. `test` — pytest with Postgres + Redis services, coverage upload
4. `summary` — aggregated pass/fail

**Pre-commit hooks:** isort, black, flake8, commitizen, bandit, trailing whitespace
