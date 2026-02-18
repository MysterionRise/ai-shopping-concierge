from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import settings


class DemoChatModel(BaseChatModel):
    """Deterministic chat model for demo/testing without an API key."""

    model_name: str = "demo"

    @property
    def _llm_type(self) -> str:
        return "demo"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self._pick_response(messages)))]
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop, run_manager=run_manager, **kwargs)

    def _pick_response(self, messages: list[BaseMessage]) -> str:
        system = ""
        user = ""
        for m in messages:
            text = m.content if isinstance(m.content, str) else ""
            if m.type == "system":
                system = text.lower()
            elif m.type == "human":
                user = text.lower()

        # Triage router
        if "classify" in system and "intent" in system:
            if any(
                w in user
                for w in [
                    "moisturizer",
                    "serum",
                    "cleanser",
                    "sunscreen",
                    "recommend",
                    "product",
                    "looking for",
                    "find me",
                ]
            ):
                return "product_search"
            if any(w in user for w in ["ingredient", "safe", "contain", "paraben", "retinol"]):
                return "ingredient_check"
            if any(
                w in user for w in ["routine", "regimen", "order", "steps", "morning", "evening"]
            ):
                return "routine_advice"
            return "general_chat"

        # Search intent extractor
        if "search intent extractor" in system:
            product_type = "moisturizer"
            properties = "hydrating"
            skin_type = "unknown"
            if "serum" in user:
                product_type = "serum"
            elif "cleanser" in user:
                product_type = "cleanser"
            elif "sunscreen" in user:
                product_type = "sunscreen"
                properties = "SPF 50, lightweight"
            if "oily" in user:
                skin_type = "oily"
                properties = "oil-free, lightweight"
            elif "dry" in user:
                skin_type = "dry"
                properties = "rich, hydrating"
            elif "sensitive" in user:
                skin_type = "sensitive"
                properties = "fragrance-free, gentle"
            return f"product_type: {product_type}\nproperties: {properties}\nskin_type: {skin_type}"

        # Safety checker
        if "safety checker" in system:
            return "All products appear SAFE based on the provided allergy list."

        # Response synthesizer (main conversational reply)
        if "beauty" in system and "concierge" in system:
            return self._conversational_reply(user, system)

        return "Hello! I'm your AI beauty concierge. How can I help you today?"

    def _conversational_reply(self, user: str, system: str) -> str:
        if any(w in user for w in ["hi", "hello", "hey"]):
            return (
                "Hello! Welcome to Beauty Concierge! I'm here to help you find the "
                "perfect skincare and beauty products for your needs. Whether you're "
                "looking for a new moisturizer, need help with a routine, or want to "
                "check ingredient safety — I've got you covered. What can I help you with today?"
            )
        if any(w in user for w in ["thank", "thanks"]):
            return (
                "You're welcome! I'm glad I could help. Feel free to come back anytime "
                "you need beauty advice or product recommendations. Take care of your skin!"
            )
        if "safe products found" in system:
            return (
                "Great news! I found some products that match your needs and are safe "
                "for your skin profile. Here are my top recommendations:\n\n"
                "Each product has been checked against your allergy profile and skin type. "
                "Would you like more details about any of these, or shall I refine the search?"
            )
        if "safety violations" in system:
            return (
                "I found some products but had to filter out a few that contain "
                "ingredients you're sensitive to. Your safety is my top priority!\n\n"
                "I've flagged the problematic products and can show you safe alternatives instead. "
                "Would you like me to search for similar products without those ingredients?"
            )
        if any(w in user for w in ["routine", "regimen"]):
            return (
                "Here's a recommended skincare routine for you:\n\n"
                "**Morning:**\n1. Gentle cleanser\n2. Toner\n3. Serum (vitamin C)\n"
                "4. Moisturizer\n5. Sunscreen (SPF 30+)\n\n"
                "**Evening:**\n1. Double cleanse (oil + water-based)\n2. Exfoliant (2-3x/week)\n"
                "3. Treatment serum\n4. Night cream\n\n"
                "Want me to recommend specific products for any of these steps?"
            )
        return (
            "I'd be happy to help with that! As your beauty concierge, I can:\n\n"
            "- **Find products** tailored to your skin type and concerns\n"
            "- **Check ingredients** for safety and compatibility\n"
            "- **Build routines** customized for your needs\n\n"
            "What would you like to explore?"
        )


def get_llm(**kwargs) -> BaseChatModel:
    if not settings.openrouter_api_key or settings.openrouter_api_key == "sk-or-v1-your-key-here":
        return DemoChatModel()
    return ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=SecretStr(settings.openrouter_api_key),
        model=settings.openrouter_model,
        temperature=kwargs.pop("temperature", 0.7),
        **kwargs,
    )
