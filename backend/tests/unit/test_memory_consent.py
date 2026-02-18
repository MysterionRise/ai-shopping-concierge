"""Tests for memory consent (memory_enabled flag) and memory_query intent."""

from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.memory import InMemoryStore

from app.agents.response_synth import _load_all_memories, response_synth_node
from app.agents.triage_router import triage_router_node
from app.memory.background_extractor import schedule_extraction
from app.memory.langmem_config import constraints_ns, user_facts_ns

# --- memory_enabled=False skips memory operations ---


async def test_triage_skips_memory_when_disabled(mock_llm):
    """When memory_enabled=False, triage should not load or store memory."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

    store = InMemoryStore()
    # Pre-populate store with data that should NOT be loaded
    await store.aput(
        constraints_ns("user-1"),
        "allergy_fragrance",
        {"ingredient": "fragrance", "severity": "absolute", "content": "Allergic to fragrance"},
    )

    state = {
        "messages": [HumanMessage(content="I'm allergic to sulfates")],
        "user_id": "user-1",
        "hard_constraints": [],
        "memory_context": [],
        "memory_enabled": False,
    }

    result = await triage_router_node(state, store=store)

    # Existing constraints should NOT be loaded
    assert result.get("active_constraints", []) == []
    # New allergy should NOT be stored
    assert result.get("memory_notifications", []) == []
    # But intent classification should still work
    assert result["current_intent"] == "general_chat"

    # Verify nothing new was stored
    items = await store.asearch(constraints_ns("user-1"))
    assert len(items) == 1  # Only the pre-existing one


async def test_triage_loads_memory_when_enabled(mock_llm):
    """When memory_enabled=True (default), triage loads and stores memory normally."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

    store = InMemoryStore()
    await store.aput(
        constraints_ns("user-1"),
        "allergy_fragrance",
        {"ingredient": "fragrance", "severity": "absolute", "content": "Allergic to fragrance"},
    )

    state = {
        "messages": [HumanMessage(content="I'm allergic to sulfates")],
        "user_id": "user-1",
        "hard_constraints": [],
        "memory_context": [],
        "memory_enabled": True,
    }

    result = await triage_router_node(state, store=store)

    # Existing constraints SHOULD be loaded
    assert len(result.get("active_constraints", [])) >= 1
    # New allergy SHOULD be stored and notified
    assert any("sulfates" in n for n in result.get("memory_notifications", []))


async def test_triage_defaults_memory_enabled_true(mock_llm):
    """When memory_enabled is not in state, defaults to True."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

    store = InMemoryStore()
    state = {
        "messages": [HumanMessage(content="I have oily skin")],
        "user_id": "user-1",
        "hard_constraints": [],
        "memory_context": [],
        # memory_enabled NOT set
    }

    result = await triage_router_node(state, store=store)

    # Should still store facts (default behavior)
    assert any("oily skin" in n for n in result.get("memory_notifications", []))


# --- background_extractor respects memory_enabled ---


def test_schedule_extraction_skips_when_disabled():
    """schedule_extraction returns immediately when memory_enabled=False."""
    store = InMemoryStore()
    # This should not raise or schedule anything
    schedule_extraction(
        "conv-1",
        "user-1",
        [{"role": "user", "content": "hi"}],
        store,
        delay_seconds=0,
        memory_enabled=False,
    )


# --- memory_query intent ---


async def test_load_all_memories_returns_facts_and_constraints():
    """_load_all_memories loads both facts and constraints."""
    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "fact_1",
        {"content": "skin_type: oily", "category": "skin_type"},
    )
    await store.aput(
        constraints_ns("user-1"),
        "allergy_1",
        {"content": "Allergic to fragrance", "ingredient": "fragrance"},
    )

    memories = await _load_all_memories(store, "user-1")
    assert len(memories) == 2
    assert any("oily" in m for m in memories)
    assert any("fragrance" in m for m in memories)


async def test_load_all_memories_empty_store():
    """_load_all_memories returns empty list for user with no memories."""
    store = InMemoryStore()
    memories = await _load_all_memories(store, "user-1")
    assert memories == []


async def test_response_synth_memory_query_with_memories(mock_llm):
    """Response synth includes all memories in context for memory_query intent."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Here's what I know about you..."))

    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "fact_1",
        {"content": "skin_type: dry", "category": "skin_type"},
    )
    await store.aput(
        constraints_ns("user-1"),
        "allergy_1",
        {"content": "Allergic to parabens", "ingredient": "parabens"},
    )

    state = {
        "messages": [HumanMessage(content="What do you know about me?")],
        "user_id": "user-1",
        "current_intent": "memory_query",
        "product_results": [],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": [],
        "memory_notifications": [],
    }

    result = await response_synth_node(state, store=store)

    assert "messages" in result
    # Verify the LLM was called (it should generate a response)
    mock_llm.ainvoke.assert_called_once()
    # Check that the system prompt included memory context
    call_args = mock_llm.ainvoke.call_args[0][0]
    system_msg = call_args[0].content
    assert (
        "what you remember about them" in system_msg.lower()
        or "stored memories" in system_msg.lower()
    )


async def test_response_synth_memory_query_no_memories(mock_llm):
    """Response synth handles memory_query when no memories exist."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="I don't have any memories yet."))

    store = InMemoryStore()
    state = {
        "messages": [HumanMessage(content="What do you remember about me?")],
        "user_id": "user-1",
        "current_intent": "memory_query",
        "product_results": [],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": [],
        "memory_notifications": [],
    }

    result = await response_synth_node(state, store=store)

    assert "messages" in result
    call_args = mock_llm.ainvoke.call_args[0][0]
    system_msg = call_args[0].content
    assert (
        "don't have any stored memories" in system_msg.lower()
        or "no stored memories" in system_msg.lower()
    )


async def test_response_synth_without_store_still_works(mock_llm):
    """Response synth works without store (backward compat, no memory_query)."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Hello!"))

    state = {
        "messages": [HumanMessage(content="Hello")],
        "user_id": "user-1",
        "current_intent": "general_chat",
        "product_results": [],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": [],
        "memory_notifications": [],
    }

    result = await response_synth_node(state)

    assert "messages" in result
    assert result["messages"][0].content == "Hello!"
