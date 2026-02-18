import structlog
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langgraph.store.base import BaseStore

from app.agents.state import AgentState
from app.core.llm import get_llm
from app.memory.langmem_config import constraints_ns, user_facts_ns

logger = structlog.get_logger()

RESPONSE_SYSTEM_PROMPT = """You are a friendly AI beauty and skincare concierge.
You help users find the right beauty products for their skin type, concerns, and preferences.

Guidelines:
- Be warm, conversational, and knowledgeable
- Always prioritize user safety — respect allergies and sensitivities
- When recommending products, explain WHY each product fits the user
- If products were vetoed for safety, explain clearly and offer alternatives
- Never pressure the user to buy anything
- If you don't know something, say so honestly
- Reference the user's profile/preferences when available

{context}"""

PRODUCT_TEMPLATE = """
**{name}** by {brand}
- Safety Score: {safety_score}/10
- Key Ingredients: {ingredients}
- {fit_reason}
"""

SAFETY_REJECTION = """I found some products but had to filter out ones containing ingredients
you're sensitive to. Here's what I flagged:
{violations}

Here are safe alternatives I found for you:"""


async def _load_all_memories(store: BaseStore, user_id: str) -> list[str]:
    """Load all user memories for the memory_query intent."""
    memories = []
    try:
        facts = await store.asearch(user_facts_ns(user_id), limit=50)
        for item in facts:
            content = item.value.get("content", "")
            if content:
                memories.append(content)
    except Exception as e:
        logger.warning("Failed to load facts for memory_query", error=str(e))
    try:
        constraint_items = await store.asearch(constraints_ns(user_id), limit=50)
        for item in constraint_items:
            content = item.value.get("content", "")
            if content:
                memories.append(content)
    except Exception as e:
        logger.warning("Failed to load constraints for memory_query", error=str(e))
    return memories


async def response_synth_node(state: AgentState, *, store: BaseStore = None) -> dict:
    logger.info("Response synthesis invoked", intent=state.get("current_intent"))

    intent = state.get("current_intent", "general_chat")
    product_results = state.get("product_results", [])
    safety_violations = state.get("safety_violations", [])
    safety_passed = state.get("safety_check_passed", True)
    memory_context = state.get("memory_context", [])
    memory_notifications = state.get("memory_notifications", [])

    context_parts = []

    # For memory_query, load all memories and present them
    if intent == "memory_query" and store:
        user_id = state.get("user_id", "")
        all_memories = await _load_all_memories(store, user_id) if user_id else []
        if all_memories:
            context_parts.append(
                "The user wants to know what you remember about them. "
                "Present ALL of the following stored memories conversationally:\n"
                + "\n".join(f"- {m}" for m in all_memories)
            )
        else:
            context_parts.append(
                "The user wants to know what you remember about them. "
                "You don't have any stored memories yet. Let them know and suggest "
                "they share their skin type, concerns, or preferences."
            )

    if memory_notifications:
        context_parts.append(
            "IMPORTANT — Include these memory acknowledgments naturally in your response:\n"
            + "\n".join(f"- {n}" for n in memory_notifications)
        )

    if memory_context:
        context_parts.append(
            "User context from previous conversations:\n"
            + "\n".join(f"- {m}" for m in memory_context)
        )

    if intent in ("product_search", "ingredient_check", "routine_advice"):
        if safety_violations:
            violation_text = "\n".join(
                f"- {v.get('product', 'Unknown')}: flagged for "
                f"{v.get('matches', v.get('reason', 'safety concern'))}"
                for v in safety_violations
            )
            context_parts.append(f"Safety violations found:\n{violation_text}")

        if product_results:
            product_text = "\n".join(
                f"- {p.get('name', 'Unknown')} by {p.get('brand', 'Unknown')} "
                f"(safety: {p.get('safety_score', 'N/A')}/10)"
                for p in product_results
            )
            context_parts.append(f"Safe products found:\n{product_text}")
        elif not safety_passed:
            context_parts.append(
                "All products were filtered out due to safety constraints. "
                "Suggest the user broaden their search or offer general advice."
            )

    context = "\n\n".join(context_parts) if context_parts else ""
    system_prompt = RESPONSE_SYSTEM_PROMPT.format(context=context)

    llm = get_llm()

    try:
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)] + list(
            state["messages"]
        )
        response = await llm.ainvoke(messages)
        return {"messages": [AIMessage(content=response.content)]}
    except Exception as e:
        logger.error("Response synthesis failed", error=str(e))
        return {
            "messages": [
                AIMessage(
                    content="I'm sorry, I encountered an issue generating a response. "
                    "Please try again."
                )
            ]
        }
