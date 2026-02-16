import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.agents.state import AgentState
from app.core.llm import get_llm

logger = structlog.get_logger()

EXTRACT_SYSTEM_PROMPT = """You are a search intent extractor for a beauty product database.
Given the user's message and conversation context, extract the search parameters.
Respond in this exact format (one per line):
product_type: <type of product, e.g. moisturizer, cleanser, serum>
properties: <desired properties, e.g. hydrating, oil-free, anti-aging>
skin_type: <user's skin type if mentioned, e.g. oily, dry, combination, sensitive>

If a field is not mentioned, write "unknown" for that field."""


class SearchIntent(BaseModel):
    product_type: str = "unknown"
    properties: str = "unknown"
    skin_type: str = "unknown"


def parse_search_intent(text: str) -> SearchIntent:
    intent = SearchIntent()
    for line in text.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "product_type":
                intent.product_type = value
            elif key == "properties":
                intent.properties = value
            elif key == "skin_type":
                intent.skin_type = value
    return intent


async def product_discovery_node(state: AgentState) -> dict:
    logger.info("Product discovery invoked", user_id=state.get("user_id"))

    messages = state.get("messages", [])
    if not messages:
        return {"product_results": []}

    last_message = messages[-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    llm = get_llm(temperature=0)

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=EXTRACT_SYSTEM_PROMPT),
                HumanMessage(content=user_text),
            ]
        )
        intent = parse_search_intent(response.content)
    except Exception as e:
        logger.error("Search intent extraction failed", error=str(e))
        intent = SearchIntent()

    # Build search query from intent
    query_parts = []
    if intent.product_type != "unknown":
        query_parts.append(intent.product_type)
    if intent.properties != "unknown":
        query_parts.append(intent.properties)
    if intent.skin_type != "unknown":
        query_parts.append(f"for {intent.skin_type} skin")

    search_query = " ".join(query_parts) if query_parts else user_text

    logger.info("Search query built", query=search_query)

    # Product search will be done via ChromaDB or DB in the graph orchestrator
    # For now, store the query and intent so downstream nodes can use it
    return {
        "product_results": [],  # Will be populated by graph orchestrator with DB/vector results
        "current_intent": state.get("current_intent", "product_search"),
    }
