"""Product Research Agent implementation."""

import json
from typing import Any, Dict, List

from .base import AgentResponse, AgentRole, AgentStatus, BaseAgent, Tool
from ..prompts.templates import get_agent_prompt
from ..tools.mock_tools import MockProductSearchTool


class ProductResearchAgent(BaseAgent):
    """Agent responsible for searching and finding products."""

    def __init__(self, tools: List[Tool] | None = None) -> None:
        """Initialize Product Research Agent."""
        # Use provided tools or default to mock
        if tools is None:
            tools = [MockProductSearchTool()]

        super().__init__(
            role=AgentRole.PRODUCT_RESEARCH,
            name="Product Researcher",
            description="Searches for products matching user criteria",
            system_prompt=get_agent_prompt("product_research"),
            tools=tools,
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process search criteria to find matching products.

        Args:
            input_data: Dictionary containing:
                - shopping_criteria: Structured needs from Needs Analysis Agent
                - max_results: Maximum number of products to return (optional)

        Returns:
            AgentResponse with list of matching products
        """
        await self.validate_input(input_data)
        self.set_status(AgentStatus.PROCESSING)

        try:
            criteria = input_data.get("shopping_criteria", {})
            max_results = input_data.get("max_results", 10)

            self.logger.info("searching_products", criteria=criteria)

            # Extract search parameters from criteria
            search_params = self._extract_search_params(criteria)

            # Execute search using tools
            search_results = await self._search_products(search_params)

            # Limit results
            products = search_results.get("products", [])[:max_results]

            # Ask Claude to analyze and structure the results
            analysis = await self._analyze_results(criteria, products)

            self.set_status(AgentStatus.COMPLETED)

            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output={
                    "products": products,
                    "result_count": len(products),
                    "search_params": search_params,
                    "analysis": analysis,
                },
                metadata={"criteria": criteria},
            )

        except Exception as e:
            self.logger.error("product_research_error", error=str(e))
            self.set_status(AgentStatus.FAILED)
            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.FAILED,
                output={},
                errors=[str(e)],
            )

    def _extract_search_params(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract search parameters from shopping criteria.

        Args:
            criteria: Shopping criteria from Needs Analysis

        Returns:
            Search parameters for product search tool
        """
        params: Dict[str, Any] = {}

        if "product_category" in criteria:
            params["category"] = criteria["product_category"]

        if "budget" in criteria:
            budget = criteria["budget"]
            if isinstance(budget, dict) and "max" in budget:
                params["max_price"] = budget["max"]
            elif isinstance(budget, (int, float)):
                params["max_price"] = budget

        if "must_have_features" in criteria:
            params["features"] = criteria["must_have_features"]

        # Default minimum rating
        params["min_rating"] = 4.0

        return params

    async def _search_products(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for products using available tools.

        Args:
            search_params: Search parameters

        Returns:
            Search results from tools
        """
        # Use the first product search tool available
        search_tool = next(
            (tool for tool in self.tools if tool.name == "product_search"),
            None,
        )

        if not search_tool:
            raise ValueError("No product search tool available")

        return await search_tool.execute(**search_params)

    async def _analyze_results(
        self, criteria: Dict[str, Any], products: List[Dict[str, Any]]
    ) -> str:
        """
        Use Claude to analyze search results.

        Args:
            criteria: Original shopping criteria
            products: Found products

        Returns:
            Analysis text from Claude
        """
        if not products:
            return "No products found matching the criteria. Consider relaxing some requirements."

        analysis_prompt = f"""
I found {len(products)} products matching the criteria.

Criteria: {json.dumps(criteria, indent=2)}

Products: {json.dumps(products, indent=2)}

Please provide a brief analysis (2-3 sentences) of these results:
- How well do they match the criteria?
- Is there good variety in price/features?
- Any notable gaps or suggestions?
"""

        messages = [{"role": "user", "content": analysis_prompt}]
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

        if "shopping_criteria" not in input_data:
            raise ValueError("Input must contain 'shopping_criteria'")

        criteria = input_data["shopping_criteria"]
        if not isinstance(criteria, dict):
            raise ValueError("Shopping criteria must be a dictionary")

        return True
