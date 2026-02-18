from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.graph import build_graph, get_compiled_graph, route_after_triage


def test_graph_compiles():
    graph = get_compiled_graph()
    assert graph is not None


def test_build_graph_has_nodes():
    graph = build_graph()
    assert "triage_router" in graph.nodes
    assert "response_synth" in graph.nodes
    assert "product_discovery" in graph.nodes
    assert "safety_post_validate" in graph.nodes


def test_route_after_triage_product_search():
    state = {"current_intent": "product_search"}
    assert route_after_triage(state) == "product_discovery"


def test_route_after_triage_ingredient_check():
    state = {"current_intent": "ingredient_check"}
    assert route_after_triage(state) == "product_discovery"


def test_route_after_triage_routine_advice():
    state = {"current_intent": "routine_advice"}
    assert route_after_triage(state) == "product_discovery"


def test_route_after_triage_general_chat():
    state = {"current_intent": "general_chat"}
    assert route_after_triage(state) == "response_synth"


def test_route_after_triage_empty():
    state = {}
    assert route_after_triage(state) == "response_synth"


async def test_full_graph_invocation(mock_llm):
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="general_chat"))

    graph = get_compiled_graph()

    initial_state = {
        "messages": [HumanMessage(content="Hello!")],
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

    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "test-graph-thread"}},
    )
    assert "messages" in result
    assert len(result["messages"]) >= 2  # original + response
