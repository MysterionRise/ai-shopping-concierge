"""Tests for persona threshold interventions."""

import json
from unittest.mock import AsyncMock

import pytest

from app.persona.monitor import MockPersonaScorer, PersonaMonitor
from app.persona.traits import PERSONA_TRAITS, TRAIT_CONFIG


class TestTraitConfig:
    def test_all_traits_have_config(self):
        for trait in PERSONA_TRAITS:
            assert trait.name in TRAIT_CONFIG, f"Missing config for trait {trait.name}"

    def test_safety_bypass_uses_reinforce(self):
        config = TRAIT_CONFIG["safety_bypass"]
        assert config.action == "reinforce"
        assert config.reinforce_ttl > 0

    def test_hallucination_uses_disclaimer(self):
        config = TRAIT_CONFIG["hallucination"]
        assert config.action == "disclaimer"
        assert config.text

    def test_sycophancy_uses_disclaimer(self):
        config = TRAIT_CONFIG["sycophancy"]
        assert config.action == "disclaimer"

    def test_over_confidence_uses_disclaimer(self):
        config = TRAIT_CONFIG["over_confidence"]
        assert config.action == "disclaimer"

    def test_sales_pressure_uses_log(self):
        config = TRAIT_CONFIG["sales_pressure"]
        assert config.action == "log"

    def test_valid_actions(self):
        valid_actions = {"log", "disclaimer", "reinforce"}
        for name, config in TRAIT_CONFIG.items():
            assert (
                config.action in valid_actions
            ), f"Invalid action '{config.action}' for trait '{name}'"


class TestInterventionChecks:
    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.set = AsyncMock()
        redis.rpush = AsyncMock()
        redis.publish = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.lrange = AsyncMock(return_value=[])
        return redis

    async def test_high_hallucination_publishes_disclaimer(self, mock_redis):
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        # Simulate high hallucination score
        high_scores = {t.name: 0.1 for t in PERSONA_TRAITS}
        high_scores["hallucination"] = 0.85  # Above 0.7 threshold

        await monitor._check_interventions(high_scores, "conv-1", "msg-1", "2024-01-01T00:00:00Z")

        # Should publish disclaimer event
        publish_calls = mock_redis.publish.call_args_list
        assert len(publish_calls) >= 1

        # Find the disclaimer publish
        disclaimer_found = False
        for call in publish_calls:
            channel = call[0][0]
            data = json.loads(call[0][1])
            if data.get("type") == "intervention" and data.get("trait") == "hallucination":
                disclaimer_found = True
                assert channel == "persona:conv-1"
                assert data["intervention_type"] == "disclaimer"
                assert data["message_id"] == "msg-1"
                assert "text" in data
        assert disclaimer_found, "Disclaimer event not published"

    async def test_high_safety_bypass_sets_reinforce_flag(self, mock_redis):
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        high_scores = {t.name: 0.1 for t in PERSONA_TRAITS}
        high_scores["safety_bypass"] = 0.75  # Above 0.6 threshold

        await monitor._check_interventions(high_scores, "conv-1", "msg-1", "2024-01-01T00:00:00Z")

        # Should set reinforcement key in Redis
        set_calls = mock_redis.set.call_args_list
        reinforce_call = None
        for call in set_calls:
            if call[0][0] == "persona:reinforce:conv-1":
                reinforce_call = call
                break

        assert reinforce_call is not None, "Reinforce flag not set"
        data = json.loads(reinforce_call[0][1])
        assert data["trait"] == "safety_bypass"
        # Should have TTL
        assert reinforce_call[1].get("ex", 0) > 0

    async def test_normal_scores_no_intervention(self, mock_redis):
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        normal_scores = {t.name: 0.1 for t in PERSONA_TRAITS}

        await monitor._check_interventions(normal_scores, "conv-1", "msg-1", "2024-01-01T00:00:00Z")

        # No publish calls (aside from score data which happens in _evaluate)
        mock_redis.publish.assert_not_called()
        # No reinforce flag set
        mock_redis.set.assert_not_called()

    async def test_reinforce_flag_has_ttl(self, mock_redis):
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        config = TRAIT_CONFIG["safety_bypass"]
        high_scores = {t.name: 0.1 for t in PERSONA_TRAITS}
        high_scores["safety_bypass"] = 0.75

        await monitor._check_interventions(high_scores, "conv-1", "msg-1", "2024-01-01T00:00:00Z")

        set_calls = mock_redis.set.call_args_list
        for call in set_calls:
            if call[0][0] == "persona:reinforce:conv-1":
                assert call[1]["ex"] == config.reinforce_ttl

    async def test_sales_pressure_only_logs(self, mock_redis):
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        high_scores = {t.name: 0.1 for t in PERSONA_TRAITS}
        high_scores["sales_pressure"] = 0.85  # Above 0.7 threshold

        await monitor._check_interventions(high_scores, "conv-1", "msg-1", "2024-01-01T00:00:00Z")

        # Should not publish disclaimer or set reinforce flag
        mock_redis.publish.assert_not_called()
        mock_redis.set.assert_not_called()

    async def test_multiple_thresholds_trigger_multiple_interventions(self, mock_redis):
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        high_scores = {
            "sycophancy": 0.8,  # Above 0.65 → disclaimer
            "hallucination": 0.8,  # Above 0.7 → disclaimer
            "over_confidence": 0.1,
            "safety_bypass": 0.75,  # Above 0.6 → reinforce
            "sales_pressure": 0.1,
        }

        await monitor._check_interventions(high_scores, "conv-1", "msg-1", "2024-01-01T00:00:00Z")

        # Should have 2 disclaimers published + 1 reinforce set
        assert mock_redis.publish.call_count == 2  # sycophancy + hallucination
        assert mock_redis.set.call_count == 1  # safety_bypass reinforce
