# Changelog

## v1.0.0 — Phase 2E: Polish, Evaluation & Documentation

### Added
- **Ingredient interaction database** — 10 known incompatible ingredient pairs (retinoid+AHA, vitamin C+benzoyl peroxide, etc.) with severity levels
- **Ingredient interaction warnings** surfaced in product results and response synthesis
- **Integration tests** — full agent pipeline, chat API, safety gate integration
- **Evaluation suite** — safety compliance, memory detection, persona scoring accuracy
- **Enhanced demo scenario** — 10-step script exercising all features (safety, memory, persona)
- Makefile targets: `make demo`, `make demo-users`, `make test-integration`, `make test-eval`

### Changed
- Updated all documentation (ARCHITECTURE.md, API.md, DECISIONS.md, PERSONA_VECTORS.md)
- Enhanced demo user profiles with budget preferences

## v0.4.0 — Phase 2D: Persona Vectors Activation

### Added
- **MockPersonaScorer** — rule-based pattern detection for 5 traits (no ML dependencies)
- **Shadow scoring service** — fire-and-forget persona evaluation after each response
- **Persona dashboard wiring** — real-time SSE data replaces mock data
- **Threshold interventions** — disclaimer (SSE), reinforce (Redis flag), log
- **PersonaSidebar** — compact toggle-able panel in chat view
- **Trait contrast pairs** — 10+ pairs per trait for vector computation
- `make compute-persona-vectors` and `make compute-persona-vectors-mock` targets
- 45 new tests (persona vectors, scoring, interventions)

### Changed
- `PERSONA_ENABLED` now defaults to `true` (mock scorer has no ML dependencies)
- PersonaMonitor accepts scorer interface instead of building extractor internally
- DriftChart uses snake_case keys matching backend

## v0.3.0 — Phase 2C: LangMem Memory

### Added
- **LangMem SDK integration** — `AsyncPostgresStore` for long-term memory
- **Hot-path memory tools** — real-time constraint and fact storage
- **Background memory extraction** — async LLM-based extraction via `ReflectionExecutor`
- **Memory conflict detection** — contradictions prompt user confirmation
- **Redis-to-LangMem migration** script
- **Memory consent toggle** — per-user `memory_enabled` flag
- **Transparency notifications** — "I've noted your allergy" confirmations
- **memory_query intent** — "What do you remember about me?"

## v0.2.0 — Phase 2B: Catalog & Search

### Added
- **Catalog seeding** from Open Beauty Facts (10 categories, ~1000 products)
- **Hybrid search** — Postgres ILIKE + ChromaDB vector similarity
- **Frontend product cards** — safety badges, ingredient lists, fit reasons
- Safety scoring with irritant DB (16 entries) and comedogenic DB (12 entries)
- Data completeness scoring for catalog entries

## v0.1.1 — Phase 2A: Infrastructure Fixes

### Added
- **AsyncPostgresSaver** — persistent LangGraph checkpointing
- **Docker Compose E2E** — all 6 services boot cleanly
- **SSE streaming robustness** — timeout handling, disconnect detection, error display

## v0.1.0 — Phase 1: Foundation

### Added
- LangGraph StateGraph with 5 agent nodes
- FastAPI backend with async SQLAlchemy
- React 18 frontend with TypeScript and Tailwind
- Dual-gate safety architecture (rule-based + LLM)
- Ingredient parser with 10 allergen synonym groups
- Override detection and refusal
- Demo LLM mode (works without API key)
- PostgreSQL, Redis, ChromaDB infrastructure
- 76 unit tests, CI/CD pipeline
