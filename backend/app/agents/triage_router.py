import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.core.llm import get_llm

logger = structlog.get_logger()

TRIAGE_SYSTEM_PROMPT = """You are a triage router for an AI beauty and skincare concierge.
Classify the user's message into exactly one intent.

Intents:
- product_search: User wants product recommendations or is looking for specific products
- ingredient_check: User asks about specific ingredients, safety, or compatibility
- routine_advice: User wants skincare routine help, ordering, or regimen advice
- general_chat: Greetings, thanks, off-topic, or general conversation

Respond with ONLY the intent name, nothing else."""


class TriageResult(BaseModel):
    intent: str = Field(
        description="The classified intent",
        pattern="^(product_search|ingredient_check|routine_advice|general_chat)$",
    )


VALID_INTENTS = {"product_search", "ingredient_check", "routine_advice", "general_chat"}


async def triage_router_node(state: AgentState) -> dict:
    logger.info("Triage router invoked", user_id=state.get("user_id"))

    messages = state.get("messages", [])
    if not messages:
        return {"current_intent": "general_chat"}

    last_message = messages[-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    llm = get_llm(temperature=0)

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
                HumanMessage(content=user_text),
            ]
        )
        intent = response.content.strip().lower()

        if intent not in VALID_INTENTS:
            logger.warning("Unknown intent from LLM, defaulting to general_chat", raw_intent=intent)
            intent = "general_chat"

    except Exception as e:
        logger.error("Triage classification failed", error=str(e))
        intent = "general_chat"

    logger.info("Intent classified", intent=intent)

    return {
        "current_intent": intent,
        "memory_context": state.get("memory_context", []),
    }
