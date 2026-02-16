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

## ADR-004: Dual-Gate Safety Architecture

**Decision:** Two-stage safety filtering (rule-based + LLM).

**Rationale:**
- Rule-based gate is fast, deterministic, and catches known allergens/synonyms
- LLM post-check catches edge cases where ingredient names differ
- Belt-and-suspenders approach for safety-critical functionality
- Sycophancy resistance is explicit — system refuses override requests for hard constraints

## ADR-005: Redis for Memory + Persona Scores

**Decision:** Use Redis as the primary fast-write store for memories and persona scores, with periodic flush to Postgres.

**Rationale:**
- Persona scoring is fire-and-forget — can't block the response pipeline
- Memory lookups need to be fast (called at start of every request)
- Redis gives sub-millisecond reads
- Postgres is the source of truth; Redis is the hot cache

## ADR-006: Monorepo Structure

**Decision:** Single repo with `backend/` and `frontend/` directories.

**Rationale:**
- Simpler CI/CD — one workflow, one PR for full-stack changes
- Docker Compose at root orchestrates everything
- Appropriate for a portfolio project of this size
