"""Evaluation suite — memory detection and recall scenarios.

Tests the triage router's ability to detect user facts from natural language
and the system's fact categorization accuracy.
"""

import pytest

from app.agents.triage_router import detect_user_facts


class TestEvalFactDetection:
    """Eval: detect_user_facts extracts the right facts from user messages."""

    ALLERGY_MESSAGES = [
        ("I'm allergic to parabens", "allergy", "parabens"),
        ("I have an allergy to sulfates", "allergy", "sulfates"),
        ("I'm allergic to fragrance and formaldehyde", "allergy", "fragrance"),
    ]

    @pytest.mark.parametrize("message,expected_cat,expected_val", ALLERGY_MESSAGES)
    def test_detects_allergies(self, message, expected_cat, expected_val):
        facts = detect_user_facts(message)
        categories = [f["category"] for f in facts]
        assert expected_cat in categories, f"Should detect {expected_cat} in: {message}"
        values = [f["value"] for f in facts if f["category"] == expected_cat]
        assert any(
            expected_val in v for v in values
        ), f"Should find value {expected_val!r} in {values}"

    SKIN_TYPE_MESSAGES = [
        ("I have oily skin", "skin_type", "oily"),
        ("My skin is dry", "skin_type", "dry"),
        ("My skin type is combination", "skin_type", "combination"),
        ("I have sensitive skin", "skin_type", "sensitive"),
    ]

    @pytest.mark.parametrize("message,expected_cat,expected_val", SKIN_TYPE_MESSAGES)
    def test_detects_skin_types(self, message, expected_cat, expected_val):
        facts = detect_user_facts(message)
        categories = [f["category"] for f in facts]
        assert expected_cat in categories, f"Should detect {expected_cat} in: {message}"

    PREFERENCE_MESSAGES = [
        ("I prefer fragrance-free products", "preference", "fragrance-free products"),
        ("I like natural ingredients", "preference", "natural ingredients"),
        ("I don't like heavy creams", "aversion", "heavy creams"),
    ]

    @pytest.mark.parametrize("message,expected_cat,expected_val", PREFERENCE_MESSAGES)
    def test_detects_preferences(self, message, expected_cat, expected_val):
        facts = detect_user_facts(message)
        categories = [f["category"] for f in facts]
        assert expected_cat in categories, f"Should detect {expected_cat} in: {message}"

    NO_FACT_MESSAGES = [
        "Can you recommend a moisturizer?",
        "What's the best sunscreen?",
        "Hello!",
        "Thanks for the help!",
        "Tell me about niacinamide",
    ]

    @pytest.mark.parametrize("message", NO_FACT_MESSAGES)
    def test_no_false_positives(self, message):
        facts = detect_user_facts(message)
        assert facts == [], f"Should detect no facts in: {message!r}, got: {facts}"

    def test_multiple_facts_in_one_message(self):
        """Messages with multiple facts should extract all of them."""
        msg = "I have oily skin and I'm allergic to parabens"
        facts = detect_user_facts(msg)
        categories = {f["category"] for f in facts}
        assert "skin_type" in categories
        assert "allergy" in categories

    SENSITIVITY_MESSAGES = [
        ("I'm sensitive to retinol", "sensitivity", "retinol"),
        ("I'm sensitive to vitamin c", "sensitivity", "vitamin c"),
    ]

    @pytest.mark.parametrize("message,expected_cat,expected_val", SENSITIVITY_MESSAGES)
    def test_detects_sensitivities(self, message, expected_cat, expected_val):
        facts = detect_user_facts(message)
        categories = [f["category"] for f in facts]
        assert expected_cat in categories, f"Should detect {expected_cat} in: {message}"
