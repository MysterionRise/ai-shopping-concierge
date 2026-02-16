from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.product_discovery import (
    parse_search_intent,
    product_discovery_node,
)


def test_parse_search_intent():
    text = """product_type: moisturizer
properties: hydrating, lightweight
skin_type: oily"""
    result = parse_search_intent(text)
    assert result.product_type == "moisturizer"
    assert "hydrating" in result.properties
    assert result.skin_type == "oily"


def test_parse_search_intent_partial():
    text = "product_type: serum"
    result = parse_search_intent(text)
    assert result.product_type == "serum"
    assert result.properties == "unknown"
    assert result.skin_type == "unknown"


def test_parse_search_intent_empty():
    result = parse_search_intent("")
    assert result.product_type == "unknown"


async def test_product_discovery_node(mock_llm):
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="product_type: moisturizer\nproperties: hydrating\nskin_type: oily"
        )
    )

    state = {
        "messages": [HumanMessage(content="I need a moisturizer for oily skin")],
        "user_id": "test",
        "current_intent": "product_search",
    }

    result = await product_discovery_node(state)
    assert "product_results" in result


async def test_product_discovery_empty_messages(mock_llm):
    state = {"messages": [], "user_id": "test"}
    result = await product_discovery_node(state)
    assert result["product_results"] == []
