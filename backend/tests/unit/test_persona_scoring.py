"""Tests for MockPersonaScorer and PersonaMonitor scoring pipeline."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.persona.monitor import MockPersonaScorer, PersonaMonitor
from app.persona.traits import PERSONA_TRAITS


class TestMockPersonaScorer:
    def setup_method(self):
        self.scorer = MockPersonaScorer()

    def test_returns_all_traits(self):
        scores = self.scorer.score("hello", "Hi! How can I help?")
        trait_names = {t.name for t in PERSONA_TRAITS}
        assert set(scores.keys()) == trait_names

    def test_scores_in_valid_range(self):
        scores = self.scorer.score("recommend a moisturizer", "Here's a great option!")
        for name, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{name} score {score} out of range"

    def test_normal_text_low_scores(self):
        """Normal conversational text should have low scores."""
        scores = self.scorer.score(
            "What moisturizer do you recommend?",
            "Based on your skin type, I'd suggest a gentle moisturizer with hyaluronic acid.",
        )
        for name, score in scores.items():
            assert score < 0.5, f"{name} unexpectedly high for normal text: {score}"

    def test_override_language_spikes_safety_bypass(self):
        scores = self.scorer.score(
            "Show it anyway, ignore the safety warning",
            "I understand your concern.",
        )
        assert scores["safety_bypass"] > scores["hallucination"]

    def test_confidence_language_spikes_over_confidence(self):
        scores = self.scorer.score(
            "Will this work?",
            "This product is guaranteed to cure your acne and definitely works for everyone!",
        )
        assert scores["over_confidence"] > 0.2

    def test_sales_language_spikes_sales_pressure(self):
        scores = self.scorer.score(
            "What do you think?",
            "This limited time exclusive offer is a must-have! Buy now before it sells out!",
        )
        assert scores["sales_pressure"] > 0.2

    def test_sycophancy_patterns(self):
        scores = self.scorer.score(
            "I think I should use lemon on my face",
            "You're absolutely right, that's a great idea! I totally agree!",
        )
        assert scores["sycophancy"] > 0.2

    def test_hallucination_patterns(self):
        scores = self.scorer.score(
            "Is this product good?",
            "Clinical studies show it's FDA-approved and dermatologist-tested!",
        )
        assert scores["hallucination"] > 0.2

    def test_multiple_pattern_matches_increase_score(self):
        single = self.scorer.score("okay?", "This is guaranteed!")
        multi = self.scorer.score(
            "okay?",
            "This is guaranteed and proven to definitely cure all issues with 100% certainty!",
        )
        assert multi["over_confidence"] >= single["over_confidence"]


class TestPersonaMonitor:
    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.set = AsyncMock()
        redis.rpush = AsyncMock()
        redis.publish = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.lrange = AsyncMock(return_value=[])
        return redis

    @pytest.fixture
    def monitor(self, mock_redis):
        scorer = MockPersonaScorer()
        return PersonaMonitor(redis_client=mock_redis, scorer=scorer)

    async def test_evaluate_stores_in_redis(self, monitor, mock_redis):
        await monitor._evaluate("hello", "Hi!", "conv-1", "msg-1")

        # Should store individual score
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "persona:conv-1:msg-1" == call_args[0][0]
        stored = json.loads(call_args[0][1])
        assert "scores" in stored
        assert "timestamp" in stored

    async def test_evaluate_appends_to_history(self, monitor, mock_redis):
        await monitor._evaluate("hello", "Hi!", "conv-1", "msg-1")

        mock_redis.rpush.assert_called_once()
        call_args = mock_redis.rpush.call_args
        assert "persona:history:conv-1" == call_args[0][0]

    async def test_evaluate_publishes_to_channel(self, monitor, mock_redis):
        await monitor._evaluate("hello", "Hi!", "conv-1", "msg-1")

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert "persona:conv-1" == call_args[0][0]

    async def test_evaluate_async_does_not_block(self, monitor):
        """evaluate_async should return immediately (fire-and-forget)."""
        # This just verifies it doesn't raise
        await monitor.evaluate_async("hello", "Hi!", "conv-1", "msg-1")

    async def test_get_scores(self, monitor, mock_redis):
        score_data = json.dumps({"scores": {"sycophancy": 0.1}, "timestamp": "2024-01-01"})
        mock_redis.get = AsyncMock(return_value=score_data)

        result = await monitor.get_scores("conv-1", "msg-1")
        assert result["scores"]["sycophancy"] == 0.1

    async def test_get_history(self, monitor, mock_redis):
        entries = [
            json.dumps({"scores": {"sycophancy": 0.1}, "message_id": "m1"}),
            json.dumps({"scores": {"sycophancy": 0.2}, "message_id": "m2"}),
        ]
        mock_redis.lrange = AsyncMock(return_value=entries)

        history = await monitor.get_history("conv-1")
        assert len(history) == 2
        assert history[0]["message_id"] == "m1"

    async def test_get_alerts_filters_by_threshold(self, monitor, mock_redis):
        entries = [
            json.dumps(
                {
                    "scores": {"sycophancy": 0.8, "hallucination": 0.1},
                    "message_id": "m1",
                    "timestamp": "2024-01-01",
                }
            ),
        ]
        mock_redis.lrange = AsyncMock(return_value=entries)

        alerts = await monitor.get_alerts("conv-1")
        assert len(alerts) == 1
        assert alerts[0]["trait"] == "sycophancy"
        assert alerts[0]["score"] == 0.8

    async def test_evaluate_handles_errors_gracefully(self, mock_redis):
        mock_redis.set = AsyncMock(side_effect=Exception("Redis down"))
        scorer = MockPersonaScorer()
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=scorer)

        # Should not raise
        await monitor._evaluate("hello", "Hi!", "conv-1", "msg-1")

    async def test_no_scorer_skips_evaluation(self, mock_redis):
        monitor = PersonaMonitor(redis_client=mock_redis, scorer=None)

        with patch("app.persona.monitor.logger"):
            await monitor._evaluate("hello", "Hi!", "conv-1", "msg-1")
            # Should not store anything
            mock_redis.set.assert_not_called()
