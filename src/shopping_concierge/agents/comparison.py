"""Comparison & Recommendation Agent implementation."""

import json
from typing import Any, Dict, List

from ..prompts.templates import get_agent_prompt
from .base import AgentResponse, AgentRole, AgentStatus, BaseAgent


class ComparisonAgent(BaseAgent):
    """Agent responsible for comparing products and making recommendations."""

    def __init__(self) -> None:
        """Initialize Comparison Agent."""
        super().__init__(
            role=AgentRole.COMPARISON,
            name="Product Comparator",
            description="Compares products and provides recommendations",
            system_prompt=get_agent_prompt("comparison"),
            tools=[],
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process products to generate comparisons and recommendations.

        Args:
            input_data: Dictionary containing:
                - products: List of products to compare
                - shopping_criteria: Original user criteria
                - top_n: Number of top recommendations (default: 3)

        Returns:
            AgentResponse with ranked recommendations
        """
        await self.validate_input(input_data)
        self.set_status(AgentStatus.PROCESSING)

        try:
            products = input_data.get("products", [])
            criteria = input_data.get("shopping_criteria", {})
            top_n = input_data.get("top_n", 3)

            self.logger.info("comparing_products", product_count=len(products))

            if not products:
                return AgentResponse(
                    agent_role=self.role,
                    status=AgentStatus.COMPLETED,
                    output={
                        "message": "No products to compare",
                        "recommendations": [],
                    },
                )

            # Generate comparison and recommendations using Claude
            comparison_result = await self._compare_and_recommend(products, criteria, top_n)

            self.set_status(AgentStatus.COMPLETED)

            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=comparison_result,
                metadata={
                    "product_count": len(products),
                    "criteria": criteria,
                },
            )

        except Exception as e:
            self.logger.error("comparison_error", error=str(e))
            self.set_status(AgentStatus.FAILED)
            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.FAILED,
                output={},
                errors=[str(e)],
            )

    async def _compare_and_recommend(
        self, products: List[Dict[str, Any]], criteria: Dict[str, Any], top_n: int
    ) -> Dict[str, Any]:
        """
        Use Claude to compare products and generate recommendations.

        Args:
            products: List of products to compare
            criteria: Shopping criteria
            top_n: Number of recommendations to return

        Returns:
            Comparison and recommendation results
        """
        prompt = f"""
I need you to compare these products and provide recommendations based on the user's criteria.

User Criteria:
{json.dumps(criteria, indent=2)}

Products to Compare:
{json.dumps(products, indent=2)}

Please analyze these products and respond with a JSON object containing:

{{
    "ranked_products": [
        {{
            "product_id": "id",
            "name": "product name",
            "rank": 1,
            "score": 9.2,
            "rationale": "Why this is recommended",
            "pros": ["pro1", "pro2"],
            "cons": ["con1", "con2"],
            "best_for": "Type of user this is best for"
        }}
    ],
    "comparison_summary": "Brief 2-3 sentence summary comparing top options",
    "top_recommendation": {{
        "product_id": "id",
        "name": "name",
        "justification": "Detailed explanation of why this is the #1 pick"
    }},
    "alternatives": [
        {{
            "product_id": "id",
            "name": "name",
            "when_better": "When this might be a better choice"
        }}
    ]
}}

Rank the top {top_n} products. Consider:
- Value for money (price vs features)
- How well they match the criteria
- Quality indicators (ratings, reviews)
- Feature completeness
- Brand reputation

Provide ONLY the JSON object, no additional text.
"""

        messages = [{"role": "user", "content": prompt}]
        response = await self._call_claude(messages, max_tokens=2000)

        # Parse JSON from response
        try:
            # Extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                # Fallback: create basic ranking by rating
                return self._create_fallback_ranking(products, top_n)

        except json.JSONDecodeError:
            self.logger.warning("failed_to_parse_comparison_json")
            return self._create_fallback_ranking(products, top_n)

    def _create_fallback_ranking(
        self, products: List[Dict[str, Any]], top_n: int
    ) -> Dict[str, Any]:
        """
        Create a simple fallback ranking based on rating and price.

        Args:
            products: Products to rank
            top_n: Number of products to include

        Returns:
            Basic ranking structure
        """
        # Sort by rating (descending) and price (ascending)
        sorted_products = sorted(
            products,
            key=lambda p: (-p.get("rating", 0), p.get("price", float("inf"))),
        )

        ranked = []
        for i, product in enumerate(sorted_products[:top_n], 1):
            ranked.append(
                {
                    "product_id": product.get("product_id"),
                    "name": product.get("name"),
                    "rank": i,
                    "score": product.get("rating", 0) * 2,  # Scale to 10
                    "rationale": (
                        f"High rating ({product.get('rating')}) " f"at ${product.get('price')}"
                    ),
                    "pros": product.get("features", [])[:3],
                    "cons": ["Limited analysis available"],
                    "best_for": "Users prioritizing rating and value",
                }
            )

        top = ranked[0] if ranked else {}

        return {
            "ranked_products": ranked,
            "comparison_summary": f"Ranked {len(ranked)} products by rating and price",
            "top_recommendation": {
                "product_id": top.get("product_id"),
                "name": top.get("name"),
                "justification": "Highest rated product with competitive pricing",
            },
            "alternatives": [],
        }

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
