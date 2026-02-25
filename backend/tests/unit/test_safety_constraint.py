from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.safety_constraint import (
    OVERRIDE_REFUSAL,
    check_override_attempt,
    safety_constraint_node,
)


@pytest.fixture
def state_with_products():
    return {
        "messages": [],
        "user_id": "test",
        "hard_constraints": ["paraben"],
        "product_results": [
            {
                "name": "Clean Moisturizer",
                "ingredients": ["water", "glycerin", "shea butter"],
                "safety_score": 9.0,
            },
            {
                "name": "Paraben Cream",
                "ingredients": ["water", "methylparaben", "fragrance"],
                "safety_score": 5.0,
            },
        ],
        "safety_check_passed": True,
        "safety_violations": [],
    }


async def test_rule_based_filtering(state_with_products, mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="All SAFE"))
    result = await safety_constraint_node(state_with_products)
    assert len(result["product_results"]) == 1
    assert result["product_results"][0]["name"] == "Clean Moisturizer"
    assert len(result["safety_violations"]) >= 1


async def test_no_constraints_passes_all(mock_llm):
    state = {
        "hard_constraints": [],
        "product_results": [
            {"name": "Product A", "ingredients": ["water"]},
            {"name": "Product B", "ingredients": ["glycerin"]},
        ],
        "safety_check_passed": True,
        "safety_violations": [],
    }
    result = await safety_constraint_node(state)
    assert result["safety_check_passed"] is True
    assert result["safety_violations"] == []


async def test_all_vetoed(mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="All SAFE"))
    state = {
        "hard_constraints": ["paraben"],
        "product_results": [
            {"name": "Bad 1", "ingredients": ["methylparaben"]},
            {"name": "Bad 2", "ingredients": ["propylparaben"]},
        ],
        "safety_check_passed": True,
        "safety_violations": [],
    }
    result = await safety_constraint_node(state)
    assert result["safety_check_passed"] is False
    assert len(result["product_results"]) == 0


class TestCheckOverrideAttempt:
    """Tests for the override detection logic."""

    # --- Messages that SHOULD be caught as override attempts ---

    @pytest.mark.parametrize(
        "message",
        [
            # Original phrases (regression)
            "show it anyway please",
            "show me anyway",
            "ignore my allergies",
            "i'll take the risk",
            "bypass safety",
            # Variations with extra whitespace / punctuation
            "SHOW  IT   ANYWAY!!!",
            "  ignore   my   allergies  ",
            "bypass... safety... please",
            # Semantic variations — "show anyway"
            "just show it anyway",
            "show them anyway",
            "give me them anyway",
            "recommend it anyway",
            "list those anyway",
            "tell me anyway",
            # Override / bypass / skip / disable
            "override the safety check",
            "override allergy filter",
            "bypass the allergy check",
            "skip the safety filter",
            "skip allergy check please",
            "disable safety filter",
            "disable the allergy check",
            "turn off safety check",
            "turn off the allergy filter",
            # Risk acceptance
            "i will take the risk",
            "ill take the risk",
            "willing to accept the risk",
            # Don't care
            "i don't care about allergies",
            "i dont care about allergies",
            "i don't care about safety",
            "don't care about sensitivity",
            "i don't care about ingredients",
            "i don't care about reactions",
            # Show unsafe
            "show the unsafe ones",
            "show me unsafe products",
            # Just give me all
            "just give me all products",
            "just give me every product",
            # Include blocked/filtered
            "include the unsafe products",
            "include the filtered products",
            "add the blocked ones back",
            "include the flagged items",
            # Remove / clear constraints
            "remove my allergies",
            "delete my allergy constraints",
            "clear my restrictions",
            "remove the safety filter",
            # Forget allergies
            "forget my allergies",
            "forget my allergy please",
            # Pretend / lying
            "pretend I'm not allergic",
            "pretend I have no allergies",
            "i'm not really allergic",
            "i'm not actually allergic to that",
            "i don't actually have allergies",
            # Stop filtering
            "stop filtering products",
            "stop blocking those",
            "stop checking for allergens",
            # Regardless
            "show me everything regardless",
            "give me all products regardless",
            # Smart quotes / unicode
            "I\u2019ll take the risk",
            "don\u2019t care about allergies",
        ],
    )
    def test_override_caught(self, message):
        assert (
            check_override_attempt(message) is True
        ), f"Expected override to be caught: {message!r}"

    # --- Messages that should NOT be caught (false positives) ---

    @pytest.mark.parametrize(
        "message",
        [
            # Normal product searches
            "show me moisturizers",
            "just show me some serums",
            "show me safe moisturizers",
            "show me products for oily skin",
            "what products do you recommend?",
            "can you recommend a sunscreen?",
            "list your best sellers",
            # Mentions of allergies in legitimate context
            "I care about ingredients",
            "I have a paraben allergy",
            "what are my allergies?",
            "I want to add an allergy",
            "can you check if this is safe for my allergies?",
            "I'm allergic to parabens",
            "are there allergens in this product?",
            # Casual phrases that shouldn't trigger
            "i don't care about price",
            "i don't care about the brand",
            "i don't care about fragrance",
            "skip to the recommendations",
            "show me everything under $30",
            "give me all the details",
            "tell me about this product",
            "anyway, what do you think?",
            "I actually like that product",
            "turn off topic — what about toners?",
            "can you filter by price?",
            "stop showing me expensive ones",
            "remove the price filter",
            "forget about the previous search",
            "I'm not really sure what I want",
            "ignore my previous message",
            "I'll take the serum",
        ],
    )
    def test_no_false_positive(self, message):
        assert (
            check_override_attempt(message) is False
        ), f"False positive on legitimate message: {message!r}"


def test_override_refusal_message():
    assert "safety" in OVERRIDE_REFUSAL.lower()
