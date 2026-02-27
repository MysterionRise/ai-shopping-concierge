"""Tests for core/llm.py — LLM factory and DemoChatModel."""

from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.llm import DemoChatModel, get_llm


class TestDemoChatModel:
    def setup_method(self):
        self.model = DemoChatModel()

    def test_llm_type(self):
        assert self.model._llm_type == "demo"

    def test_generate_returns_chat_result(self):
        messages = [HumanMessage(content="hello")]
        result = self.model._generate(messages)
        assert len(result.generations) == 1
        assert isinstance(result.generations[0].message, AIMessage)
        assert result.generations[0].message.content != ""

    @pytest.mark.asyncio
    async def test_agenerate_returns_same_as_generate(self):
        messages = [HumanMessage(content="hello")]
        sync_result = self.model._generate(messages)
        async_result = await self.model._agenerate(messages)
        assert (
            sync_result.generations[0].message.content
            == async_result.generations[0].message.content
        )

    @pytest.mark.asyncio
    async def test_astream_yields_chunks(self):
        messages = [
            SystemMessage(content="You are a beauty concierge assistant."),
            HumanMessage(content="hello"),
        ]
        chunks = []
        async for chunk in self.model._astream(messages):
            chunks.append(chunk)
        assert len(chunks) > 0
        # Reassembled content should match the full response
        full = "".join(c.message.content for c in chunks)
        assert len(full) > 0

    def test_triage_router_product_search(self):
        messages = [
            SystemMessage(content="classify the user intent"),
            HumanMessage(content="I need a moisturizer for dry skin"),
        ]
        result = self.model._generate(messages)
        assert result.generations[0].message.content == "product_search"

    def test_triage_router_ingredient_check(self):
        messages = [
            SystemMessage(content="classify the user intent"),
            HumanMessage(content="Is retinol safe for sensitive skin?"),
        ]
        result = self.model._generate(messages)
        assert result.generations[0].message.content == "ingredient_check"

    def test_triage_router_routine_advice(self):
        messages = [
            SystemMessage(content="classify the user intent"),
            HumanMessage(content="What should my morning routine be?"),
        ]
        result = self.model._generate(messages)
        assert result.generations[0].message.content == "routine_advice"

    def test_triage_router_general_chat(self):
        messages = [
            SystemMessage(content="classify the user intent"),
            HumanMessage(content="what's the weather like?"),
        ]
        result = self.model._generate(messages)
        assert result.generations[0].message.content == "general_chat"

    def test_search_intent_extractor(self):
        messages = [
            SystemMessage(content="You are a search intent extractor."),
            HumanMessage(content="I want a serum for oily skin by CeraVe"),
        ]
        result = self.model._generate(messages)
        content = result.generations[0].message.content
        assert "product_type: serum" in content
        assert "skin_type: oily" in content
        assert "Cerave" in content

    def test_search_intent_extractor_sunscreen(self):
        messages = [
            SystemMessage(content="You are a search intent extractor."),
            HumanMessage(content="looking for a sunscreen"),
        ]
        result = self.model._generate(messages)
        content = result.generations[0].message.content
        assert "sunscreen" in content
        assert "SPF" in content

    def test_search_intent_extractor_dry_skin(self):
        messages = [
            SystemMessage(content="You are a search intent extractor."),
            HumanMessage(content="I need a moisturizer for dry skin"),
        ]
        result = self.model._generate(messages)
        content = result.generations[0].message.content
        assert "skin_type: dry" in content
        assert "cream" in content

    def test_search_intent_extractor_sensitive(self):
        messages = [
            SystemMessage(content="You are a search intent extractor."),
            HumanMessage(content="a gentle cleanser for sensitive skin"),
        ]
        result = self.model._generate(messages)
        content = result.generations[0].message.content
        assert "skin_type: sensitive" in content
        assert "fragrance-free" in content

    def test_search_intent_extractor_format_detection(self):
        messages = [
            SystemMessage(content="You are a search intent extractor."),
            HumanMessage(content="I want a gel moisturizer"),
        ]
        result = self.model._generate(messages)
        content = result.generations[0].message.content
        assert "format_preference: gel" in content

    def test_safety_checker(self):
        messages = [
            SystemMessage(content="You are a safety checker."),
            HumanMessage(content="Check these products"),
        ]
        result = self.model._generate(messages)
        assert '{"results": []}' in result.generations[0].message.content

    def test_conversational_reply_greeting(self):
        messages = [
            SystemMessage(content="You are a beauty concierge."),
            HumanMessage(content="hello"),
        ]
        result = self.model._generate(messages)
        assert "Beauty Concierge" in result.generations[0].message.content

    def test_conversational_reply_thanks(self):
        messages = [
            SystemMessage(content="You are a beauty concierge."),
            HumanMessage(content="thanks for the help"),
        ]
        result = self.model._generate(messages)
        assert "welcome" in result.generations[0].message.content.lower()

    def test_conversational_reply_routine(self):
        messages = [
            SystemMessage(content="You are a beauty concierge."),
            HumanMessage(content="what should my skincare routine look like?"),
        ]
        result = self.model._generate(messages)
        assert "routine" in result.generations[0].message.content.lower()

    def test_conversational_reply_memory_acknowledgment(self):
        messages = [
            SystemMessage(content="You are a beauty concierge. Memory acknowledgments: noted."),
            HumanMessage(content="hello"),
        ]
        result = self.model._generate(messages)
        assert "updated my notes" in result.generations[0].message.content

    def test_conversational_reply_memory_query_with_memories(self):
        messages = [
            SystemMessage(
                content="You are a beauty concierge. The user wants to know what you remember. "
                "Stored memories: skin type is oily."
            ),
            HumanMessage(content="what do you know about me?"),
        ]
        result = self.model._generate(messages)
        assert "remember" in result.generations[0].message.content.lower()

    def test_conversational_reply_memory_query_no_memories(self):
        messages = [
            SystemMessage(
                content="You are a beauty concierge. The user wants to know what you remember."
            ),
            HumanMessage(content="what do you know about me?"),
        ]
        result = self.model._generate(messages)
        content = result.generations[0].message.content.lower()
        assert "don't have" in content or "no stored" in content.replace("'", "'")

    def test_conversational_reply_ingredient_with_violations(self):
        messages = [
            SystemMessage(content="You are a beauty concierge. safety violations found."),
            HumanMessage(content="check ingredient safety for paraben"),
        ]
        result = self.model._generate(messages)
        assert "concern" in result.generations[0].message.content.lower()

    def test_conversational_reply_safe_products(self):
        messages = [
            SystemMessage(content="You are a beauty concierge. safe products found."),
            HumanMessage(content="find me a serum"),
        ]
        result = self.model._generate(messages)
        assert "safe" in result.generations[0].message.content.lower()

    def test_conversational_reply_default(self):
        messages = [
            SystemMessage(content="You are a beauty concierge."),
            HumanMessage(content="something random"),
        ]
        result = self.model._generate(messages)
        assert "help" in result.generations[0].message.content.lower()

    def test_default_response_no_system(self):
        messages = [HumanMessage(content="hello")]
        result = self.model._generate(messages)
        assert "beauty concierge" in result.generations[0].message.content.lower()

    def test_handles_non_string_content(self):
        """Messages with non-string content should be handled gracefully."""
        msg = HumanMessage(content=[{"type": "text", "text": "hello"}])
        result = self.model._generate([msg])
        # Should not crash, returns default response
        assert result.generations[0].message.content != ""


class TestGetLLM:
    @patch("app.core.llm.settings")
    def test_returns_demo_model_when_no_key(self, mock_settings):
        mock_settings.openrouter_api_key = ""
        model = get_llm()
        assert isinstance(model, DemoChatModel)

    @patch("app.core.llm.settings")
    def test_returns_demo_model_for_placeholder_key(self, mock_settings):
        mock_settings.openrouter_api_key = "sk-or-v1-your-key-here"
        model = get_llm()
        assert isinstance(model, DemoChatModel)

    @patch("app.core.llm.settings")
    def test_returns_openai_model_with_real_key(self, mock_settings):
        mock_settings.openrouter_api_key = "sk-or-v1-real-key-12345"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.openrouter_model = "anthropic/claude-sonnet-4-20250514"
        model = get_llm()
        assert type(model).__name__ == "ChatOpenAI"

    @patch("app.core.llm.settings")
    def test_passes_kwargs_to_openai(self, mock_settings):
        mock_settings.openrouter_api_key = "sk-or-v1-real-key-12345"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.openrouter_model = "anthropic/claude-sonnet-4-20250514"
        model = get_llm(temperature=0)
        assert model.temperature == 0
