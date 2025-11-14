"""Tests for Needs Analysis Agent."""

import pytest
from unittest.mock import AsyncMock, patch

from src.shopping_concierge.agents import NeedsAnalysisAgent, AgentStatus
from tests.fixtures.mock_data import (
    get_mock_user_message,
    get_mock_conversation_history,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestNeedsAnalysisAgent:
    """Test suite for Needs Analysis Agent."""

    @pytest.fixture
    def agent(self) -> NeedsAnalysisAgent:
        """Create agent instance."""
        return NeedsAnalysisAgent()

    async def test_agent_initialization(self, agent: NeedsAnalysisAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Needs Analyzer"
        assert agent.role.value == "needs_analysis"
        assert agent.status == AgentStatus.IDLE

    async def test_process_valid_input(
        self, agent: NeedsAnalysisAgent, mock_claude_json_response: str
    ) -> None:
        """Test processing valid user input."""
        with patch.object(
            agent,
            "_call_claude",
            return_value=mock_claude_json_response,
        ):
            input_data = {
                "user_message": get_mock_user_message(),
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert "ready" in response.output
            assert response.output["ready"] is True
            assert "product_category" in response.output

    async def test_process_with_conversation_history(
        self, agent: NeedsAnalysisAgent
    ) -> None:
        """Test processing with conversation history."""
        with patch.object(
            agent,
            "_call_claude",
            return_value='{"ready": false, "question": "What is your budget?"}',
        ):
            input_data = {
                "user_message": "I need shoes",
                "conversation_history": get_mock_conversation_history(),
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert "ready" in response.output
            assert "question" in response.output

    async def test_process_empty_message(self, agent: NeedsAnalysisAgent) -> None:
        """Test processing empty message raises error."""
        input_data = {"user_message": ""}

        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.process(input_data)

    async def test_process_missing_user_message(
        self, agent: NeedsAnalysisAgent
    ) -> None:
        """Test processing without user_message raises error."""
        input_data = {}

        with pytest.raises(ValueError, match="must contain 'user_message'"):
            await agent.process(input_data)

    async def test_process_handles_claude_error(
        self, agent: NeedsAnalysisAgent
    ) -> None:
        """Test handling Claude API errors."""
        with patch.object(
            agent,
            "_call_claude",
            side_effect=Exception("API Error"),
        ):
            input_data = {"user_message": get_mock_user_message()}

            response = await agent.process(input_data)

            assert response.status == AgentStatus.FAILED
            assert len(response.errors) > 0

    async def test_parse_response_with_json(
        self, agent: NeedsAnalysisAgent
    ) -> None:
        """Test parsing response with valid JSON."""
        response = '{"ready": true, "product_category": "shoes"}'
        result = agent._parse_response(response)

        assert result["ready"] is True
        assert result["product_category"] == "shoes"

    async def test_parse_response_without_json(
        self, agent: NeedsAnalysisAgent
    ) -> None:
        """Test parsing response without JSON."""
        response = "What type of shoes are you looking for?"
        result = agent._parse_response(response)

        assert result["ready"] is False
        assert "question" in result
