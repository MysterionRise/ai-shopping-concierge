"""Tests for the LangMem store configuration and basic operations.

Uses InMemoryStore (no Postgres needed) to verify the namespace layout
and CRUD operations that the rest of the app depends on.
"""

import pytest
from langgraph.store.memory import InMemoryStore

from app.memory.langmem_config import (
    CONSTRAINTS_NS,
    EPISODES_NS,
    PENDING_CONFIRMATIONS_NS,
    USER_FACTS_NS,
    constraints_ns,
    episodes_ns,
    pending_confirmations_ns,
    user_facts_ns,
)


@pytest.fixture
def store():
    """InMemoryStore for unit tests — no embeddings, no Postgres."""
    return InMemoryStore()


def test_namespace_helpers():
    assert user_facts_ns("u1") == ("user_facts", "u1")
    assert constraints_ns("u1") == ("constraints", "u1")
    assert episodes_ns("u1") == ("episodes", "u1")
    assert pending_confirmations_ns("u1") == ("pending_confirmations", "u1")


def test_namespace_constants():
    assert USER_FACTS_NS == ("user_facts",)
    assert CONSTRAINTS_NS == ("constraints",)
    assert EPISODES_NS == ("episodes",)
    assert PENDING_CONFIRMATIONS_NS == ("pending_confirmations",)


async def test_store_put_and_get(store):
    ns = user_facts_ns("test-user")
    await store.aput(ns, "fact_1", {"content": "Has dry skin"})

    item = await store.aget(ns, "fact_1")
    assert item is not None
    assert item.value["content"] == "Has dry skin"


async def test_store_search(store):
    ns = user_facts_ns("test-user")
    await store.aput(ns, "fact_1", {"content": "Has dry skin"})
    await store.aput(ns, "fact_2", {"content": "Prefers Korean brands"})

    results = await store.asearch(ns)
    assert len(results) == 2
    contents = {r.value["content"] for r in results}
    assert "Has dry skin" in contents
    assert "Prefers Korean brands" in contents


async def test_store_delete(store):
    ns = user_facts_ns("test-user")
    await store.aput(ns, "fact_1", {"content": "Has dry skin"})

    await store.adelete(ns, "fact_1")

    item = await store.aget(ns, "fact_1")
    assert item is None


async def test_store_update(store):
    ns = user_facts_ns("test-user")
    await store.aput(ns, "fact_1", {"content": "Has dry skin"})
    await store.aput(ns, "fact_1", {"content": "Has oily skin"})

    item = await store.aget(ns, "fact_1")
    assert item is not None
    assert item.value["content"] == "Has oily skin"


async def test_namespace_isolation(store):
    """Facts for different users should not leak across namespaces."""
    await store.aput(user_facts_ns("user-a"), "fact_1", {"content": "Allergic to fragrance"})
    await store.aput(user_facts_ns("user-b"), "fact_1", {"content": "Loves fragrance"})

    results_a = await store.asearch(user_facts_ns("user-a"))
    results_b = await store.asearch(user_facts_ns("user-b"))

    assert len(results_a) == 1
    assert results_a[0].value["content"] == "Allergic to fragrance"
    assert len(results_b) == 1
    assert results_b[0].value["content"] == "Loves fragrance"


async def test_constraints_namespace(store):
    ns = constraints_ns("test-user")
    await store.aput(
        ns,
        "allergy_fragrance",
        {
            "ingredient": "fragrance",
            "severity": "absolute",
            "source": "user_stated",
        },
    )

    results = await store.asearch(ns)
    assert len(results) == 1
    assert results[0].value["ingredient"] == "fragrance"
    assert results[0].value["severity"] == "absolute"


async def test_compile_graph_with_store(store):
    """Graph compiles successfully when a store is provided."""
    from app.agents.graph import compile_graph

    graph = compile_graph(store=store)
    assert graph is not None
