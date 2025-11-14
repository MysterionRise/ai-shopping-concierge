"""Mock data fixtures for testing."""

from typing import Any, Dict, List


def get_mock_shopping_criteria() -> Dict[str, Any]:
    """Get mock shopping criteria."""
    return {
        "ready": True,
        "product_category": "running shoes",
        "budget": {"min": 0, "max": 150},
        "must_have_features": ["cushioning", "breathable"],
        "nice_to_have_features": ["lightweight"],
        "constraints": ["under $150"],
        "use_case": "daily running and training",
        "confidence_level": "high",
    }


def get_mock_products() -> List[Dict[str, Any]]:
    """Get mock product list."""
    return [
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
            ],
            "availability": "in_stock",
            "brand": "Nike",
            "url": "https://example.com/products/nike-pegasus-40",
        },
        {
            "product_id": "SHOE-RUN-002",
            "name": "Adidas Ultraboost 23",
            "category": "running shoes",
            "description": "Energy-returning running shoes",
            "price": 189.99,
            "original_price": 189.99,
            "rating": 4.7,
            "review_count": 892,
            "features": [
                "Boost midsole technology",
                "Primeknit upper",
            ],
            "availability": "in_stock",
            "brand": "Adidas",
        },
    ]


def get_mock_user_message() -> str:
    """Get mock user message."""
    return "I need running shoes under $150 for daily training"


def get_mock_conversation_history() -> List[Dict[str, str]]:
    """Get mock conversation history."""
    return [
        {
            "role": "user",
            "content": "I need some shoes",
        },
        {
            "role": "assistant",
            "content": "What type of shoes are you looking for?",
        },
        {
            "role": "user",
            "content": "Running shoes under $150",
        },
    ]


def get_mock_shipping_address() -> Dict[str, str]:
    """Get mock shipping address."""
    return {
        "name": "John Doe",
        "address_line1": "123 Main St",
        "address_line2": "Apt 4B",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "country": "USA",
    }


def get_mock_deal_info() -> Dict[str, Any]:
    """Get mock deal information."""
    return {
        "product_id": "SHOE-RUN-001",
        "product_name": "Nike Air Zoom Pegasus 40",
        "current_price": 129.99,
        "original_price": 140.00,
        "coupons": ["NIKE10 - 10% off"],
        "best_coupon": "NIKE10 - 10% off",
        "price_history": {
            "lowest_price": 120.00,
            "highest_price": 150.00,
            "is_good_deal": True,
        },
        "is_good_deal": True,
        "savings_potential": {
            "amount": 13.00,
            "percentage": 10.0,
            "description": "NIKE10 - 10% off",
        },
    }
