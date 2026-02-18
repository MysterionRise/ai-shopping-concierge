"""Memory conflict detection — detects when new facts contradict existing ones.

When a contradiction is detected, a pending confirmation is created. The triage
router checks for pending confirmations at the start of each conversation and
naturally asks the user about the change.
"""

from datetime import UTC, datetime

import structlog
from langgraph.store.base import BaseStore

from app.memory.langmem_config import pending_confirmations_ns, user_facts_ns

logger = structlog.get_logger()

# Fact categories where contradictions are meaningful
CONTRADICTION_CATEGORIES = {"skin_type", "age"}

MAX_IGNORED_ATTEMPTS = 3


async def check_and_store_conflict(
    store: BaseStore,
    user_id: str,
    new_fact_key: str,
    new_value: dict,
) -> bool:
    """Check if a new fact contradicts an existing one. If so, store a pending confirmation.

    Returns True if a conflict was detected and stored.
    """
    category = new_value.get("category", "")
    if category not in CONTRADICTION_CATEGORIES:
        return False

    # Search existing facts in the same category
    try:
        existing_items = await store.asearch(user_facts_ns(user_id), limit=50)
    except Exception as e:
        logger.warning("Failed to search for conflicts", error=str(e))
        return False

    for item in existing_items:
        existing_category = item.value.get("category", "")
        existing_value = item.value.get("value", "")
        new_val = new_value.get("value", "")

        if existing_category == category and existing_value != new_val and item.key != new_fact_key:
            # Contradiction found
            conflict_key = f"conflict_{category}_{item.key}"
            await store.aput(
                pending_confirmations_ns(user_id),
                conflict_key,
                {
                    "old_key": item.key,
                    "old_value": existing_value,
                    "new_value": new_val,
                    "category": category,
                    "detected_at": datetime.now(UTC).isoformat(),
                    "attempts": 0,
                    "source_message": new_value.get("content", ""),
                },
            )
            logger.info(
                "Memory conflict detected",
                user_id=user_id,
                category=category,
                old=existing_value,
                new=new_val,
            )
            return True

    return False


async def load_pending_confirmations(store: BaseStore, user_id: str) -> list[dict]:
    """Load all pending confirmations for a user.

    Returns a list of confirmation dicts with their keys for tracking.
    """
    try:
        items = await store.asearch(pending_confirmations_ns(user_id), limit=20)
        return [{"key": item.key, **item.value} for item in items]
    except Exception as e:
        logger.warning("Failed to load pending confirmations", error=str(e))
        return []


async def resolve_conflict(
    store: BaseStore,
    user_id: str,
    conflict_key: str,
    resolution: str,
    conflict_data: dict,
) -> None:
    """Resolve a pending conflict.

    Args:
        resolution: "accept_new", "keep_both", or "ignore"
    """
    category = conflict_data.get("category", "")
    old_key = conflict_data.get("old_key", "")

    if resolution == "accept_new":
        # Delete the old fact — the new one is already stored
        if old_key:
            await store.adelete(user_facts_ns(user_id), old_key)
        await store.adelete(pending_confirmations_ns(user_id), conflict_key)
        logger.info("Conflict resolved: accepted new value", category=category)

    elif resolution == "keep_both":
        # Update both facts with temporal qualifiers
        old_val = conflict_data.get("old_value", "")
        if old_key:
            await store.aput(
                user_facts_ns(user_id),
                old_key,
                {
                    "category": category,
                    "value": f"{old_val} (sometimes)",
                    "content": f"{category}: {old_val} (varies)",
                },
            )
        await store.adelete(pending_confirmations_ns(user_id), conflict_key)
        logger.info("Conflict resolved: keeping both with qualifiers", category=category)

    elif resolution == "ignore":
        # Increment attempts, auto-accept after max
        attempts = conflict_data.get("attempts", 0) + 1
        if attempts >= MAX_IGNORED_ATTEMPTS:
            # Auto-accept newer value
            if old_key:
                await store.adelete(user_facts_ns(user_id), old_key)
            await store.adelete(pending_confirmations_ns(user_id), conflict_key)
            logger.info(
                "Conflict auto-resolved after max attempts",
                category=category,
                attempts=attempts,
            )
        else:
            # Update attempts counter
            updated = {**conflict_data, "attempts": attempts}
            updated.pop("key", None)
            await store.aput(pending_confirmations_ns(user_id), conflict_key, updated)
            logger.debug("Conflict ignored, attempts incremented", attempts=attempts)


def format_conflict_prompt(confirmations: list[dict]) -> str:
    """Format pending confirmations as context for the system prompt."""
    if not confirmations:
        return ""

    lines = []
    for conf in confirmations:
        old = conf.get("old_value", "unknown")
        new = conf.get("new_value", "unknown")
        cat = conf.get("category", "fact")
        lines.append(
            f"The user previously mentioned having {old} {cat}, "
            f"but recently indicated {new} {cat}. "
            f"Naturally ask if their {cat} has changed or if it varies seasonally."
        )

    return "PENDING CONFIRMATIONS — address these naturally in your response:\n" + "\n".join(
        f"- {line}" for line in lines
    )
