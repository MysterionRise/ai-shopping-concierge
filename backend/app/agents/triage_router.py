import re
import uuid

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.core.llm import get_llm
from app.memory.conflict_detector import (
    check_and_store_conflict,
    format_conflict_prompt,
    load_pending_confirmations,
    resolve_conflict,
)
from app.memory.langmem_config import constraints_ns, user_facts_ns

logger = structlog.get_logger()

TRIAGE_SYSTEM_PROMPT = """You are a triage router for an AI beauty and skincare concierge.
Classify the user's message into exactly one intent.

Intents:
- product_search: User wants product recommendations or is looking for specific products
- ingredient_check: User asks about specific ingredients, safety, or compatibility
- routine_advice: User wants skincare routine help, ordering, or regimen advice
- general_chat: Greetings, thanks, off-topic, or general conversation

Respond with ONLY the intent name, nothing else."""


class TriageResult(BaseModel):
    intent: str = Field(
        description="The classified intent",
        pattern="^(product_search|ingredient_check|routine_advice|general_chat)$",
    )


VALID_INTENTS = {"product_search", "ingredient_check", "routine_advice", "general_chat"}

# Patterns for detecting user self-statements
FACT_PATTERNS = [
    (r"\bi(?:'m| am) (\d+)\b", "age"),
    (r"\bmy skin (?:is|type is) (\w+)", "skin_type"),
    (r"\bi have (\w+) skin\b", "skin_type"),
    (r"\bi(?:'m| am) allergic to (.+?)(?:\.|,|$)", "allergy"),
    (r"\bi have (?:an? )?allergy to (.+?)(?:\.|,|$)", "allergy"),
    (r"\bi(?:'m| am) sensitive to (.+?)(?:\.|,|$)", "sensitivity"),
    (r"\bi prefer (.+?)(?:\.|,|$)", "preference"),
    (r"\bi like (.+?)(?:\.|,|!|$)", "preference"),
    (r"\bi don'?t like (.+?)(?:\.|,|!|$)", "aversion"),
]


def detect_user_facts(text: str) -> list[dict]:
    """Extract explicit self-statements from user text."""
    facts = []
    lower = text.lower()
    for pattern, category in FACT_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            value = match.group(1).strip()
            facts.append({"category": category, "value": value, "source_text": text})
    return facts


async def _load_memory_context(store: BaseStore, user_id: str, user_text: str) -> dict:
    """Load constraints, relevant facts, and pending confirmations from the LangMem store."""
    active_constraints: list[dict] = []
    memory_context: list[str] = []
    conflict_prompt = ""

    try:
        # Always load ALL constraints for this user
        constraint_items = await store.asearch(constraints_ns(user_id), limit=50)
        active_constraints = [item.value for item in constraint_items]

        # Search for relevant facts based on the user's message
        fact_items = await store.asearch(user_facts_ns(user_id), query=user_text, limit=10)
        memory_context = [item.value.get("content", str(item.value)) for item in fact_items]

        # Check for pending conflict confirmations
        confirmations = await load_pending_confirmations(store, user_id)
        if confirmations:
            conflict_prompt = format_conflict_prompt(confirmations)
            # Increment ignore attempts for these confirmations
            for conf in confirmations:
                await resolve_conflict(store, user_id, conf["key"], "ignore", conf)
    except Exception as e:
        logger.warning("Failed to load memory context", error=str(e), user_id=user_id)

    result = {"active_constraints": active_constraints, "memory_context": memory_context}
    if conflict_prompt:
        result["memory_context"] = memory_context + [conflict_prompt]
    return result


async def _store_detected_facts(store: BaseStore, user_id: str, facts: list[dict]) -> list[str]:
    """Store detected user facts and return notification messages."""
    notifications: list[str] = []
    for fact in facts:
        category = fact["category"]
        value = fact["value"]

        if category == "allergy":
            key = f"allergy_{value.replace(' ', '_')}"
            await store.aput(
                constraints_ns(user_id),
                key,
                {
                    "ingredient": value,
                    "severity": "absolute",
                    "source": "user_stated",
                    "content": f"Allergic to {value}",
                },
            )
            notifications.append(
                f"I've noted your {value} allergy — "
                f"I'll filter out products containing {value} going forward."
            )
        elif category == "sensitivity":
            key = f"sensitivity_{value.replace(' ', '_')}"
            await store.aput(
                constraints_ns(user_id),
                key,
                {
                    "ingredient": value,
                    "severity": "high",
                    "source": "user_stated",
                    "content": f"Sensitive to {value}",
                },
            )
            notifications.append(
                f"I've noted your sensitivity to {value} — "
                f"I'll avoid recommending products with {value}."
            )
        else:
            key = f"{category}_{uuid.uuid4().hex[:8]}"
            fact_value = {"category": category, "value": value, "content": f"{category}: {value}"}
            # Check for contradictions before storing
            await check_and_store_conflict(store, user_id, key, fact_value)
            await store.aput(user_facts_ns(user_id), key, fact_value)
            if category == "skin_type":
                notifications.append(f"I've noted that you have {value} skin.")
            elif category == "preference":
                notifications.append(f"I've noted your preference for {value}.")
            elif category == "aversion":
                notifications.append(f"I've noted that you prefer to avoid {value}.")

    return notifications


async def triage_router_node(
    state: AgentState, config: RunnableConfig = None, *, store: BaseStore = None
) -> dict:
    logger.info("Triage router invoked", user_id=state.get("user_id"))

    messages = state.get("messages", [])
    if not messages:
        return {"current_intent": "general_chat"}

    last_message = messages[-1]
    raw_content = last_message.content if hasattr(last_message, "content") else str(last_message)
    user_text = raw_content if isinstance(raw_content, str) else str(raw_content)
    user_id = state.get("user_id", "")

    # Load memory context from store (constraints + relevant facts)
    memory_update = {}
    if store and user_id:
        memory_update = await _load_memory_context(store, user_id, user_text)
        # Merge store constraints into hard_constraints for safety agent
        constraint_ingredients = [
            c.get("ingredient", "")
            for c in memory_update.get("active_constraints", [])
            if c.get("ingredient")
        ]
        existing = state.get("hard_constraints", [])
        merged = list(set(existing + constraint_ingredients))
        memory_update["hard_constraints"] = merged

    # Classify intent
    llm = get_llm(temperature=0)

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
                HumanMessage(content=user_text),
            ]
        )
        content = response.content if isinstance(response.content, str) else str(response.content)
        intent = content.strip().lower()

        if intent not in VALID_INTENTS:
            logger.warning("Unknown intent from LLM, defaulting to general_chat", raw_intent=intent)
            intent = "general_chat"

    except Exception as e:
        logger.error("Triage classification failed", error=str(e))
        intent = "general_chat"

    logger.info("Intent classified", intent=intent)

    # Detect and store user facts / constraints
    notifications: list[str] = []
    if store and user_id:
        detected = detect_user_facts(user_text)
        if detected:
            notifications = await _store_detected_facts(store, user_id, detected)
            logger.info("User facts detected and stored", count=len(detected))

    result = {
        "current_intent": intent,
        "memory_context": memory_update.get("memory_context", state.get("memory_context", [])),
        "active_constraints": memory_update.get("active_constraints", []),
        "memory_notifications": notifications,
    }
    if "hard_constraints" in memory_update:
        result["hard_constraints"] = memory_update["hard_constraints"]

    return result
