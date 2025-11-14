"""Mock tools for testing agents without real API integrations."""

import asyncio
import json
import random
from typing import Any, Dict, List, Optional

from ..agents.base import Tool


class MockProductSearchTool(Tool):
    """Mock tool for searching products."""

    def __init__(self) -> None:
        """Initialize mock product search tool."""
        super().__init__(
            name="product_search",
            description="Search for products based on criteria",
        )
        self._mock_products = self._generate_mock_products()

    def _generate_mock_products(self) -> List[Dict[str, Any]]:
        """Generate mock product data."""
        products = [
            {
                "product_id": "SHOE-RUN-001",
                "name": "Nike Air Zoom Pegasus 40",
                "category": "running shoes",
                "description": "Responsive cushioning for everyday running",
                "price": 129.99,
                "original_price": 140.00,
                "rating": 4.5,
                "review_count": 1243,
                "features": [
                    "React foam midsole",
                    "Breathable mesh upper",
                    "Rubber outsole",
                    "Zoom Air units",
                ],
                "availability": "in_stock",
                "brand": "Nike",
                "url": "https://example.com/products/nike-pegasus-40",
                "image_url": "https://example.com/images/nike-pegasus-40.jpg",
            },
            {
                "product_id": "SHOE-RUN-002",
                "name": "Adidas Ultraboost 23",
                "category": "running shoes",
                "description": "Energy-returning running shoes with Boost cushioning",
                "price": 189.99,
                "original_price": 189.99,
                "rating": 4.7,
                "review_count": 892,
                "features": [
                    "Boost midsole technology",
                    "Primeknit upper",
                    "Continental rubber outsole",
                    "Torsion system",
                ],
                "availability": "in_stock",
                "brand": "Adidas",
                "url": "https://example.com/products/adidas-ultraboost-23",
                "image_url": "https://example.com/images/adidas-ultraboost-23.jpg",
            },
            {
                "product_id": "SHOE-RUN-003",
                "name": "New Balance Fresh Foam 1080v12",
                "category": "running shoes",
                "description": "Plush cushioning for long distance comfort",
                "price": 159.99,
                "original_price": 159.99,
                "rating": 4.6,
                "review_count": 567,
                "features": [
                    "Fresh Foam X midsole",
                    "Hypoknit upper",
                    "Blown rubber outsole",
                    "Wide sizes available",
                ],
                "availability": "in_stock",
                "brand": "New Balance",
                "url": "https://example.com/products/nb-1080v12",
                "image_url": "https://example.com/images/nb-1080v12.jpg",
            },
            {
                "product_id": "SHOE-RUN-004",
                "name": "Asics Gel-Nimbus 25",
                "category": "running shoes",
                "description": "Maximum cushioning for neutral runners",
                "price": 169.99,
                "original_price": 169.99,
                "rating": 4.4,
                "review_count": 734,
                "features": [
                    "FF Blast+ cushioning",
                    "PureGEL technology",
                    "Engineered knit upper",
                    "AHAR+ outsole",
                ],
                "availability": "in_stock",
                "brand": "Asics",
                "url": "https://example.com/products/asics-nimbus-25",
                "image_url": "https://example.com/images/asics-nimbus-25.jpg",
            },
            {
                "product_id": "SHOE-RUN-005",
                "name": "Saucony Kinvara 14",
                "category": "running shoes",
                "description": "Lightweight and responsive for speed training",
                "price": 119.99,
                "original_price": 129.99,
                "rating": 4.3,
                "review_count": 423,
                "features": [
                    "PWRRUN cushioning",
                    "Minimal design",
                    "4mm drop",
                    "Breathable mesh",
                ],
                "availability": "in_stock",
                "brand": "Saucony",
                "url": "https://example.com/products/saucony-kinvara-14",
                "image_url": "https://example.com/images/saucony-kinvara-14.jpg",
            },
        ]
        return products

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute product search.

        Args:
            category: Product category to search
            max_price: Maximum price filter
            min_rating: Minimum rating filter
            features: Required features

        Returns:
            Dictionary with search results
        """
        # Simulate API delay
        await asyncio.sleep(0.5)

        category = kwargs.get("category", "").lower()
        max_price = kwargs.get("max_price", float("inf"))
        min_rating = kwargs.get("min_rating", 0.0)
        required_features = kwargs.get("features", [])

        # Filter products
        results = []
        for product in self._mock_products:
            # Category filter
            if category and category not in product["category"].lower():
                continue

            # Price filter
            if product["price"] > max_price:
                continue

            # Rating filter
            if product["rating"] < min_rating:
                continue

            # Feature filter (at least one required feature must match)
            if required_features:
                product_features_lower = [f.lower() for f in product["features"]]
                has_required = any(
                    feat.lower() in " ".join(product_features_lower)
                    for feat in required_features
                )
                if not has_required:
                    continue

            results.append(product)

        return {
            "success": True,
            "query": kwargs,
            "result_count": len(results),
            "products": results,
        }


class MockCouponTool(Tool):
    """Mock tool for finding coupons and deals."""

    def __init__(self) -> None:
        """Initialize mock coupon tool."""
        super().__init__(
            name="coupon_search",
            description="Search for coupons and promotional deals",
        )
        self._mock_coupons = {
            "Nike": ["NIKE10 - 10% off", "FREESHIP - Free shipping over $50"],
            "Adidas": ["WELCOME15 - 15% off first order", "SAVE20 - $20 off $100+"],
            "New Balance": ["NB10 - 10% off", "LOYALTY - 5% rewards points"],
            "Asics": ["ASICS15 - 15% off sale items"],
            "Saucony": ["RUNNER10 - 10% off running shoes"],
        }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute coupon search.

        Args:
            brand: Brand to search coupons for
            product_id: Specific product to find deals for

        Returns:
            Dictionary with available coupons
        """
        # Simulate API delay
        await asyncio.sleep(0.3)

        brand = kwargs.get("brand", "")
        product_id = kwargs.get("product_id", "")

        coupons = self._mock_coupons.get(brand, [])

        # Add random limited-time deal
        if random.random() > 0.5:
            coupons.append("FLASH20 - 20% off (expires in 2 hours)")

        return {
            "success": True,
            "brand": brand,
            "product_id": product_id,
            "coupons": coupons,
            "best_deal": coupons[0] if coupons else None,
        }


class MockPriceHistoryTool(Tool):
    """Mock tool for checking price history."""

    def __init__(self) -> None:
        """Initialize mock price history tool."""
        super().__init__(
            name="price_history",
            description="Get price history and trends for products",
        )

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute price history lookup.

        Args:
            product_id: Product to get price history for

        Returns:
            Dictionary with price history data
        """
        # Simulate API delay
        await asyncio.sleep(0.3)

        product_id = kwargs.get("product_id", "")

        # Generate mock price history
        current_price = kwargs.get("current_price", 100.0)
        lowest_price = current_price * 0.85
        highest_price = current_price * 1.15
        average_price = current_price * 0.95

        return {
            "success": True,
            "product_id": product_id,
            "current_price": current_price,
            "lowest_price": lowest_price,
            "highest_price": highest_price,
            "average_price": average_price,
            "price_trend": random.choice(["decreasing", "stable", "increasing"]),
            "is_good_deal": current_price < average_price,
            "recommendation": (
                "Good time to buy" if current_price < average_price else "Consider waiting"
            ),
        }


class MockCheckoutTool(Tool):
    """Mock tool for simulating checkout process."""

    def __init__(self) -> None:
        """Initialize mock checkout tool."""
        super().__init__(
            name="checkout",
            description="Process checkout and create orders",
        )

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute checkout process.

        Args:
            products: List of products to purchase
            shipping_address: Shipping address
            payment_method: Payment method

        Returns:
            Dictionary with order confirmation
        """
        # Simulate processing delay
        await asyncio.sleep(1.0)

        products = kwargs.get("products", [])
        shipping_address = kwargs.get("shipping_address", {})
        payment_method = kwargs.get("payment_method", "credit_card")

        # Calculate totals
        subtotal = sum(p.get("price", 0) * p.get("quantity", 1) for p in products)
        tax = subtotal * 0.08  # 8% tax
        shipping = 0.0 if subtotal > 50 else 5.99
        total = subtotal + tax + shipping

        order_id = f"ORD-{random.randint(100000, 999999)}"

        return {
            "success": True,
            "order_id": order_id,
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "shipping": round(shipping, 2),
            "total": round(total, 2),
            "payment_method": payment_method,
            "shipping_address": shipping_address,
            "estimated_delivery": "3-5 business days",
            "tracking_number": f"TRACK-{random.randint(1000000000, 9999999999)}",
            "items": products,
        }
