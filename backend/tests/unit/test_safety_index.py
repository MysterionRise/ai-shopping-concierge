from app.catalog.safety_index import compute_safety_score


def test_clean_product():
    ingredients = ["water", "glycerin", "niacinamide", "hyaluronic acid"]
    score, flags = compute_safety_score(ingredients)
    assert score == 10.0
    assert len(flags) == 0


def test_product_with_irritants():
    ingredients = ["water", "sodium lauryl sulfate", "glycerin"]
    score, flags = compute_safety_score(ingredients)
    assert score < 10.0
    assert any(f["ingredient"] == "sodium lauryl sulfate" for f in flags)


def test_product_with_comedogenic():
    ingredients = ["water", "coconut oil", "glycerin"]
    score, flags = compute_safety_score(ingredients)
    assert score < 10.0
    assert any(f["type"] == "comedogenic" for f in flags)


def test_empty_ingredients():
    score, flags = compute_safety_score([])
    assert score == 5.0
    assert len(flags) == 0


def test_heavily_flagged_product():
    ingredients = ["sodium lauryl sulfate", "formaldehyde", "triclosan", "coconut oil"]
    score, flags = compute_safety_score(ingredients)
    assert score <= 4.0
    assert len(flags) >= 3


def test_score_clamped():
    # Even with many bad ingredients, score should not go below 0
    ingredients = [
        "sodium lauryl sulfate",
        "formaldehyde",
        "triclosan",
        "toluene",
        "hydroquinone",
        "coconut oil",
        "wheat germ oil",
    ]
    score, flags = compute_safety_score(ingredients)
    assert score >= 0.0
