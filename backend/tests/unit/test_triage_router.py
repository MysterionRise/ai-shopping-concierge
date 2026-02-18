from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.triage_router import VALID_INTENTS, triage_router_node


@pytest.fixture
def mock_state():
    return {
        "messages": [HumanMessage(content="test message")],
        "user_id": "test-user",
        "conversation_id": "test-conv",
        "user_profile": {},
        "hard_constraints": [],
        "soft_preferences": [],
        "current_intent": "",
        "product_results": [],
        "safety_check_passed": True,
        "safety_violations": [],
        "memory_context": [],
        "persona_scores": {},
        "error": None,
    }


async def test_triage_classifies_product_search(mock_state, mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="product_search"))
    mock_state["messages"] = [HumanMessage(content="I need a moisturizer for oily skin")]

    result = await triage_router_node(mock_state)
    assert result["current_intent"] == "product_search"


async def test_triage_classifies_general_chat(mock_state, mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))
    mock_state["messages"] = [HumanMessage(content="Hello!")]

    result = await triage_router_node(mock_state)
    assert result["current_intent"] == "general_chat"


async def test_triage_classifies_ingredient_check(mock_state, mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="ingredient_check"))
    mock_state["messages"] = [HumanMessage(content="Is retinol safe for sensitive skin?")]

    result = await triage_router_node(mock_state)
    assert result["current_intent"] == "ingredient_check"


async def test_triage_classifies_routine_advice(mock_state, mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="routine_advice"))
    mock_state["messages"] = [HumanMessage(content="What order should I apply my products?")]

    result = await triage_router_node(mock_state)
    assert result["current_intent"] == "routine_advice"


async def test_triage_handles_unknown_intent(mock_state, mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="unknown_thing"))

    result = await triage_router_node(mock_state)
    assert result["current_intent"] == "general_chat"


async def test_triage_handles_llm_error(mock_state, mock_llm):
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

    result = await triage_router_node(mock_state)
    assert result["current_intent"] == "general_chat"


async def test_triage_empty_messages(mock_llm):
    state = {
        "messages": [],
        "user_id": "test",
        "memory_context": [],
    }
    result = await triage_router_node(state)
    assert result["current_intent"] == "general_chat"


def test_valid_intents():
    assert "product_search" in VALID_INTENTS
    assert "ingredient_check" in VALID_INTENTS
    assert "routine_advice" in VALID_INTENTS
    assert "memory_query" in VALID_INTENTS
    assert "general_chat" in VALID_INTENTS
    assert len(VALID_INTENTS) == 5
