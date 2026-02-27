import asyncio
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
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

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Yield response token-by-token to simulate real LLM streaming."""
        full_response = self._pick_response(messages)
        words = [w for w in full_response.split(" ") if w]
        last_idx = len(words) - 1
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            is_last = i == last_idx
            msg = AIMessageChunk(content=token, chunk_position="last" if is_last else None)
            chunk = ChatGenerationChunk(message=msg)
            if run_manager:
                await run_manager.on_llm_new_token(token, chunk=chunk)
            yield chunk
            if not is_last:
                await asyncio.sleep(0.025)

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
            if any(
                w in user
                for w in [
                    "remember",
                    "know about me",
                    "what do you know",
                    "my profile",
                    "my data",
                    "my preferences",
                    "my memories",
                ]
            ):
                return "memory_query"
            return "general_chat"

        # Search intent extractor
        if "search intent extractor" in system:
            product_type = "moisturizer"
            properties = "hydrating"
            skin_type = "unknown"
            brand_preference = "unknown"
            format_preference = "unknown"
            if "serum" in user:
                product_type = "serum"
                format_preference = "serum"
            elif "cleanser" in user:
                product_type = "cleanser"
                format_preference = "foam"
            elif "sunscreen" in user:
                product_type = "sunscreen"
                properties = "SPF 50, lightweight"
                format_preference = "lotion"
            if "oily" in user:
                skin_type = "oily"
                properties = "oil-free, lightweight"
            elif "dry" in user:
                skin_type = "dry"
                properties = "rich, hydrating"
                format_preference = "cream"
            elif "sensitive" in user:
                skin_type = "sensitive"
                properties = "fragrance-free, gentle"
            # Detect brand mentions
            for brand in [
                "cerave",
                "la roche-posay",
                "the ordinary",
                "neutrogena",
                "cetaphil",
            ]:
                if brand in user:
                    brand_preference = brand.title()
                    break
            # Detect format mentions
            for fmt in ["cream", "gel", "oil", "lotion", "foam", "mist", "balm"]:
                if fmt in user:
                    format_preference = fmt
                    break
            return (
                f"product_type: {product_type}\n"
                f"properties: {properties}\n"
                f"skin_type: {skin_type}\n"
                f"brand_preference: {brand_preference}\n"
                f"format_preference: {format_preference}"
            )

        # Safety checker — return structured JSON
        if "safety checker" in system:
            return '{"results": []}'

        # Response synthesizer (main conversational reply)
        if "beauty" in system and "concierge" in system:
            return self._conversational_reply(user, system)

        return "Hello! I'm your AI beauty concierge. How can I help you today?"

    def _conversational_reply(self, user: str, system: str) -> str:
        # Memory acknowledgments — prepend if present in context
        memory_prefix = ""
        if "memory acknowledgments" in system:
            memory_prefix = (
                "I've updated my notes about your preferences. "
                "I'll keep that in mind for future recommendations.\n\n"
            )

        if any(w in user for w in ["hi", "hello", "hey"]):
            return memory_prefix + (
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

        # Memory query — user asks what the assistant knows about them
        if "wants to know what you remember" in system:
            if "stored memories" in system:
                return (
                    "Here's what I remember about you:\n\n"
                    "I have your skin profile, preferences, and any allergies you've shared "
                    "on file. This helps me give you personalized recommendations and "
                    "avoid suggesting products with ingredients you're sensitive to.\n\n"
                    "You can manage or delete any of these memories from your Profile page. "
                    "Is there anything you'd like to update?"
                )
            return (
                "I don't have any stored memories about you yet! As we chat, I'll learn "
                "your skin type, concerns, and preferences to give better recommendations.\n\n"
                "Want to get started? Tell me about your skin type and any allergies or "
                "sensitivities you have."
            )

        # Ingredient check — user asks about specific ingredients
        if any(
            w in user
            for w in ["ingredient", "safe", "contain", "paraben", "retinol", "niacinamide"]
        ):
            if "safety violations" in system:
                return memory_prefix + (
                    "I checked the ingredients and found some concerns based on your profile. "
                    "Some of these ingredients may not be compatible with your sensitivities.\n\n"
                    "I've flagged the specific ingredients of concern. Would you like me to "
                    "suggest alternative products with safer ingredient profiles?"
                )
            return memory_prefix + (
                "Great question about ingredients! Here's what I can tell you:\n\n"
                "When evaluating ingredients, I check for potential allergens, irritants, "
                "and how they interact with your skin type. I also look for known "
                "ingredient interactions that could cause sensitivity.\n\n"
                "Would you like me to check a specific product's ingredient list, "
                "or do you want to know more about a particular ingredient?"
            )

        if "safe products found" in system:
            # Vary response based on original query terms
            if "serum" in user:
                return memory_prefix + (
                    "I found some great serums that are safe for your skin! "
                    "Serums are excellent for delivering concentrated active ingredients. "
                    "Each has been checked against your allergy profile. "
                    "Would you like more details about any of these?"
                )
            if "cleanser" in user:
                return memory_prefix + (
                    "Here are some cleansers that match your needs and are safe "
                    "for your skin! A good cleanser is the foundation of any routine. "
                    "Each has been verified against your sensitivities. "
                    "Want to know more about any of these?"
                )
            if "sunscreen" in user:
                return memory_prefix + (
                    "I found some sunscreens that work for your skin type! "
                    "Sun protection is essential — these are all safe for your profile. "
                    "Would you like details on any of these, or should I narrow down further?"
                )
            return memory_prefix + (
                "Great news! I found some products that match your needs and are safe "
                "for your skin profile. Here are my top recommendations:\n\n"
                "Each product has been checked against your allergy profile and skin type. "
                "Would you like more details about any of these, or shall I refine the search?"
            )
        if "safety violations" in system:
            return memory_prefix + (
                "I found some products but had to filter out a few that contain "
                "ingredients you're sensitive to. Your safety is my top priority!\n\n"
                "I've flagged the problematic products and can show you safe alternatives instead. "
                "Would you like me to search for similar products without those ingredients?"
            )
        if any(w in user for w in ["routine", "regimen"]):
            return memory_prefix + (
                "Here's a recommended skincare routine for you:\n\n"
                "**Morning:**\n1. Gentle cleanser\n2. Toner\n3. Serum (vitamin C)\n"
                "4. Moisturizer\n5. Sunscreen (SPF 30+)\n\n"
                "**Evening:**\n1. Double cleanse (oil + water-based)\n2. Exfoliant (2-3x/week)\n"
                "3. Treatment serum\n4. Night cream\n\n"
                "Want me to recommend specific products for any of these steps?"
            )
        return memory_prefix + (
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
