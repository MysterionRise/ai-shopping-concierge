from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.response_synth import response_synth_node


async def test_response_synth_general_chat(mock_llm):
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Hello! How can I help with skincare?")
    )

    state = {
        "messages": [HumanMessage(content="Hello!")],
        "current_intent": "general_chat",
        "product_results": [],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": [],
    }

    result = await response_synth_node(state)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "Hello! How can I help with skincare?"


async def test_response_synth_with_products(mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Here are some products for you!"))

    state = {
        "messages": [HumanMessage(content="Find me a moisturizer")],
        "current_intent": "product_search",
        "product_results": [{"name": "Good Cream", "brand": "BrandX", "safety_score": 9.0}],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": [],
    }

    result = await response_synth_node(state)
    assert len(result["messages"]) == 1


async def test_response_synth_with_violations(mock_llm):
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(content="Some products were filtered for safety.")
    )

    state = {
        "messages": [HumanMessage(content="Find me a moisturizer")],
        "current_intent": "product_search",
        "product_results": [],
        "safety_violations": [
            {"product": "Bad Cream", "matches": [{"ingredient": "methylparaben"}]}
        ],
        "safety_check_passed": False,
        "memory_context": [],
    }

    result = await response_synth_node(state)
    assert len(result["messages"]) == 1


async def test_response_synth_with_memory(mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Based on your preferences..."))

    state = {
        "messages": [HumanMessage(content="Help me")],
        "current_intent": "general_chat",
        "product_results": [],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": ["User has dry skin", "Prefers fragrance-free products"],
    }

    result = await response_synth_node(state)
    assert len(result["messages"]) == 1


async def test_response_synth_llm_error(mock_llm):
    mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM down"))

    state = {
        "messages": [HumanMessage(content="Hi")],
        "current_intent": "general_chat",
        "product_results": [],
        "safety_violations": [],
        "safety_check_passed": True,
        "memory_context": [],
    }

    result = await response_synth_node(state)
    assert "sorry" in result["messages"][0].content.lower()
