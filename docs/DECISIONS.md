# Architectural Decision Records

## ADR-001: Complete Rewrite vs Incremental Migration

**Decision:** Complete rewrite.

**Context:** The Phase 1 codebase used custom `BaseAgent` + direct Anthropic API for generic shopping. The target uses LangGraph state machine + OpenRouter for beauty/skincare.

**Rationale:** Zero code reuse possible between the architectures. Attempting incremental migration would be slower and produce worse code than a clean start. Only infrastructure configs (CI, pre-commit, .gitignore) carry over.

## ADR-002: OpenRouter as LLM Gateway

**Decision:** All LLM calls go through OpenRouter.

**Rationale:**
- Provider-agnostic — can switch between Claude, GPT-4, Llama, etc. without code changes
- Single API key, single billing
- Makes the project more portable and demonstrable

## ADR-003: Raw Transformers for Persona Monitoring

**Decision:** Load Llama 3.1 8B directly via HuggingFace transformers + PyTorch, not through Ollama.

**Rationale:** We need access to intermediate layer hidden state activations. Ollama only exposes final outputs. Raw transformers give us full control over the forward pass and access to all hidden states.

**Trade-offs:**
- Requires ~16GB RAM or 6GB VRAM
- Model download is ~16GB
- Made optional via `PERSONA_ENABLED` config flag
- Mock scorer provides dev/CI coverage without ML dependencies

## ADR-004: Dual-Gate Safety Architecture

**Decision:** Two-stage safety filtering (rule-based + LLM).

**Rationale:**
- Rule-based gate is fast, deterministic, and catches known allergens/synonyms
- LLM post-check catches edge cases where ingredient names differ
- Belt-and-suspenders approach for safety-critical functionality
- Sycophancy resistance is explicit — system refuses override requests for hard constraints

## ADR-005: LangMem SDK for Long-Term Memory

**Decision:** Use LangMem SDK with `AsyncPostgresStore` for long-term memory (replaced earlier Redis-only approach).

**Rationale:**
- Semantic search over memories via vector embeddings
- Structured namespaces (user_facts, constraints, episodes)
- Conflict detection for contradictory facts
- Background extraction via LLM after each conversation turn
- PostgreSQL persistence with Redis for hot-path caching (persona scores, SSE)

## ADR-006: Monorepo Structure

**Decision:** Single repo with `backend/` and `frontend/` directories.

**Rationale:**
- Simpler CI/CD — one workflow, one PR for full-stack changes
- Docker Compose at root orchestrates everything
- Appropriate for a portfolio project of this size

## ADR-007: Mock-First Persona Scoring

**Decision:** Default to `MockPersonaScorer` (rule-based regex) with opt-in real model scoring.

**Rationale:**
- Enables persona monitoring in all environments (dev, CI, production)
- No ML dependencies required for the default path
- Real scorer only needed for production-quality monitoring
- Mock scorer detects common patterns (override language, sales pressure, etc.) via regex
- Config: `PERSONA_SCORER=mock` (default) or `PERSONA_SCORER=real`

## ADR-008: Ingredient Interaction Database

**Decision:** Static database of known ingredient incompatibilities, checked at product enrichment time.

**Rationale:**
- Dermatological consensus on which actives conflict (retinoid+AHA, etc.)
- Zero-latency check (no LLM call needed)
- Surfaced as warnings in response synthesis, not hard blocks
- Severity levels (high/medium/low) let the response synthesizer calibrate advice
