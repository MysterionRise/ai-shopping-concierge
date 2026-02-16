from app.catalog.ingredient_parser import (
    find_allergen_matches,
    get_allergen_group,
    normalize_ingredient,
    parse_ingredients,
)


def test_parse_ingredients_basic():
    text = "Water, Glycerin, Niacinamide, Hyaluronic Acid"
    result = parse_ingredients(text)
    assert "water" in result
    assert "glycerin" in result
    assert "niacinamide" in result
    assert "hyaluronic acid" in result


def test_parse_ingredients_empty():
    assert parse_ingredients("") == []
    assert parse_ingredients(None) == []


def test_parse_ingredients_with_brackets():
    text = "Water, Glycerin [1-5%], Niacinamide"
    result = parse_ingredients(text)
    assert "glycerin" in result
    assert not any("[" in item for item in result)


def test_normalize_ingredient():
    assert normalize_ingredient("  Glycerin  ") == "glycerin"
    assert normalize_ingredient("WATER") == "water"


def test_get_allergen_group():
    assert get_allergen_group("methylparaben") == "paraben"
    assert get_allergen_group("sodium lauryl sulfate") == "sulfate"
    assert get_allergen_group("parfum") == "fragrance"
    assert get_allergen_group("water") is None


def test_find_allergen_matches_direct():
    ingredients = ["water", "methylparaben", "glycerin"]
    allergens = ["paraben"]
    matches = find_allergen_matches(ingredients, allergens)
    assert len(matches) == 1
    assert matches[0]["ingredient"] == "methylparaben"


def test_find_allergen_matches_no_match():
    ingredients = ["water", "glycerin", "niacinamide"]
    allergens = ["paraben"]
    matches = find_allergen_matches(ingredients, allergens)
    assert len(matches) == 0


def test_find_allergen_matches_multiple():
    ingredients = ["water", "methylparaben", "ethylparaben", "glycerin"]
    allergens = ["paraben"]
    matches = find_allergen_matches(ingredients, allergens)
    assert len(matches) == 2
