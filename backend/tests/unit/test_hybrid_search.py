from app.agents.product_discovery import SearchIntent, _generate_fit_reasons


def test_fit_reasons_matching_product_type():
    intent = SearchIntent(product_type="moisturizer", properties="unknown", skin_type="unknown")
    product = {
        "name": "Daily Moisturizer SPF 30",
        "categories": ["moisturizers", "face care"],
        "key_ingredients": ["water", "glycerin"],
        "safety_badge": "safe",
    }
    reasons = _generate_fit_reasons(intent, product)
    assert any("moisturizer" in r.lower() for r in reasons)
    assert any("safety" in r.lower() for r in reasons)


def test_fit_reasons_matching_skin_type():
    intent = SearchIntent(product_type="unknown", properties="unknown", skin_type="dry")
    product = {
        "name": "Cream for Dry Skin",
        "categories": ["creams"],
        "key_ingredients": [],
        "safety_badge": "safe",
    }
    reasons = _generate_fit_reasons(intent, product)
    assert any("dry" in r.lower() for r in reasons)


def test_fit_reasons_no_match_gets_default():
    intent = SearchIntent(product_type="serum", properties="unknown", skin_type="unknown")
    product = {
        "name": "Lip Balm",
        "categories": ["lip care"],
        "key_ingredients": ["beeswax"],
        "safety_badge": "unverified",
    }
    reasons = _generate_fit_reasons(intent, product)
    assert len(reasons) >= 1
    assert "Relevant to your search" in reasons


def test_fit_reasons_with_properties():
    intent = SearchIntent(product_type="unknown", properties="hydrating", skin_type="unknown")
    product = {
        "name": "Hydrating Face Cream",
        "categories": [],
        "key_ingredients": ["hyaluronic acid", "glycerin"],
        "safety_badge": "safe",
    }
    reasons = _generate_fit_reasons(intent, product)
    assert any("hydrating" in r.lower() for r in reasons)
