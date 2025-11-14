"""Tests for Deal-Finding Agent."""

import pytest
from unittest.mock import AsyncMock, patch

from src.shopping_concierge.agents import DealFindingAgent, AgentStatus
from tests.fixtures.mock_data import get_mock_products


@pytest.mark.unit
@pytest.mark.asyncio
class TestDealFindingAgent:
    """Test suite for Deal-Finding Agent."""

    @pytest.fixture
    def agent(self) -> DealFindingAgent:
        """Create agent instance."""
        return DealFindingAgent()

    async def test_agent_initialization(self, agent: DealFindingAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Deal Finder"
        assert agent.role.value == "deal_finding"
        assert len(agent.tools) > 0

    async def test_process_valid_products(self, agent: DealFindingAgent) -> None:
        """Test processing valid product list."""
        with patch.object(
            agent,
            "_call_claude",
            return_value="Great deals available with 10-15% savings possible.",
        ):
            input_data = {"products": get_mock_products()}

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert "deals" in response.output
            assert "summary" in response.output
            assert "best_deal" in response.output

    async def test_find_product_deals(self, agent: DealFindingAgent) -> None:
        """Test finding deals for a single product."""
        product = get_mock_products()[0]

        deal_info = await agent._find_product_deals(product)

        assert "product_id" in deal_info
        assert "current_price" in deal_info
        assert "coupons" in deal_info
        assert "price_history" in deal_info

    async def test_calculate_savings_with_percentage(
        self, agent: DealFindingAgent
    ) -> None:
        """Test calculating savings with percentage coupon."""
        coupons = ["SAVE15 - 15% off"]
        current_price = 100.0

        savings = agent._calculate_savings(current_price, coupons)

        assert savings["amount"] == 15.0
        assert savings["percentage"] == 15.0
        assert savings["final_price"] == 85.0

    async def test_calculate_savings_with_dollar_amount(
        self, agent: DealFindingAgent
    ) -> None:
        """Test calculating savings with dollar amount coupon."""
        coupons = ["SAVE20 - $20 off"]
        current_price = 100.0

        savings = agent._calculate_savings(current_price, coupons)

        assert savings["amount"] == 20.0
        assert savings["final_price"] == 80.0

    async def test_calculate_savings_no_coupons(
        self, agent: DealFindingAgent
    ) -> None:
        """Test calculating savings with no coupons."""
        coupons = []
        current_price = 100.0

        savings = agent._calculate_savings(current_price, coupons)

        assert savings["amount"] == 0
        assert "No savings" in savings["description"]

    async def test_identify_best_deal(self, agent: DealFindingAgent) -> None:
        """Test identifying best deal from multiple products."""
        deals = [
            {
                "product_id": "1",
                "savings_potential": {"amount": 10.0},
            },
            {
                "product_id": "2",
                "savings_potential": {"amount": 25.0},
            },
            {
                "product_id": "3",
                "savings_potential": {"amount": 15.0},
            },
        ]

        best = agent._identify_best_deal(deals)

        assert best["product_id"] == "2"  # Highest savings

    async def test_process_without_products(self, agent: DealFindingAgent) -> None:
        """Test processing without products raises error."""
        input_data = {}

        with pytest.raises(ValueError, match="must contain 'products'"):
            await agent.process(input_data)

    async def test_process_invalid_products_type(
        self, agent: DealFindingAgent
    ) -> None:
        """Test processing with invalid products type."""
        input_data = {"products": "invalid"}

        with pytest.raises(ValueError, match="must be a list"):
            await agent.process(input_data)

    async def test_process_handles_error(self, agent: DealFindingAgent) -> None:
        """Test handling errors during processing."""
        with patch.object(
            agent,
            "_find_product_deals",
            side_effect=Exception("Tool error"),
        ):
            input_data = {"products": get_mock_products()}

            response = await agent.process(input_data)

            assert response.status == AgentStatus.FAILED
            assert len(response.errors) > 0
