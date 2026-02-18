"""Background memory extraction — runs after conversations end.

Uses LangMem's create_memory_store_manager + ReflectionExecutor to extract
user facts, preferences, and implicit constraints from conversation history.
"""

import asyncio
from typing import Any

import structlog
from langgraph.store.base import BaseStore

from app.core.llm import get_llm

logger = structlog.get_logger()

BEAUTY_EXTRACTION_INSTRUCTIONS = """Extract noteworthy facts from this beauty consultation.

ALWAYS extract:
- Skin type (oily, dry, combination, sensitive, normal)
- Skin concerns (acne, aging, hyperpigmentation, rosacea, etc.)
- Ingredient allergies or sensitivities (mark as HARD CONSTRAINT)
- Medical skin conditions mentioned
- Current routine products the user mentions
- Products the user has used before (with sentiment: liked, disliked, neutral)

EXTRACT IF MENTIONED:
- Age or age range
- Brand preferences or aversions
- Budget range or price sensitivity
- Texture/format preferences (gel vs cream, fragrance-free, etc.)
- Climate or seasonal skincare variations

DO NOT EXTRACT:
- One-time search queries ("show me red lipsticks" does NOT mean "prefers red lipstick")
- Transient shopping context ("buying a gift for my sister")
- Conversational filler ("thanks", "that sounds good")
- Product recommendations the agent made (store user facts, not agent outputs)
- Ingredient safety information the agent provided (system knowledge, not user knowledge)

When updating existing memories:
- If a user contradicts a previous fact, UPDATE the existing memory (not duplicate)
- If a seasonal change is implied, ADD a temporal qualifier ("dry skin in winter")
- If certainty is low, set confidence to 'low' and include the source quote
"""

# Track processed conversations to prevent duplicate extraction
_processed_conversations: set[str] = set()
_pending_tasks: dict[str, asyncio.Task] = {}


def _get_extractor(store: BaseStore):
    """Create a memory store manager and reflection executor.

    Returns None if LLM is not available (demo mode).
    """
    try:
        from langmem import ReflectionExecutor, create_memory_store_manager

        llm = get_llm(temperature=0)
        # Check if this is the demo model (no real extraction possible)
        if type(llm).__name__ == "DemoChatModel":
            logger.info("Demo mode — background extraction disabled")
            return None

        memory_manager = create_memory_store_manager(
            llm,
            namespace=("user_facts", "{user_id}"),
            instructions=BEAUTY_EXTRACTION_INSTRUCTIONS,
            enable_inserts=True,
            enable_deletes=False,
            store=store,
        )

        executor = ReflectionExecutor(memory_manager, store=store)
        return executor
    except Exception as e:
        logger.warning("Failed to create background extractor", error=str(e))
        return None


def schedule_extraction(
    conversation_id: str,
    user_id: str,
    messages: list[dict[str, Any]],
    store: BaseStore | None,
    delay_seconds: int = 30,
) -> None:
    """Schedule background memory extraction after a conversation ends.

    Waits delay_seconds before processing (in case user reconnects).
    Idempotent — skips already-processed conversations.
    """
    if store is None:
        return

    if conversation_id in _processed_conversations:
        logger.debug("Conversation already processed", conversation_id=conversation_id)
        return

    # Cancel any pending task for this conversation (user sent another message)
    if conversation_id in _pending_tasks:
        _pending_tasks[conversation_id].cancel()

    async def _delayed_extract():
        await asyncio.sleep(delay_seconds)

        if conversation_id in _processed_conversations:
            return

        try:
            executor = _get_extractor(store)
            if executor is None:
                return

            config = {
                "configurable": {
                    "thread_id": conversation_id,
                    "user_id": user_id,
                }
            }
            payload = {"messages": messages}

            executor.submit(payload, config=config, after_seconds=0)
            _processed_conversations.add(conversation_id)
            logger.info(
                "Background extraction submitted",
                conversation_id=conversation_id,
                user_id=user_id,
                message_count=len(messages),
            )
        except Exception as e:
            logger.warning(
                "Background extraction failed",
                error=str(e),
                conversation_id=conversation_id,
            )
        finally:
            _pending_tasks.pop(conversation_id, None)

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_delayed_extract())
        _pending_tasks[conversation_id] = task
    except RuntimeError:
        logger.debug("No running event loop for background extraction")


def reset_processed():
    """Reset processed conversations set (for testing)."""
    _processed_conversations.clear()
    _pending_tasks.clear()
