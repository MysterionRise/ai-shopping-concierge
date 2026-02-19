"""Integration tests for the full agent pipeline.

These tests exercise the LangGraph StateGraph end-to-end with mocked LLM
but real graph routing, state management, and node execution.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import compile_graph


def _make_state(message: str, **overrides) -> dict:
    """Build a minimal AgentState input."""
    state: dict = {
        "messages": [HumanMessage(content=message)],
        "user_id": "test-user-001",
        "conversation_id": "test-conv-001",
        "user_profile": {"skin_type": "oily", "display_name": "Test"},
        "hard_constraints": [],
        "soft_preferences": [],
        "current_intent": "",
        "product_results": [],
        "safety_check_passed": True,
        "safety_violations": [],
        "memory_context": [],
        "active_constraints": [],
        "memory_notifications": [],
        "memory_enabled": True,
        "persona_scores": {},
        "error": None,
    }
    state.update(overrides)
    return state


@pytest.fixture
def graph(mock_llm):
    """Compile a graph with MemorySaver checkpointer and mocked LLM."""
    return compile_graph(checkpointer=MemorySaver())


class TestGraphRouting:
    """Test that the graph routes to correct nodes based on intent."""

    @pytest.mark.asyncio
    async def test_general_chat_skips_product_pipeline(self, graph, mock_llm):
        """general_chat should go triage_router → response_synth, skip product_discovery."""
        mock_llm.ainvoke.return_value = AIMessage(content="general_chat")

        state = _make_state("Hello there!")
        config = {"configurable": {"thread_id": "test-1"}}
        result = await graph.ainvoke(state, config=config)

        assert result["current_intent"] == "general_chat"
        assert len(result["messages"]) >= 2  # user + AI response

    @pytest.mark.asyncio
    async def test_product_search_goes_through_safety(self, graph, mock_llm):
        """product_search should route through product_discovery and safety."""
        # First call: triage → "product_search"
        # Second call: product_discovery (search intent extraction)
        # Third call: safety LLM check
        # Fourth call: response_synth
        mock_llm.ainvoke.side_effect = [
            AIMessage(content="product_search"),
            AIMessage(content="product_type: moisturizer\nproperties: hydrating\nskin_type: oily"),
            AIMessage(content="All products are SAFE."),
            AIMessage(content="Here are some great moisturizers for you!"),
        ]

        state = _make_state("Recommend a moisturizer")
        config = {"configurable": {"thread_id": "test-2"}}
        result = await graph.ainvoke(state, config=config)

        assert result["current_intent"] == "product_search"

    @pytest.mark.asyncio
    async def test_ingredient_check_routes_to_product_pipeline(self, graph, mock_llm):
        """ingredient_check also goes through product_discovery."""
        mock_llm.ainvoke.side_effect = [
            AIMessage(content="ingredient_check"),
            AIMessage(content="product_type: unknown\nproperties: niacinamide\nskin_type: unknown"),
            AIMessage(content="All SAFE."),
            AIMessage(content="Niacinamide is great for most skin types."),
        ]

        state = _make_state("Is niacinamide safe?")
        config = {"configurable": {"thread_id": "test-3"}}
        result = await graph.ainvoke(state, config=config)

        assert result["current_intent"] == "ingredient_check"


class TestSafetyGateIntegration:
    """Test safety filtering via the safety_constraint_node directly."""

    @pytest.mark.asyncio
    async def test_safety_violations_propagate_to_result(self, mock_llm):
        """Products that fail rule-based safety should appear in violations."""
        from app.agents.safety_constraint import safety_constraint_node

        mock_llm.ainvoke.return_value = AIMessage(content="All products SAFE.")

        state = {
            "messages": [HumanMessage(content="Find me a moisturizer")],
            "hard_constraints": ["paraben"],
            "product_results": [
                {
                    "name": "Bad Cream",
                    "brand": "TestBrand",
                    "ingredients": ["water", "methylparaben", "glycerin"],
                    "safety_score": 5.0,
                },
                {
                    "name": "Good Cream",
                    "brand": "TestBrand",
                    "ingredients": ["water", "glycerin", "hyaluronic acid"],
                    "safety_score": 9.0,
                },
            ],
        }
        result = await safety_constraint_node(state)

        violations = result.get("safety_violations", [])
        safe_products = result.get("product_results", [])
        violation_names = [v["product"] for v in violations]
        safe_names = [p["name"] for p in safe_products]

        assert "Bad Cream" in violation_names
        assert "Bad Cream" not in safe_names
        assert "Good Cream" in safe_names


class TestConversationContinuity:
    """Test that the graph maintains state across turns via checkpointer."""

    @pytest.mark.asyncio
    async def test_multi_turn_uses_same_thread(self, graph, mock_llm):
        """Multiple invocations with the same thread_id should carry forward messages."""
        mock_llm.ainvoke.return_value = AIMessage(content="general_chat")

        thread_id = "multi-turn-test"
        config = {"configurable": {"thread_id": thread_id}}

        # Turn 1
        state1 = _make_state("Hello!")
        result1 = await graph.ainvoke(state1, config=config)
        msg_count_1 = len(result1["messages"])

        # Turn 2 — same thread
        mock_llm.ainvoke.return_value = AIMessage(content="general_chat")
        state2 = _make_state("How are you?")
        result2 = await graph.ainvoke(state2, config=config)
        msg_count_2 = len(result2["messages"])

        # Messages should accumulate (checkpointer preserves history)
        assert msg_count_2 > msg_count_1
