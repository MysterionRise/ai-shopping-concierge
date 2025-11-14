"""Basic usage example of the Shopping Concierge agents."""

import asyncio
import json
import os
from typing import Any, Dict

from src.shopping_concierge.agents import (
    ComparisonAgent,
    DealFindingAgent,
    NeedsAnalysisAgent,
    ProductResearchAgent,
    TransactionAgent,
)


async def demonstrate_shopping_flow() -> None:
    """Demonstrate a complete shopping flow using all agents."""

    print("=" * 80)
    print("Personal AI Shopping Concierge - Demo")
    print("=" * 80)
    print()

    # Step 1: Needs Analysis
    print("Step 1: Understanding Your Needs")
    print("-" * 80)

    needs_agent = NeedsAnalysisAgent()
    user_request = "I need running shoes under $150 for daily training"

    print(f"User: {user_request}")
    print()

    needs_response = await needs_agent.process(
        {"user_message": user_request}
    )

    if needs_response.status.value == "completed" and needs_response.output.get("ready"):
        print("✓ Needs Analysis Complete")
        print(f"  Category: {needs_response.output.get('product_category')}")
        print(f"  Budget: ${needs_response.output.get('budget', {}).get('max')}")
        print(f"  Must-have features: {needs_response.output.get('must_have_features')}")
        print()
    else:
        print(f"Question: {needs_response.output.get('question')}")
        return

    # Step 2: Product Research
    print("Step 2: Searching for Products")
    print("-" * 80)

    research_agent = ProductResearchAgent()
    products_response = await research_agent.process(
        {
            "shopping_criteria": needs_response.output,
            "max_results": 5,
        }
    )

    if products_response.status.value == "completed":
        products = products_response.output.get("products", [])
        print(f"✓ Found {len(products)} matching products")
        for i, product in enumerate(products[:3], 1):
            print(f"  {i}. {product['name']} - ${product['price']} (⭐ {product['rating']})")
        print()

    # Step 3: Comparison and Recommendations
    print("Step 3: Comparing Options")
    print("-" * 80)

    comparison_agent = ComparisonAgent()
    comparison_response = await comparison_agent.process(
        {
            "products": products,
            "shopping_criteria": needs_response.output,
            "top_n": 3,
        }
    )

    if comparison_response.status.value == "completed":
        ranked = comparison_response.output.get("ranked_products", [])
        top_rec = comparison_response.output.get("top_recommendation", {})

        print("✓ Top Recommendations:")
        for product in ranked:
            print(f"  #{product['rank']}. {product['name']}")
            print(f"      Score: {product['score']}/10")
            print(f"      Best for: {product['best_for']}")
            print()

        print(f"🏆 Top Pick: {top_rec.get('name')}")
        print(f"   {top_rec.get('justification')}")
        print()

    # Step 4: Finding Deals
    print("Step 4: Finding Best Deals")
    print("-" * 80)

    deal_agent = DealFindingAgent()
    deals_response = await deal_agent.process(
        {
            "products": products,
            "top_product": top_rec,
        }
    )

    if deals_response.status.value == "completed":
        deals = deals_response.output.get("deals", [])
        best_deal = deals_response.output.get("best_deal", {})

        print("✓ Deal Analysis Complete")
        print(f"  Best Deal: {best_deal.get('product_name')}")
        print(f"  Current Price: ${best_deal.get('current_price')}")
        savings = best_deal.get('savings_potential', {})
        if savings.get('amount', 0) > 0:
            print(f"  Potential Savings: ${savings['amount']} ({savings['percentage']}%)")
            print(f"  Final Price: ${savings['final_price']}")
        print()

    # Step 5: Transaction (Prepare Order)
    print("Step 5: Preparing Order")
    print("-" * 80)

    transaction_agent = TransactionAgent()

    # Get top product for purchase
    top_product = products[0] if products else None
    if top_product:
        top_product["quantity"] = 1

    order_prep_response = await transaction_agent.process(
        {
            "action": "prepare",
            "products": [top_product] if top_product else [],
            "shipping_address": {
                "name": "John Doe",
                "address_line1": "123 Main St",
                "city": "Seattle",
                "state": "WA",
                "zip_code": "98101",
            },
        }
    )

    if order_prep_response.status.value == "completed":
        order_summary = order_prep_response.output.get("order_summary", {})
        print("✓ Order Summary:")
        print(f"  Item: {top_product['name']}")
        print(f"  Subtotal: ${order_summary['subtotal']}")
        print(f"  Tax: ${order_summary['tax']}")
        print(f"  Shipping: ${order_summary['shipping']}")
        print(f"  Total: ${order_summary['total']}")
        print()
        print(f"  {order_prep_response.output.get('approval_message')}")
        print()

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Note: This demo uses mock data. In production, agents would:")
    print("  - Search real product databases")
    print("  - Access live pricing and inventory")
    print("  - Process actual transactions (with approval)")
    print("  - Track orders and provide updates")


async def demonstrate_individual_agent() -> None:
    """Demonstrate using a single agent."""

    print("\nIndividual Agent Example - Needs Analysis")
    print("-" * 80)

    agent = NeedsAnalysisAgent()

    # Example 1: Clear request
    response1 = await agent.process(
        {"user_message": "I want wireless headphones for working out under $100"}
    )

    print(f"Input: 'I want wireless headphones for working out under $100'")
    print(f"Status: {response1.status.value}")

    if response1.output.get("ready"):
        print("Output (structured):")
        print(json.dumps(response1.output, indent=2))
    else:
        print(f"Agent Question: {response1.output.get('question')}")

    print()


def main() -> None:
    """Main entry point."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set in environment")
        print("Please set it in your .env file or environment variables")
        return

    # Run demos
    asyncio.run(demonstrate_shopping_flow())
    # asyncio.run(demonstrate_individual_agent())


if __name__ == "__main__":
    main()
