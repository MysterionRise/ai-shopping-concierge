"""Deal-Finding Agent implementation."""

import json
from typing import Any, Dict, List

from .base import AgentResponse, AgentRole, AgentStatus, BaseAgent, Tool
from ..prompts.templates import get_agent_prompt
from ..tools.mock_tools import MockCouponTool, MockPriceHistoryTool


class DealFindingAgent(BaseAgent):
    """Agent responsible for finding deals, discounts, and best prices."""

    def __init__(self, tools: List[Tool] | None = None) -> None:
        """Initialize Deal-Finding Agent."""
        # Use provided tools or default to mock tools
        if tools is None:
            tools = [MockCouponTool(), MockPriceHistoryTool()]

        super().__init__(
            role=AgentRole.DEAL_FINDING,
            name="Deal Finder",
            description="Finds discounts, coupons, and best prices",
            system_prompt=get_agent_prompt("deal_finding"),
            tools=tools,
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process products to find deals and best prices.

        Args:
            input_data: Dictionary containing:
                - products: List of products to find deals for
                - top_product: Optional specific product to prioritize

        Returns:
            AgentResponse with deal information
        """
        await self.validate_input(input_data)
        self.set_status(AgentStatus.PROCESSING)

        try:
            products = input_data.get("products", [])
            top_product = input_data.get("top_product")

            self.logger.info("finding_deals", product_count=len(products))

            # Find deals for each product
            deal_results = []
            for product in products:
                deal_info = await self._find_product_deals(product)
                deal_results.append(deal_info)

            # Generate summary and recommendations using Claude
            summary = await self._generate_deal_summary(deal_results, top_product)

            self.set_status(AgentStatus.COMPLETED)

            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output={
                    "deals": deal_results,
                    "summary": summary,
                    "best_deal": self._identify_best_deal(deal_results),
                },
                metadata={"product_count": len(products)},
            )

        except Exception as e:
            self.logger.error("deal_finding_error", error=str(e))
            self.set_status(AgentStatus.FAILED)
            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.FAILED,
                output={},
                errors=[str(e)],
            )

    async def _find_product_deals(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find deals for a specific product.

        Args:
            product: Product to find deals for

        Returns:
            Deal information for the product
        """
        product_id = product.get("product_id")
        brand = product.get("brand")
        current_price = product.get("price")

        # Find coupons
        coupon_tool = next((t for t in self.tools if t.name == "coupon_search"), None)
        coupons_result = {}
        if coupon_tool:
            coupons_result = await coupon_tool.execute(
                brand=brand, product_id=product_id
            )

        # Get price history
        price_tool = next((t for t in self.tools if t.name == "price_history"), None)
        price_history = {}
        if price_tool:
            price_history = await price_tool.execute(
                product_id=product_id, current_price=current_price
            )

        return {
            "product_id": product_id,
            "product_name": product.get("name"),
            "current_price": current_price,
            "original_price": product.get("original_price", current_price),
            "coupons": coupons_result.get("coupons", []),
            "best_coupon": coupons_result.get("best_deal"),
            "price_history": price_history,
            "is_good_deal": price_history.get("is_good_deal", False),
            "savings_potential": self._calculate_savings(
                current_price, coupons_result.get("coupons", [])
            ),
        }

    def _calculate_savings(
        self, current_price: float, coupons: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate potential savings from coupons.

        Args:
            current_price: Current product price
            coupons: List of available coupons

        Returns:
            Savings calculation
        """
        if not coupons or not current_price:
            return {"amount": 0, "percentage": 0, "description": "No savings available"}

        # Parse coupon percentages (simplified)
        max_discount = 0
        best_coupon = ""

        for coupon in coupons:
            # Look for percentage discounts (e.g., "15%")
            if "%" in coupon:
                try:
                    pct = float(coupon.split("%")[0].split()[-1])
                    if pct > max_discount:
                        max_discount = pct
                        best_coupon = coupon
                except (ValueError, IndexError):
                    pass
            # Look for dollar amounts (e.g., "$20 off")
            elif "$" in coupon:
                try:
                    amount = float(coupon.split("$")[1].split()[0])
                    pct_equiv = (amount / current_price) * 100
                    if pct_equiv > max_discount:
                        max_discount = pct_equiv
                        best_coupon = coupon
                except (ValueError, IndexError):
                    pass

        savings_amount = current_price * (max_discount / 100)

        return {
            "amount": round(savings_amount, 2),
            "percentage": round(max_discount, 1),
            "description": best_coupon,
            "final_price": round(current_price - savings_amount, 2),
        }

    async def _generate_deal_summary(
        self, deals: List[Dict[str, Any]], top_product: Dict[str, Any] | None
    ) -> str:
        """
        Generate a summary of deal findings using Claude.

        Args:
            deals: Deal information for products
            top_product: Top recommended product

        Returns:
            Summary text
        """
        prompt = f"""
Analyze these deal findings and provide a concise summary (3-4 sentences):

Deals: {json.dumps(deals, indent=2)}

Top Recommended Product: {json.dumps(top_product, indent=2) if top_product else 'None'}

Focus on:
- Best overall deal/savings opportunity
- Whether now is a good time to buy
- Any notable discounts or coupons
- Price trend insights
"""

        messages = [{"role": "user", "content": prompt}]
        return await self._call_claude(messages, max_tokens=500)

    def _identify_best_deal(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify the best overall deal.

        Args:
            deals: List of deal information

        Returns:
            Best deal information
        """
        if not deals:
            return {}

        # Sort by savings amount
        sorted_deals = sorted(
            deals,
            key=lambda d: d.get("savings_potential", {}).get("amount", 0),
            reverse=True,
        )

        return sorted_deals[0] if sorted_deals else {}

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

        if "products" not in input_data:
            raise ValueError("Input must contain 'products'")

        products = input_data["products"]
        if not isinstance(products, list):
            raise ValueError("Products must be a list")

        return True
