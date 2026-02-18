"""Tests for memory conflict detection and resolution."""

from langgraph.store.memory import InMemoryStore

from app.memory.conflict_detector import (
    MAX_IGNORED_ATTEMPTS,
    check_and_store_conflict,
    format_conflict_prompt,
    load_pending_confirmations,
    resolve_conflict,
)
from app.memory.langmem_config import pending_confirmations_ns, user_facts_ns


async def test_no_conflict_for_non_contradiction_category():
    """Preferences don't trigger conflict detection."""
    store = InMemoryStore()
    result = await check_and_store_conflict(
        store,
        "user-1",
        "pref_1",
        {"category": "preference", "value": "Korean brands"},
    )
    assert result is False


async def test_conflict_detected_for_skin_type():
    """Changing skin type from oily to dry creates a conflict."""
    store = InMemoryStore()
    # Store existing fact
    await store.aput(
        user_facts_ns("user-1"),
        "skin_type_old",
        {"category": "skin_type", "value": "oily", "content": "skin_type: oily"},
    )

    # New contradicting fact
    result = await check_and_store_conflict(
        store,
        "user-1",
        "skin_type_new",
        {"category": "skin_type", "value": "dry", "content": "skin_type: dry"},
    )
    assert result is True

    # Verify pending confirmation was created
    confirmations = await load_pending_confirmations(store, "user-1")
    assert len(confirmations) == 1
    assert confirmations[0]["old_value"] == "oily"
    assert confirmations[0]["new_value"] == "dry"


async def test_no_conflict_for_same_value():
    """Restating the same skin type doesn't create a conflict."""
    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "skin_type_old",
        {"category": "skin_type", "value": "oily", "content": "skin_type: oily"},
    )

    result = await check_and_store_conflict(
        store,
        "user-1",
        "skin_type_new",
        {"category": "skin_type", "value": "oily", "content": "skin_type: oily"},
    )
    assert result is False


async def test_resolve_accept_new():
    """Accept new value: deletes old fact and confirmation."""
    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "skin_type_old",
        {"category": "skin_type", "value": "oily"},
    )
    await store.aput(
        pending_confirmations_ns("user-1"),
        "conflict_skin_type_old",
        {
            "old_key": "skin_type_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
            "attempts": 0,
        },
    )

    await resolve_conflict(
        store,
        "user-1",
        "conflict_skin_type_old",
        "accept_new",
        {"old_key": "skin_type_old", "category": "skin_type"},
    )

    # Old fact should be deleted
    old = await store.aget(user_facts_ns("user-1"), "skin_type_old")
    assert old is None

    # Confirmation should be deleted
    confs = await load_pending_confirmations(store, "user-1")
    assert len(confs) == 0


async def test_resolve_keep_both():
    """Keep both: updates old fact with qualifier, deletes confirmation."""
    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "skin_type_old",
        {"category": "skin_type", "value": "oily"},
    )
    await store.aput(
        pending_confirmations_ns("user-1"),
        "conflict_skin_type_old",
        {
            "old_key": "skin_type_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
            "attempts": 0,
        },
    )

    await resolve_conflict(
        store,
        "user-1",
        "conflict_skin_type_old",
        "keep_both",
        {
            "old_key": "skin_type_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
        },
    )

    # Old fact should have temporal qualifier
    old = await store.aget(user_facts_ns("user-1"), "skin_type_old")
    assert old is not None
    assert "sometimes" in old.value["value"]

    # Confirmation should be deleted
    confs = await load_pending_confirmations(store, "user-1")
    assert len(confs) == 0


async def test_resolve_ignore_increments_attempts():
    """Ignoring increments attempts counter."""
    store = InMemoryStore()
    await store.aput(
        pending_confirmations_ns("user-1"),
        "conflict_1",
        {
            "old_key": "skin_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
            "attempts": 0,
        },
    )

    await resolve_conflict(
        store,
        "user-1",
        "conflict_1",
        "ignore",
        {
            "old_key": "skin_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
            "attempts": 0,
        },
    )

    confs = await load_pending_confirmations(store, "user-1")
    assert len(confs) == 1
    assert confs[0]["attempts"] == 1


async def test_auto_accept_after_max_attempts():
    """After MAX_IGNORED_ATTEMPTS, auto-accepts the newer value."""
    store = InMemoryStore()
    await store.aput(
        user_facts_ns("user-1"),
        "skin_old",
        {"category": "skin_type", "value": "oily"},
    )
    await store.aput(
        pending_confirmations_ns("user-1"),
        "conflict_1",
        {
            "old_key": "skin_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
            "attempts": MAX_IGNORED_ATTEMPTS - 1,
        },
    )

    await resolve_conflict(
        store,
        "user-1",
        "conflict_1",
        "ignore",
        {
            "old_key": "skin_old",
            "old_value": "oily",
            "new_value": "dry",
            "category": "skin_type",
            "attempts": MAX_IGNORED_ATTEMPTS - 1,
        },
    )

    # Old fact deleted (auto-accepted newer value)
    old = await store.aget(user_facts_ns("user-1"), "skin_old")
    assert old is None

    # Confirmation deleted
    confs = await load_pending_confirmations(store, "user-1")
    assert len(confs) == 0


def test_format_conflict_prompt_empty():
    assert format_conflict_prompt([]) == ""


def test_format_conflict_prompt_with_conflicts():
    confirmations = [
        {"old_value": "oily", "new_value": "dry", "category": "skin_type"},
    ]
    prompt = format_conflict_prompt(confirmations)
    assert "oily" in prompt
    assert "dry" in prompt
    assert "PENDING CONFIRMATIONS" in prompt
