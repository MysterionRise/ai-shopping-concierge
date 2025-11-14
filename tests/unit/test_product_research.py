"""Tests for Product Research Agent."""

import pytest
from unittest.mock import AsyncMock, patch

from src.shopping_concierge.agents import ProductResearchAgent, AgentStatus
from src.shopping_concierge.tools import MockProductSearchTool
from tests.fixtures.mock_data import get_mock_shopping_criteria, get_mock_products


@pytest.mark.unit
@pytest.mark.asyncio
class TestProductResearchAgent:
    """Test suite for Product Research Agent."""

    @pytest.fixture
    def agent(self) -> ProductResearchAgent:
        """Create agent instance."""
        return ProductResearchAgent()

    async def test_agent_initialization(self, agent: ProductResearchAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Product Researcher"
        assert agent.role.value == "product_research"
        assert len(agent.tools) > 0

    async def test_process_valid_criteria(
        self, agent: ProductResearchAgent
    ) -> None:
        """Test processing valid shopping criteria."""
        with patch.object(
            agent,
            "_call_claude",
            return_value="The results match the criteria well with good variety.",
        ):
            input_data = {
                "shopping_criteria": get_mock_shopping_criteria(),
                "max_results": 5,
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert "products" in response.output
            assert "result_count" in response.output
            assert isinstance(response.output["products"], list)

    async def test_extract_search_params(
        self, agent: ProductResearchAgent
    ) -> None:
        """Test extracting search parameters from criteria."""
        criteria = get_mock_shopping_criteria()
        params = agent._extract_search_params(criteria)

        assert "category" in params
        assert "max_price" in params
        assert params["category"] == "running shoes"
        assert params["max_price"] == 150

    async def test_process_without_criteria(
        self, agent: ProductResearchAgent
    ) -> None:
        """Test processing without criteria raises error."""
        input_data = {}

        with pytest.raises(ValueError, match="must contain 'shopping_criteria'"):
            await agent.process(input_data)

    async def test_process_invalid_criteria_type(
        self, agent: ProductResearchAgent
    ) -> None:
        """Test processing with invalid criteria type."""
        input_data = {"shopping_criteria": "invalid"}

        with pytest.raises(ValueError, match="must be a dictionary"):
            await agent.process(input_data)

    async def test_search_products(self, agent: ProductResearchAgent) -> None:
        """Test product search execution."""
        search_params = {
            "category": "running shoes",
            "max_price": 150,
        }

        results = await agent._search_products(search_params)

        assert "success" in results
        assert "products" in results
        assert results["success"] is True

    async def test_process_limits_results(self, agent: ProductResearchAgent) -> None:
        """Test that max_results limits the output."""
        with patch.object(
            agent,
            "_call_claude",
            return_value="Good results",
        ):
            input_data = {
                "shopping_criteria": get_mock_shopping_criteria(),
                "max_results": 2,
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert len(response.output["products"]) <= 2

    async def test_analyze_results_no_products(
        self, agent: ProductResearchAgent
    ) -> None:
        """Test analyzing empty results."""
        criteria = get_mock_shopping_criteria()
        products = []

        analysis = await agent._analyze_results(criteria, products)

        assert "no products" in analysis.lower()

    async def test_process_handles_tool_error(
        self, agent: ProductResearchAgent
    ) -> None:
        """Test handling tool execution errors."""
        with patch.object(
            agent,
            "_search_products",
            side_effect=Exception("Tool error"),
        ):
            input_data = {"shopping_criteria": get_mock_shopping_criteria()}

            response = await agent.process(input_data)

            assert response.status == AgentStatus.FAILED
            assert len(response.errors) > 0
