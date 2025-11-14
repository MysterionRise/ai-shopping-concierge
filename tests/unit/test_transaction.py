"""Tests for Transaction Agent."""

import pytest
from unittest.mock import AsyncMock, patch

from src.shopping_concierge.agents import TransactionAgent, AgentStatus
from tests.fixtures.mock_data import get_mock_products, get_mock_shipping_address


@pytest.mark.unit
@pytest.mark.asyncio
class TestTransactionAgent:
    """Test suite for Transaction Agent."""

    @pytest.fixture
    def agent(self) -> TransactionAgent:
        """Create agent instance."""
        return TransactionAgent()

    async def test_agent_initialization(self, agent: TransactionAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Transaction Handler"
        assert agent.role.value == "transaction"
        assert len(agent.tools) > 0

    async def test_process_prepare_order(self, agent: TransactionAgent) -> None:
        """Test preparing order summary."""
        with patch.object(
            agent,
            "_call_claude",
            return_value="Your order includes Nike shoes for $129.99 total.",
        ):
            input_data = {
                "action": "prepare",
                "products": get_mock_products()[:1],
                "shipping_address": get_mock_shipping_address(),
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert response.output["action"] == "prepare"
            assert "order_summary" in response.output
            assert response.output["requires_approval"] is True

    async def test_prepare_order_calculates_costs(
        self, agent: TransactionAgent
    ) -> None:
        """Test that order preparation calculates costs correctly."""
        with patch.object(agent, "_call_claude", return_value="Order summary"):
            products = [
                {
                    "product_id": "1",
                    "name": "Product 1",
                    "price": 100.0,
                    "quantity": 1,
                },
                {
                    "product_id": "2",
                    "name": "Product 2",
                    "price": 50.0,
                    "quantity": 2,
                },
            ]

            input_data = {
                "action": "prepare",
                "products": products,
            }

            response = await agent.process(input_data)

            summary = response.output["order_summary"]
            assert summary["subtotal"] == 200.0  # 100 + 50*2
            assert summary["tax"] == 16.0  # 8% of 200
            assert summary["shipping"] == 0.0  # Free over $50
            assert summary["total"] == 216.0

    async def test_prepare_order_includes_shipping_cost(
        self, agent: TransactionAgent
    ) -> None:
        """Test that shipping is charged for orders under $50."""
        with patch.object(agent, "_call_claude", return_value="Order summary"):
            products = [
                {
                    "product_id": "1",
                    "name": "Product 1",
                    "price": 30.0,
                    "quantity": 1,
                },
            ]

            input_data = {
                "action": "prepare",
                "products": products,
            }

            response = await agent.process(input_data)

            summary = response.output["order_summary"]
            assert summary["shipping"] == 5.99

    async def test_execute_order_without_approval(
        self, agent: TransactionAgent
    ) -> None:
        """Test that order execution requires approval."""
        input_data = {
            "action": "execute",
            "products": get_mock_products()[:1],
            "user_approved": False,
        }

        response = await agent.process(input_data)

        assert response.status == AgentStatus.COMPLETED
        assert response.output["success"] is False
        assert "requires_approval" in response.output

    async def test_execute_order_with_approval(self, agent: TransactionAgent) -> None:
        """Test executing order with user approval."""
        with patch.object(
            agent,
            "_call_claude",
            return_value="Order confirmed! Your order #12345 will arrive in 3-5 days.",
        ):
            input_data = {
                "action": "execute",
                "products": get_mock_products()[:1],
                "shipping_address": get_mock_shipping_address(),
                "payment_method": "credit_card",
                "user_approved": True,
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.COMPLETED
            assert response.output["action"] == "execute"
            assert response.output["success"] is True
            assert "order_id" in response.output
            assert "order_details" in response.output

    async def test_process_invalid_action(self, agent: TransactionAgent) -> None:
        """Test processing with invalid action."""
        input_data = {
            "action": "invalid",
            "products": get_mock_products(),
        }

        with pytest.raises(ValueError, match="Invalid action"):
            await agent.process(input_data)

    async def test_process_without_products(self, agent: TransactionAgent) -> None:
        """Test processing without products raises error."""
        input_data = {"action": "prepare"}

        with pytest.raises(ValueError, match="must contain 'products'"):
            await agent.process(input_data)

    async def test_process_empty_products(self, agent: TransactionAgent) -> None:
        """Test processing with empty products list."""
        input_data = {
            "action": "prepare",
            "products": [],
        }

        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.process(input_data)

    async def test_process_handles_error(self, agent: TransactionAgent) -> None:
        """Test handling errors during processing."""
        with patch.object(
            agent,
            "_prepare_order",
            side_effect=Exception("Processing error"),
        ):
            input_data = {
                "action": "prepare",
                "products": get_mock_products(),
            }

            response = await agent.process(input_data)

            assert response.status == AgentStatus.FAILED
            assert len(response.errors) > 0
