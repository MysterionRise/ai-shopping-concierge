"""LangMem configuration — AsyncPostgresStore-backed long-term memory.

Namespace layout:
- ("user_facts", "{user_id}")       — skin type, age, general facts
- ("constraints", "{user_id}")      — hard constraints (allergies, sensitivities)
- ("episodes", "{user_id}")         — conversation episode summaries
- ("agent_instructions",)           — shared agent tuning (future)
- ("pending_confirmations", "{user_id}") — conflict resolution queue
"""

import structlog
from langgraph.store.postgres import AsyncPostgresStore

from app.config import settings

logger = structlog.get_logger()

# Namespace constants (use .format(user_id=...) at runtime for template vars)
USER_FACTS_NS = ("user_facts",)
CONSTRAINTS_NS = ("constraints",)
EPISODES_NS = ("episodes",)
AGENT_INSTRUCTIONS_NS = ("agent_instructions",)
PENDING_CONFIRMATIONS_NS = ("pending_confirmations",)


# Legacy compatibility — used by memory_manager.py (Redis-backed, will be removed in 2C.5)
MEMORY_CATEGORIES = ["semantic", "episodic", "constraints", "preferences"]


def get_memory_namespace(user_id: str, category: str) -> tuple[str, ...]:
    return ("user", user_id, category)


def user_facts_ns(user_id: str) -> tuple[str, str]:
    return ("user_facts", user_id)


def constraints_ns(user_id: str) -> tuple[str, str]:
    return ("constraints", user_id)


def episodes_ns(user_id: str) -> tuple[str, str]:
    return ("episodes", user_id)


def pending_confirmations_ns(user_id: str) -> tuple[str, str]:
    return ("pending_confirmations", user_id)


def _build_index_config() -> dict | None:
    """Build vector index config if an embedding API key is available."""
    if settings.openai_api_key:
        return {
            "dims": 1536,
            "embed": "openai:text-embedding-3-small",
        }
    logger.info("No OPENAI_API_KEY set — LangMem store will operate without vector search")
    return None


def get_store_context():
    """Return an async context manager for the AsyncPostgresStore.

    Usage::

        async with get_store_context() as store:
            await store.setup()
            # ... use store ...
    """
    index = _build_index_config()
    return AsyncPostgresStore.from_conn_string(
        settings.checkpoint_db_url,
        index=index,
    )
