"""Tests for hot-path memory operations in agent nodes.

Tests detect_user_facts, _load_memory_context, _store_detected_facts,
and the integration with triage_router_node.
"""

from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.memory import InMemoryStore

from app.agents.triage_router import (
    _load_memory_context,
    _store_detected_facts,
    detect_user_facts,
    triage_router_node,
)
from app.memory.langmem_config import constraints_ns, user_facts_ns

# --- detect_user_facts ---


def test_detect_allergy():
    facts = detect_user_facts("I'm allergic to fragrance")
    assert len(facts) == 1
    assert facts[0]["category"] == "allergy"
    assert facts[0]["value"] == "fragrance"


def test_detect_sensitivity():
    facts = detect_user_facts("I'm sensitive to retinol")
    assert len(facts) == 1
    assert facts[0]["category"] == "sensitivity"
    assert facts[0]["value"] == "retinol"


def test_detect_skin_type_i_have():
    facts = detect_user_facts("I have oily skin")
    assert any(f["category"] == "skin_type" and f["value"] == "oily" for f in facts)


def test_detect_skin_type_my_skin_is():
    facts = detect_user_facts("My skin is dry")
    assert any(f["category"] == "skin_type" and f["value"] == "dry" for f in facts)


def test_detect_preference():
    facts = detect_user_facts("I prefer Korean brands")
    assert any(f["category"] == "preference" for f in facts)


def test_detect_aversion():
    facts = detect_user_facts("I don't like heavy creams")
    assert any(f["category"] == "aversion" for f in facts)


def test_detect_no_facts():
    facts = detect_user_facts("What moisturizer should I use?")
    assert len(facts) == 0


def test_detect_multiple_facts():
    facts = detect_user_facts("I have dry skin and I'm allergic to sulfates")
    categories = {f["category"] for f in facts}
    assert "skin_type" in categories
    assert "allergy" in categories


# --- _load_memory_context ---


async def test_load_memory_context_empty_store():
    store = InMemoryStore()
    result = await _load_memory_context(store, "user-1", "hello")
    assert result["active_constraints"] == []
    assert result["memory_context"] == []


async def test_load_memory_context_with_constraints():
    store = InMemoryStore()
    await store.aput(
        constraints_ns("user-1"),
        "allergy_fragrance",
        {"ingredient": "fragrance", "severity": "absolute", "content": "Allergic to fragrance"},
    )

    result = await _load_memory_context(store, "user-1", "show me moisturizers")
    assert len(result["active_constraints"]) == 1
    assert result["active_constraints"][0]["ingredient"] == "fragrance"


async def test_load_memory_context_with_facts():
    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "skin_type_1",
        {"content": "Has dry skin", "category": "skin_type", "value": "dry"},
    )

    result = await _load_memory_context(store, "user-1", "recommend a moisturizer")
    assert len(result["memory_context"]) >= 1
    assert any("dry skin" in m for m in result["memory_context"])


# --- _store_detected_facts ---


async def test_store_allergy_creates_constraint():
    store = InMemoryStore()
    facts = [{"category": "allergy", "value": "fragrance", "source_text": "test"}]

    notifications = await _store_detected_facts(store, "user-1", facts)

    assert len(notifications) == 1
    assert "fragrance allergy" in notifications[0]

    items = await store.asearch(constraints_ns("user-1"))
    assert len(items) == 1
    assert items[0].value["ingredient"] == "fragrance"
    assert items[0].value["severity"] == "absolute"


async def test_store_sensitivity_creates_constraint():
    store = InMemoryStore()
    facts = [{"category": "sensitivity", "value": "retinol", "source_text": "test"}]

    notifications = await _store_detected_facts(store, "user-1", facts)

    assert len(notifications) == 1
    assert "retinol" in notifications[0]

    items = await store.asearch(constraints_ns("user-1"))
    assert len(items) == 1
    assert items[0].value["severity"] == "high"


async def test_store_skin_type_creates_fact():
    store = InMemoryStore()
    facts = [{"category": "skin_type", "value": "oily", "source_text": "test"}]

    notifications = await _store_detected_facts(store, "user-1", facts)

    assert len(notifications) == 1
    assert "oily skin" in notifications[0]

    items = await store.asearch(user_facts_ns("user-1"))
    assert len(items) == 1
    assert items[0].value["value"] == "oily"


async def test_store_preference_creates_fact():
    store = InMemoryStore()
    facts = [{"category": "preference", "value": "korean brands", "source_text": "test"}]

    notifications = await _store_detected_facts(store, "user-1", facts)

    assert len(notifications) == 1
    assert "korean brands" in notifications[0]


# --- triage_router_node with store ---


async def test_triage_with_store_loads_constraints(mock_llm):
    """Triage node merges store constraints into hard_constraints."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

    store = InMemoryStore()
    await store.aput(
        constraints_ns("user-1"),
        "allergy_fragrance",
        {"ingredient": "fragrance", "severity": "absolute", "content": "Allergic to fragrance"},
    )

    state = {
        "messages": [HumanMessage(content="recommend a moisturizer")],
        "user_id": "user-1",
        "hard_constraints": [],
        "memory_context": [],
    }

    result = await triage_router_node(state, store=store)

    assert "fragrance" in result.get("hard_constraints", [])
    assert len(result.get("active_constraints", [])) == 1


async def test_triage_detects_and_stores_allergy(mock_llm):
    """Triage node detects 'allergic to X' and stores constraint."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

    store = InMemoryStore()
    state = {
        "messages": [HumanMessage(content="I'm allergic to sulfates")],
        "user_id": "user-1",
        "hard_constraints": [],
        "memory_context": [],
    }

    result = await triage_router_node(state, store=store)

    assert len(result.get("memory_notifications", [])) >= 1
    assert any("sulfates" in n for n in result["memory_notifications"])

    # Verify stored in constraint namespace
    items = await store.asearch(constraints_ns("user-1"))
    assert len(items) == 1
    assert items[0].value["ingredient"] == "sulfates"


async def test_triage_without_store_still_works(mock_llm):
    """Triage node works normally when no store is available (backward compat)."""
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="product_search"))

    state = {
        "messages": [HumanMessage(content="I have oily skin, recommend a cleanser")],
        "user_id": "user-1",
        "hard_constraints": [],
        "memory_context": [],
    }

    result = await triage_router_node(state)

    assert result["current_intent"] == "product_search"
    assert result.get("memory_notifications", []) == []
