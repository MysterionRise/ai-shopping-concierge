"""Tests for Comparison Agent."""

import pytest
from unittest.mock import patch

from src.shopping_concierge.agents import ComparisonAgent, AgentStatus
from tests.fixtures.mock_data import get_mock_products, get_mock_shopping_criteria


@pytest.mark.unit
@pytest.mark.asyncio
class TestComparisonAgent:
    """Test suite for Comparison Agent."""

    @pytest.fixture
    def agent(self) -> ComparisonAgent:
        """Create agent instance."""
        return ComparisonAgent()

    async def test_agent_initialization(self, agent: ComparisonAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Product Comparator"
        assert agent.role.value == "comparison"

    async def test_process_valid_products(self, agent: ComparisonAgent) -> None:
        """Test processing valid product list."""
        mock_comparison = {
            "ranked_products": [
                {
                    "product_id": "SHOE-RUN-001",
                    "name": "Nike Air Zoom Pegasus 40",
                    "rank": 1,
                    "score": 9.0,
                    "rationale": "Best value",
                    "pros": ["Great cushioning"],
                    "cons": ["Limited colors"],
                    "best_for": "Daily runners",
                }
            ],
            "comparison_summary": "Nike Pegasus offers best value",
            "top_recommendation": {
                "product_id": "SHOE-RUN-001",
                "justification": "Best overall",
            },
            "alternatives": [],
        }

        with patch.object(
            agent,
            "_call_claude",
            return_value=f"{mock_comparison}",
        ):
            with patch.object(
                agent,
                "_compare_and_recommend",
                return_value=mock_comparison,
            ):
                input_data = {
                    "products": get_mock_products(),
                    "shopping_criteria": get_mock_shopping_criteria(),
                    "top_n": 3,
                }

                response = await agent.process(input_data)

                assert response.status == AgentStatus.COMPLETED
                assert "ranked_products" in response.output
                assert "comparison_summary" in response.output
                assert "top_recommendation" in response.output

    async def test_process_empty_products(self, agent: ComparisonAgent) -> None:
        """Test processing empty product list."""
        input_data = {
            "products": [],
            "shopping_criteria": get_mock_shopping_criteria(),
        }

        response = await agent.process(input_data)

        assert response.status == AgentStatus.COMPLETED
        assert "message" in response.output

    async def test_process_without_products(self, agent: ComparisonAgent) -> None:
        """Test processing without products raises error."""
        input_data = {"shopping_criteria": get_mock_shopping_criteria()}

        with pytest.raises(ValueError, match="must contain 'products'"):
            await agent.process(input_data)

    async def test_process_invalid_products_type(
        self, agent: ComparisonAgent
    ) -> None:
        """Test processing with invalid products type."""
        input_data = {"products": "invalid"}

        with pytest.raises(ValueError, match="must be a list"):
            await agent.process(input_data)

    async def test_create_fallback_ranking(self, agent: ComparisonAgent) -> None:
        """Test fallback ranking creation."""
        products = get_mock_products()
        result = agent._create_fallback_ranking(products, 2)

        assert "ranked_products" in result
        assert len(result["ranked_products"]) <= 2
        assert "top_recommendation" in result

    async def test_fallback_ranking_sorts_correctly(
        self, agent: ComparisonAgent
    ) -> None:
        """Test that fallback ranking sorts by rating and price."""
        products = [
            {"product_id": "1", "name": "Low rating", "rating": 3.0, "price": 50.0},
            {"product_id": "2", "name": "High rating", "rating": 4.8, "price": 100.0},
            {"product_id": "3", "name": "Mid rating", "rating": 4.0, "price": 75.0},
        ]

        result = agent._create_fallback_ranking(products, 3)
        ranked = result["ranked_products"]

        # Should be sorted by rating (descending)
        assert ranked[0]["product_id"] == "2"  # 4.8 rating
        assert ranked[0]["rank"] == 1

    async def test_process_handles_claude_error(self, agent: ComparisonAgent) -> None:
        """Test handling Claude API errors."""
        with patch.object(
            agent,
            "_compare_and_recommend",
            side_effect=Exception("API Error"),
        ):
            input_data = {
                "products": get_mock_products(),
                "shopping_criteria": get_mock_shopping_criteria(),
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.FAILED
            assert len(response.errors) > 0
