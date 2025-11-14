"""Transaction Agent implementation."""

import json
from typing import Any, Dict, List

from .base import AgentResponse, AgentRole, AgentStatus, BaseAgent, Tool
from ..prompts.templates import get_agent_prompt
from ..tools.mock_tools import MockCheckoutTool


class TransactionAgent(BaseAgent):
    """Agent responsible for handling checkout and transaction processing."""

    def __init__(self, tools: List[Tool] | None = None) -> None:
        """Initialize Transaction Agent."""
        # Use provided tools or default to mock
        if tools is None:
            tools = [MockCheckoutTool()]

        super().__init__(
            role=AgentRole.TRANSACTION,
            name="Transaction Handler",
            description="Processes checkout and handles transactions",
            system_prompt=get_agent_prompt("transaction"),
            tools=tools,
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process transaction request.

        Args:
            input_data: Dictionary containing:
                - action: "prepare" or "execute"
                - products: Products to purchase
                - shipping_address: Shipping address (optional)
                - payment_method: Payment method (optional)
                - user_approved: Whether user has approved (for execute)

        Returns:
            AgentResponse with transaction result
        """
        await self.validate_input(input_data)
        self.set_status(AgentStatus.PROCESSING)

        try:
            action = input_data.get("action", "prepare")
            products = input_data.get("products", [])

            if action == "prepare":
                result = await self._prepare_order(input_data)
            elif action == "execute":
                result = await self._execute_order(input_data)
            else:
                raise ValueError(f"Unknown action: {action}")

            self.set_status(AgentStatus.COMPLETED)

            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=result,
                metadata={"action": action, "product_count": len(products)},
            )

        except Exception as e:
            self.logger.error("transaction_error", error=str(e))
            self.set_status(AgentStatus.FAILED)
            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.FAILED,
                output={},
                errors=[str(e)],
            )

    async def _prepare_order(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare order summary for user approval.

        Args:
            input_data: Order information

        Returns:
            Order summary
        """
        products = input_data.get("products", [])
        shipping_address = input_data.get("shipping_address", {})

        # Calculate costs
        subtotal = sum(
            p.get("price", 0) * p.get("quantity", 1)
            for p in products
        )
        tax = subtotal * 0.08  # 8% tax
        shipping = 0.0 if subtotal > 50 else 5.99
        total = subtotal + tax + shipping

        # Generate order summary with Claude
        summary_text = await self._generate_order_summary(
            products, subtotal, tax, shipping, total, shipping_address
        )

        return {
            "action": "prepare",
            "order_summary": {
                "items": [
                    {
                        "product_id": p.get("product_id"),
                        "name": p.get("name"),
                        "price": p.get("price"),
                        "quantity": p.get("quantity", 1),
                        "subtotal": p.get("price", 0) * p.get("quantity", 1),
                    }
                    for p in products
                ],
                "subtotal": round(subtotal, 2),
                "tax": round(tax, 2),
                "shipping": round(shipping, 2),
                "total": round(total, 2),
            },
            "shipping_address": shipping_address,
            "summary_text": summary_text,
            "requires_approval": True,
            "approval_message": (
                "Please review the order summary above and confirm to proceed with purchase."
            ),
        }

    async def _execute_order(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the order after user approval.

        Args:
            input_data: Order execution information

        Returns:
            Order confirmation
        """
        # Check for user approval
        if not input_data.get("user_approved", False):
            return {
                "action": "execute",
                "success": False,
                "message": "Order requires user approval before execution",
                "requires_approval": True,
            }

        self.logger.info("executing_order_with_approval")

        products = input_data.get("products", [])
        shipping_address = input_data.get("shipping_address", {})
        payment_method = input_data.get("payment_method", "credit_card")

        # Execute checkout using tool
        checkout_tool = next((t for t in self.tools if t.name == "checkout"), None)

        if not checkout_tool:
            raise ValueError("No checkout tool available")

        # Prepare products for checkout
        checkout_products = [
            {
                "product_id": p.get("product_id"),
                "name": p.get("name"),
                "price": p.get("price"),
                "quantity": p.get("quantity", 1),
            }
            for p in products
        ]

        checkout_result = await checkout_tool.execute(
            products=checkout_products,
            shipping_address=shipping_address,
            payment_method=payment_method,
        )

        # Generate confirmation message with Claude
        confirmation_text = await self._generate_confirmation(checkout_result)

        return {
            "action": "execute",
            "success": checkout_result.get("success", False),
            "order_id": checkout_result.get("order_id"),
            "order_details": checkout_result,
            "confirmation_text": confirmation_text,
            "next_steps": [
                "Check your email for order confirmation",
                f"Track your order with tracking number: {checkout_result.get('tracking_number')}",
                f"Expected delivery: {checkout_result.get('estimated_delivery')}",
            ],
        }

    async def _generate_order_summary(
        self,
        products: List[Dict[str, Any]],
        subtotal: float,
        tax: float,
        shipping: float,
        total: float,
        shipping_address: Dict[str, Any],
    ) -> str:
        """
        Generate human-readable order summary using Claude.

        Args:
            products: Products in order
            subtotal: Subtotal amount
            tax: Tax amount
            shipping: Shipping cost
            total: Total amount
            shipping_address: Shipping address

        Returns:
            Order summary text
        """
        prompt = f"""
Generate a clear, friendly order summary for the following:

Products:
{json.dumps(products, indent=2)}

Costs:
- Subtotal: ${subtotal:.2f}
- Tax: ${tax:.2f}
- Shipping: ${shipping:.2f}
- Total: ${total:.2f}

Shipping Address: {json.dumps(shipping_address, indent=2) if shipping_address else 'To be provided'}

Create a 3-4 sentence summary that:
- Lists the products being ordered
- Highlights the total cost
- Mentions shipping details
- Has a friendly, professional tone
"""

        messages = [{"role": "user", "content": prompt}]
        return await self._call_claude(messages, max_tokens=500)

    async def _generate_confirmation(
        self, checkout_result: Dict[str, Any]
    ) -> str:
        """
        Generate order confirmation message using Claude.

        Args:
            checkout_result: Result from checkout tool

        Returns:
            Confirmation message
        """
        prompt = f"""
Generate a friendly order confirmation message for:

{json.dumps(checkout_result, indent=2)}

Include:
- Confirmation that order was successful
- Order ID
- Total amount charged
- Estimated delivery
- Next steps

Keep it to 3-4 sentences, warm and professional tone.
"""

        messages = [{"role": "user", "content": prompt}]
        return await self._call_claude(messages, max_tokens=500)

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.

        Args:
            input_data: Input to validate

        Returns:
            True if valid

        Raises:
            ValueError: If input is invalid
        """
        await super().validate_input(input_data)

        action = input_data.get("action", "prepare")

        if action not in ["prepare", "execute"]:
            raise ValueError(f"Invalid action: {action}")

        if "products" not in input_data:
            raise ValueError("Input must contain 'products'")

        products = input_data["products"]
        if not isinstance(products, list):
            raise ValueError("Products must be a list")

        if not products:
            raise ValueError("Products list cannot be empty")

        # Validate execute action has approval
        if action == "execute" and not input_data.get("user_approved", False):
            # This is not an error - we'll handle it in processing
            pass

        return True
