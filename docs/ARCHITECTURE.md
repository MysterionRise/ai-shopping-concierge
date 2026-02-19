# Architecture

## System Overview

The AI Beauty Shopping Concierge is a multi-agent system built on LangGraph, with a FastAPI backend, React frontend, and multiple data stores.

## Agent Architecture

The core of the system is a LangGraph `StateGraph` with the following nodes:

### 1. Triage Router
- **Purpose:** Classify user intent and load memory context
- **Intents:** `product_search`, `ingredient_check`, `routine_advice`, `memory_query`, `general_chat`
- **Method:** LLM structured output classification
- **Memory:** Loads user constraints and facts from LangMem store
- **Fact detection:** Regex-based extraction of allergies, skin type, preferences from user messages
- **Persona reinforcement:** Checks Redis for active safety reinforcement flags
- **Fallback:** Defaults to `general_chat` on error

### 2. Product Discovery
- **Purpose:** Find relevant products from the catalog
- **Method:** LLM extracts search intent, then hybrid search (Postgres ILIKE + ChromaDB vectors)
- **Allergen pre-filtering:** Removes products matching user's hard constraints
- **Ingredient interactions:** Flags known incompatible ingredient pairs within products
- **Ranking:** Safety score, ingredient relevance, user preference match

### 3. Safety Post-Validation
- **Purpose:** LLM-based second check on discovered products
- **Gate 1 (rule-based):** Cross-references ingredients against user allergies with synonym expansion (10 allergen groups, 45+ synonyms)
- **Gate 2 (LLM):** Catches ingredient synonyms that rule-based matching missed
- **Sycophancy resistance:** Refuses to override safety even when user pushes

### 4. Response Synthesizer
- **Purpose:** Generate natural language response from agent state
- **Templates:** Different formats for recommendations, safety rejections, general chat
- **Memory-aware:** Incorporates previous conversation context and memory notifications
- **Interaction warnings:** Surfaces ingredient interaction warnings when relevant

## State Schema

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    conversation_id: str
    user_profile: dict
    hard_constraints: list[str]          # Allergies (absolute, never override)
    soft_preferences: list[str]          # Preferences (flexible)
    current_intent: str
    product_results: list[dict]
    safety_check_passed: bool
    safety_violations: list[dict]
    memory_context: list[str]            # Retrieved memories for context
    active_constraints: list[dict]       # Loaded from LangMem store
    memory_notifications: list[str]      # New memories discovered this turn
    memory_enabled: bool                 # User consent toggle
    persona_scores: dict[str, float]
    error: str | None
```

## Safety Gate Pattern

The dual-gate safety architecture is the system's centerpiece:

1. **Rule-based gate:** Deterministic, fast. Cross-references every product ingredient against user's hard constraints using a synonym dictionary (10 allergen groups, 45+ synonyms).
2. **LLM post-check:** Catches edge cases where ingredient names differ from the synonym list.
3. **Override resistance:** If the user says "just show it anyway," the system refuses for hard constraints (allergies). Detected via pattern matching in the chat endpoint.

## Ingredient Interaction Checking

Products are checked for known ingredient incompatibilities:

| Interaction | Severity | Example |
|------------|----------|---------|
| Retinoid + AHA | High | Retinol + glycolic acid |
| Retinoid + BHA | High | Tretinoin + salicylic acid |
| Retinoid + Benzoyl Peroxide | High | Retinol + benzoyl peroxide |
| Vitamin C + Retinoid | Medium | Ascorbic acid + retinol |
| AHA + BHA | Medium | Glycolic acid + salicylic acid |
| Vitamin C + Niacinamide | Low | Generally safe in modern formulations |

## Memory Architecture

Long-term memory via LangMem SDK backed by PostgreSQL (`AsyncPostgresStore`):

1. **User facts:** General facts about the user (skin type, preferences, age)
2. **Constraints:** Allergies and sensitivities (severity: absolute/high/moderate)
3. **Episodes:** Conversation summaries (via background extraction)

Key features:
- **Hot-path storage:** Regex-based fact detection stores immediately during triage
- **Background extraction:** Async LLM-based extraction runs after response delivery
- **Conflict detection:** Detects contradictions (e.g., "dry skin" then "oily skin"), prompts user to confirm
- **User consent:** `memory_enabled` toggle per user, respected throughout pipeline

## Persona Monitoring

Shadow scoring system that runs asynchronously after each response:

1. **Mock scorer (default):** Rule-based pattern detection for dev/CI, no ML dependencies
2. **Real scorer (optional):** Raw transformers (Llama 3.1 8B) hidden state activation analysis

Five monitored traits: sycophancy, hallucination, over-confidence, safety bypass, sales pressure.

Intervention system:
- **Disclaimer:** Appended via SSE when hallucination or over-confidence exceeds threshold
- **Reinforce:** Sets Redis flag to prepend safety reinforcement to next turn's system prompt
- **Log:** Default action, records the score for analysis

Scores are stored in both Redis (fast SSE cache) and PostgreSQL (long-term storage).

## Checkpointing

LangGraph conversation state is persisted via `AsyncPostgresSaver` (auto-creates tables).
Falls back to in-memory `MemorySaver` if Postgres connection fails.
