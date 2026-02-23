import pytest

from app.agents.safety_constraint import expand_allergens, safety_pre_filter_node


class TestExpandAllergens:
    def test_expand_group_name(self):
        result = expand_allergens(["paraben"])
        assert "paraben" in result
        assert "methylparaben" in result
        assert "ethylparaben" in result
        assert "propylparaben" in result
        assert "butylparaben" in result

    def test_expand_group_member(self):
        """Expanding a member should include the whole group."""
        result = expand_allergens(["methylparaben"])
        assert "paraben" in result
        assert "methylparaben" in result
        assert "ethylparaben" in result

    def test_expand_unknown_allergen(self):
        """Unknown allergens are kept as-is."""
        result = expand_allergens(["bee venom"])
        assert "bee venom" in result
        assert len(result) == 1

    def test_expand_multiple(self):
        result = expand_allergens(["paraben", "sulfate"])
        assert "methylparaben" in result
        assert "sodium lauryl sulfate" in result

    def test_expand_empty(self):
        result = expand_allergens([])
        assert result == []

    def test_expand_normalizes_case(self):
        result = expand_allergens(["Paraben"])
        assert "paraben" in result
        assert "methylparaben" in result

    def test_expand_deduplicates(self):
        result = expand_allergens(["paraben", "methylparaben"])
        # Should not have duplicates
        assert len(result) == len(set(result))


class TestSafetyPreFilterNode:
    @pytest.fixture
    def base_state(self):
        return {
            "messages": [],
            "user_id": "test-user",
            "conversation_id": "test-conv",
            "user_profile": {},
            "hard_constraints": ["paraben"],
            "soft_preferences": [],
            "current_intent": "product_search",
            "product_results": [],
            "safety_check_passed": True,
            "safety_violations": [],
            "memory_context": [],
            "persona_scores": {},
            "error": None,
        }

    async def test_expands_allergens_for_product_search(self, base_state):
        result = await safety_pre_filter_node(base_state)
        assert "hard_constraints" in result
        assert "methylparaben" in result["hard_constraints"]
        assert "paraben" in result["hard_constraints"]

    async def test_expands_allergens_for_ingredient_check(self, base_state):
        base_state["current_intent"] = "ingredient_check"
        result = await safety_pre_filter_node(base_state)
        assert "hard_constraints" in result
        assert "methylparaben" in result["hard_constraints"]

    async def test_skips_for_general_chat(self, base_state):
        base_state["current_intent"] = "general_chat"
        result = await safety_pre_filter_node(base_state)
        assert "hard_constraints" not in result

    async def test_skips_for_routine_advice(self, base_state):
        base_state["current_intent"] = "routine_advice"
        result = await safety_pre_filter_node(base_state)
        assert "hard_constraints" not in result

    async def test_no_constraints(self, base_state):
        base_state["hard_constraints"] = []
        result = await safety_pre_filter_node(base_state)
        assert result.get("safety_check_passed") is True
        assert "hard_constraints" not in result

    async def test_sets_safety_check_passed(self, base_state):
        result = await safety_pre_filter_node(base_state)
        assert result["safety_check_passed"] is True
        assert result["safety_violations"] == []

    async def test_multiple_allergens(self, base_state):
        base_state["hard_constraints"] = ["paraben", "fragrance"]
        result = await safety_pre_filter_node(base_state)
        expanded = result["hard_constraints"]
        assert "methylparaben" in expanded
        assert "parfum" in expanded
        assert "linalool" in expanded
