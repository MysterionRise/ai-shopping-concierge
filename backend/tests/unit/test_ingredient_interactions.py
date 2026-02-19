"""Tests for ingredient-to-ingredient interaction detection."""

from app.catalog.ingredient_interactions import (
    INTERACTION_DB,
    find_ingredient_interactions,
)


class TestInteractionDB:
    """Verify the interaction database structure."""

    def test_all_entries_have_required_fields(self):
        for entry in INTERACTION_DB:
            assert "group_a" in entry
            assert "group_b" in entry
            assert "severity" in entry
            assert "concern" in entry
            assert "label" in entry

    def test_severity_values_are_valid(self):
        valid = {"high", "medium", "low"}
        for entry in INTERACTION_DB:
            assert entry["severity"] in valid, f"Invalid severity in {entry['label']}"

    def test_at_least_5_interactions(self):
        assert len(INTERACTION_DB) >= 5


class TestFindInteractions:
    """Test find_ingredient_interactions."""

    def test_retinol_plus_glycolic_acid(self):
        ingredients = ["water", "retinol", "glycolic acid", "niacinamide"]
        warnings = find_ingredient_interactions(ingredients)
        labels = [w["label"] for w in warnings]
        assert "Retinoid + AHA" in labels

    def test_retinol_plus_salicylic_acid(self):
        ingredients = ["retinyl palmitate", "salicylic acid"]
        warnings = find_ingredient_interactions(ingredients)
        labels = [w["label"] for w in warnings]
        assert "Retinoid + BHA" in labels

    def test_retinol_plus_benzoyl_peroxide(self):
        ingredients = ["tretinoin", "benzoyl peroxide"]
        warnings = find_ingredient_interactions(ingredients)
        labels = [w["label"] for w in warnings]
        assert "Retinoid + Benzoyl Peroxide" in labels

    def test_vitamin_c_plus_niacinamide_low_severity(self):
        ingredients = ["ascorbic acid", "niacinamide"]
        warnings = find_ingredient_interactions(ingredients)
        assert len(warnings) == 1
        assert warnings[0]["severity"] == "low"
        assert warnings[0]["label"] == "Vitamin C + Niacinamide"

    def test_no_interactions_for_safe_ingredients(self):
        ingredients = ["water", "glycerin", "hyaluronic acid", "ceramides"]
        warnings = find_ingredient_interactions(ingredients)
        assert warnings == []

    def test_empty_ingredients(self):
        assert find_ingredient_interactions([]) == []

    def test_multiple_interactions_in_one_product(self):
        ingredients = ["retinol", "glycolic acid", "salicylic acid", "benzoyl peroxide"]
        warnings = find_ingredient_interactions(ingredients)
        labels = {w["label"] for w in warnings}
        assert "Retinoid + AHA" in labels
        assert "Retinoid + BHA" in labels
        assert "Retinoid + Benzoyl Peroxide" in labels
        assert "AHA + BHA" in labels

    def test_case_insensitivity(self):
        ingredients = ["Retinol", "Glycolic Acid"]
        warnings = find_ingredient_interactions(ingredients)
        assert len(warnings) >= 1

    def test_warning_structure(self):
        ingredients = ["retinol", "glycolic acid"]
        warnings = find_ingredient_interactions(ingredients)
        assert len(warnings) == 1
        w = warnings[0]
        assert "ingredient_a" in w
        assert "ingredient_b" in w
        assert "severity" in w
        assert "concern" in w
        assert "label" in w

    def test_no_duplicate_labels(self):
        """Same interaction should not be reported twice."""
        ingredients = [
            "retinol",
            "retinyl palmitate",
            "glycolic acid",
            "lactic acid",
        ]
        warnings = find_ingredient_interactions(ingredients)
        labels = [w["label"] for w in warnings]
        assert len(labels) == len(set(labels))

    def test_benzoyl_peroxide_plus_vitamin_c(self):
        ingredients = ["benzoyl peroxide", "l-ascorbic acid"]
        warnings = find_ingredient_interactions(ingredients)
        labels = [w["label"] for w in warnings]
        assert "Benzoyl Peroxide + Vitamin C" in labels
