from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    conversation_id: str
    user_profile: dict[str, Any]
    hard_constraints: list[str]
    soft_preferences: list[str]
    current_intent: str
    product_results: list[dict[str, Any]]
    safety_check_passed: bool
    safety_violations: list[dict[str, Any]]
    memory_context: list[str]
    persona_scores: dict[str, float]
    error: str | None
