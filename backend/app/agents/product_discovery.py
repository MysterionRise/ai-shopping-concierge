import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.agents.state import AgentState
from app.catalog.product_service import hybrid_search
from app.core.database import async_session_factory
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


def _generate_fit_reasons(intent: SearchIntent, product: dict) -> list[str]:
    """Generate human-readable fit reasons based on search intent and product."""
    reasons = []
    categories = [c.lower() for c in product.get("categories", [])]
    name_lower = (product.get("name") or "").lower()

    if intent.product_type != "unknown":
        pt = intent.product_type.lower()
        if any(pt in c for c in categories) or pt in name_lower:
            reasons.append(f"Matches your search for {intent.product_type}")

    if intent.skin_type != "unknown":
        st = intent.skin_type.lower()
        if st in name_lower or any(st in c for c in categories):
            reasons.append(f"Suitable for {intent.skin_type} skin")

    if intent.properties != "unknown":
        props = intent.properties.lower()
        ingredients = product.get("key_ingredients", [])
        ing_text = " ".join(i.lower() for i in ingredients)
        if any(p.strip() in ing_text or p.strip() in name_lower for p in props.split(",")):
            reasons.append(f"Contains {intent.properties}")

    if product.get("safety_badge") == "safe":
        reasons.append("Passed safety checks")

    if not reasons:
        reasons.append("Relevant to your search")

    return reasons


async def product_discovery_node(state: AgentState) -> dict:
    logger.info("Product discovery invoked", user_id=state.get("user_id"))

    messages = state.get("messages", [])
    if not messages:
        return {"product_results": []}

    last_message = messages[-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)
    if not isinstance(user_text, str):
        user_text = str(user_text)

    llm = get_llm(temperature=0)

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=EXTRACT_SYSTEM_PROMPT),
                HumanMessage(content=user_text),
            ]
        )
        content = response.content if isinstance(response.content, str) else str(response.content)
        intent = parse_search_intent(content)
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

    # Hybrid search: keyword + vector, with allergen pre-filtering
    hard_constraints = state.get("hard_constraints", [])
    product_results: list[dict] = []
    try:
        async with async_session_factory() as db:
            product_results = await hybrid_search(
                db,
                query=search_query,
                allergens=hard_constraints if hard_constraints else None,
                limit=10,
            )

        # Add fit reasons to each result
        for result in product_results:
            result["fit_reasons"] = _generate_fit_reasons(intent, result)

        logger.info("Products found", count=len(product_results))
    except Exception as e:
        logger.error("Product search failed", error=str(e))

    return {
        "product_results": product_results,
        "current_intent": state.get("current_intent", "product_search"),
    }
