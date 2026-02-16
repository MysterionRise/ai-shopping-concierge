# Architecture

## System Overview

The AI Beauty Shopping Concierge is a multi-agent system built on LangGraph, with a FastAPI backend, React frontend, and multiple data stores.

## Agent Architecture

The core of the system is a LangGraph `StateGraph` with the following nodes:

### 1. Triage Router
- **Purpose:** Classify user intent from the message
- **Intents:** `product_search`, `ingredient_check`, `routine_advice`, `general_chat`
- **Method:** LLM structured output classification
- **Fallback:** Defaults to `general_chat` on error

### 2. Safety Pre-Filter
- **Purpose:** Apply hard constraints before product discovery
- **Gate 1:** Rule-based ingredient matching against user allergies
- **Includes:** Synonym expansion (e.g., "paraben" catches "methylparaben")

### 3. Product Discovery
- **Purpose:** Find relevant products from the catalog
- **Method:** LLM extracts search intent, then semantic search via ChromaDB + SQL filtering
- **Ranking:** Safety score, ingredient relevance, user preference match

### 4. Safety Post-Validation
- **Purpose:** LLM-based second check on discovered products
- **Catches:** Ingredient synonyms that rule-based matching missed
- **Sycophancy resistance:** Refuses to override safety even when user pushes

### 5. Response Synthesizer
- **Purpose:** Generate natural language response from agent state
- **Templates:** Different formats for recommendations, safety rejections, general chat
- **Memory-aware:** Incorporates previous conversation context

## State Schema

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    conversation_id: str
    user_profile: dict
    hard_constraints: list[str]      # Allergies — never override
    soft_preferences: list[str]      # Preferences — can be flexible
    current_intent: str
    product_results: list[dict]
    safety_check_passed: bool
    safety_violations: list[dict]
    memory_context: list[str]
    persona_scores: dict[str, float]
    error: str | None
```

## Safety Gate Pattern

The dual-gate safety architecture is the system's centerpiece:

1. **Rule-based gate:** Deterministic, fast. Cross-references every product ingredient against user's hard constraints using a synonym dictionary.
2. **LLM post-check:** Catches edge cases where ingredient names differ from the synonym list.
3. **Override resistance:** If the user says "just show it anyway," the system refuses for hard constraints (allergies).

## Memory Architecture

Three-tier memory system:
1. **Semantic memories:** General facts about the user (skin type, preferences)
2. **Episodic memories:** Conversation summaries
3. **Constraint memories:** Allergies and sensitivities learned from conversation

Stored in Redis for fast access, with periodic flush to PostgreSQL for persistence.

## Persona Monitoring

Uses raw transformers (not through an API) to extract hidden state activations from Llama 3.1 8B:

1. Pre-compute "persona vectors" by contrasting desirable vs undesirable behavior prompts
2. After each response, run the response through the model and extract activations
3. Project activations onto persona vectors to get trait scores
4. Alert if any trait exceeds threshold

Monitored traits: sycophancy, hallucination, over-confidence, safety bypass, sales pressure.

This runs asynchronously (fire-and-forget) — never blocks the response pipeline.
