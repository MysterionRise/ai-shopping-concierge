import structlog
from langgraph.graph import END, StateGraph

from app.agents.product_discovery import product_discovery_node
from app.agents.response_synth import response_synth_node
from app.agents.safety_constraint import safety_constraint_node
from app.agents.state import AgentState
from app.agents.triage_router import triage_router_node

logger = structlog.get_logger()


def route_after_triage(state: AgentState) -> str:
    intent = state.get("current_intent", "general_chat")
    if intent in ("product_search", "ingredient_check", "routine_advice"):
        return "safety_pre_filter"
    return "response_synth"


def route_after_safety_post(state: AgentState) -> str:
    return "response_synth"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("triage_router", triage_router_node)
    graph.add_node("safety_pre_filter", safety_constraint_node)
    graph.add_node("product_discovery", product_discovery_node)
    graph.add_node("safety_post_validate", safety_constraint_node)
    graph.add_node("response_synth", response_synth_node)

    # Entry
    graph.set_entry_point("triage_router")

    # Triage -> conditional routing
    graph.add_conditional_edges(
        "triage_router",
        route_after_triage,
        {
            "safety_pre_filter": "safety_pre_filter",
            "response_synth": "response_synth",
        },
    )

    # Safety pre-filter -> product discovery -> safety post-validate -> response synth
    graph.add_edge("safety_pre_filter", "product_discovery")
    graph.add_edge("product_discovery", "safety_post_validate")
    graph.add_edge("safety_post_validate", "response_synth")

    graph.add_edge("response_synth", END)

    return graph


def get_compiled_graph():
    graph = build_graph()
    return graph.compile()
