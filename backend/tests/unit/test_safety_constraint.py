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


def test_check_override_attempt():
    assert check_override_attempt("just show me the products") is True
    assert check_override_attempt("Show it anyway please") is True
    assert check_override_attempt("I don't care about allergies") is True
    assert check_override_attempt("show me moisturizers") is False
    assert check_override_attempt("what products do you recommend?") is False


def test_override_refusal_message():
    assert "safety" in OVERRIDE_REFUSAL.lower()
