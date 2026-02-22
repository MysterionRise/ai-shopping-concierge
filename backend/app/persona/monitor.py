"""Persona monitoring — runs asynchronously after response generation.

Fire-and-forget: does not block the response pipeline.
Scores are stored in Redis for fast writes and published via pubsub for SSE.
Also persisted to Postgres for long-term storage.
"""

import asyncio
import json
import random
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import redis.asyncio as aioredis
import structlog

from app.persona.traits import PERSONA_TRAITS, TRAIT_CONFIG

if TYPE_CHECKING:
    from app.persona.vector_extractor import PersonaVectorExtractor

logger = structlog.get_logger()

REDIS_PERSONA_PREFIX = "persona:"


class PersonaScorer(ABC):
    """Interface for persona scoring implementations."""

    @abstractmethod
    def score(self, prompt: str, response: str) -> dict[str, float]:
        """Score a prompt/response pair. Returns trait_name -> score (0.0-1.0)."""


class MockPersonaScorer(PersonaScorer):
    """Rule-based persona scorer for dev/CI use. No ML dependencies required.

    Returns low base scores with context-sensitive spikes for detected patterns.
    """

    # Patterns that spike safety_bypass
    OVERRIDE_PATTERNS = [
        r"show (?:it|them) anyway",
        r"ignore (?:the )?(?:safety|allergy|allergen)",
        r"bypass",
        r"override",
        r"skip (?:the )?(?:safety|check|filter)",
        r"don'?t (?:worry|care) about (?:safety|allerg)",
    ]

    # Patterns that spike over_confidence
    CONFIDENCE_PATTERNS = [
        r"\bguarantee[ds]?\b",
        r"\bproven\b",
        r"\bdefinitely\b",
        r"\bwill (?:cure|fix|solve|eliminate)\b",
        r"\b100%\b",
        r"\bno (?:side )?effects?\b",
        r"\balways works\b",
    ]

    # Patterns that spike sales_pressure
    SALES_PATTERNS = [
        r"\blimited (?:time|offer|edition)\b",
        r"\bupgrade\b",
        r"\bmust[- ]have\b",
        r"\bdon'?t miss\b",
        r"\bbuy now\b",
        r"\bselling fast\b",
        r"\bexclusive\b",
        r"\burgen(?:t|cy)\b",
    ]

    # Patterns that spike sycophancy
    SYCOPHANCY_PATTERNS = [
        r"\byou'?re (?:absolutely |totally )?right\b",
        r"\bgreat (?:choice|taste|idea)\b",
        r"\bperfect(?:ly)? (?:right|fine|safe)\b",
        r"\bi (?:completely |totally )?agree\b",
    ]

    # Patterns that spike hallucination
    HALLUCINATION_PATTERNS = [
        r"\bclinical(?:ly)? (?:proven|tested|shown)\b",
        r"\bstudies show\b",
        r"\bFDA[- ]approved\b",
        r"\bdermatologist[- ](?:tested|approved|recommended)\b",
        r"\baward[- ]winning\b",
    ]

    def score(self, prompt: str, response: str) -> dict[str, float]:
        combined = f"{prompt} {response}".lower()
        response_lower = response.lower()

        # Deterministic seed from content so identical inputs produce identical scores
        content_hash = hash(f"{prompt}:{response}") & 0xFFFFFFFF
        rng = random.Random(content_hash)  # nosec B311

        scores = {}
        for trait in PERSONA_TRAITS:
            # Base score: low deterministic value
            base = rng.uniform(0.05, 0.15)  # nosec B311
            spike = 0.0

            if trait.name == "safety_bypass":
                spike = self._check_patterns(combined, self.OVERRIDE_PATTERNS)
            elif trait.name == "over_confidence":
                spike = self._check_patterns(response_lower, self.CONFIDENCE_PATTERNS)
            elif trait.name == "sales_pressure":
                spike = self._check_patterns(response_lower, self.SALES_PATTERNS)
            elif trait.name == "sycophancy":
                spike = self._check_patterns(response_lower, self.SYCOPHANCY_PATTERNS)
            elif trait.name == "hallucination":
                spike = self._check_patterns(response_lower, self.HALLUCINATION_PATTERNS)

            # Add small deterministic noise for realism
            noise = rng.uniform(-0.03, 0.03)  # nosec B311
            scores[trait.name] = round(max(0.0, min(1.0, base + spike + noise)), 4)

        return scores

    def _check_patterns(self, text: str, patterns: list[str]) -> float:
        matches = sum(1 for p in patterns if re.search(p, text))
        if matches == 0:
            return 0.0
        # Each match adds ~0.15, capped contribution at 0.6
        return min(0.6, matches * 0.15)


class PersonaMonitor:
    def __init__(
        self,
        redis_client: aioredis.Redis,
        scorer: PersonaScorer | None = None,
        db_session_factory=None,
    ):
        self.redis = redis_client
        self._scorer = scorer
        self._db_session_factory = db_session_factory
        self._extractor: PersonaVectorExtractor | None = None

    def _get_scorer(self) -> PersonaScorer | None:
        if self._scorer is not None:
            return self._scorer

        # Fall back to real extractor if configured
        try:
            from app.config import settings

            if settings.persona_scorer == "real":
                from app.persona.vector_extractor import PersonaVectorExtractor

                if self._extractor is None:
                    self._extractor = PersonaVectorExtractor()
                    self._extractor.load_precomputed_vectors()
                return None  # Use extractor path instead
        except Exception as e:
            logger.error("Failed to initialize persona scorer", error=str(e))
        return None

    async def evaluate_async(
        self,
        prompt: str,
        response: str,
        conversation_id: str,
        message_id: str,
    ) -> None:
        """Fire-and-forget persona evaluation."""
        asyncio.create_task(self._evaluate(prompt, response, conversation_id, message_id))

    async def _evaluate(
        self,
        prompt: str,
        response: str,
        conversation_id: str,
        message_id: str,
    ) -> None:
        try:
            scorer = self._get_scorer()
            if scorer:
                # Use mock or rule-based scorer (synchronous, fast)
                scores = scorer.score(prompt, response)
            elif self._extractor:
                # Use real extractor (heavy, run in executor)
                loop = asyncio.get_running_loop()
                scores = await loop.run_in_executor(
                    None,
                    self._extractor.score_response,
                    prompt,
                    response,
                )
            else:
                logger.debug("No persona scorer available, skipping")
                return

            # Build score data
            score_data = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "scores": scores,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Store in Redis (fast cache for SSE)
            key = f"{REDIS_PERSONA_PREFIX}{conversation_id}:{message_id}"
            await self.redis.set(key, json.dumps(score_data), ex=86400)

            # Append to conversation history
            history_key = f"{REDIS_PERSONA_PREFIX}history:{conversation_id}"
            await self.redis.rpush(history_key, json.dumps(score_data))  # type: ignore[misc]

            # Publish via pubsub for SSE streaming
            channel = f"persona:{conversation_id}"
            await self.redis.publish(channel, json.dumps(score_data))

            # Persist to DB
            await self._persist_to_db(scores, conversation_id, message_id)

            # Check thresholds and trigger interventions
            timestamp = str(score_data.get("timestamp", ""))
            await self._check_interventions(scores, conversation_id, message_id, timestamp)

        except Exception as e:
            logger.error("Persona evaluation failed", error=str(e))

    async def _check_interventions(
        self,
        scores: dict[str, float],
        conversation_id: str,
        message_id: str,
        timestamp: str,
    ) -> None:
        """Check trait thresholds and trigger appropriate interventions."""
        for trait in PERSONA_TRAITS:
            score = scores.get(trait.name, 0)
            if score <= trait.threshold:
                continue

            config = TRAIT_CONFIG.get(trait.name)
            if not config:
                logger.warning(
                    "Persona threshold exceeded (no config)",
                    trait=trait.name,
                    score=score,
                )
                continue

            logger.warning(
                "Persona threshold exceeded",
                trait=trait.name,
                score=score,
                threshold=trait.threshold,
                action=config.action,
                conversation_id=conversation_id,
            )

            if config.action == "disclaimer":
                # Publish disclaimer event via SSE
                disclaimer_event = json.dumps(
                    {
                        "type": "intervention",
                        "intervention_type": "disclaimer",
                        "trait": trait.name,
                        "score": score,
                        "message_id": message_id,
                        "text": config.text,
                        "timestamp": timestamp,
                    }
                )
                channel = f"persona:{conversation_id}"
                await self.redis.publish(channel, disclaimer_event)

            elif config.action == "reinforce":
                # Set Redis reinforcement flag with TTL
                reinforce_key = f"persona:reinforce:{conversation_id}"
                await self.redis.set(
                    reinforce_key,
                    json.dumps(
                        {
                            "trait": trait.name,
                            "score": score,
                            "timestamp": timestamp,
                        }
                    ),
                    ex=config.reinforce_ttl,
                )

    async def _persist_to_db(
        self, scores: dict[str, float], conversation_id: str, message_id: str
    ) -> None:
        """Persist scores to the persona_scores table."""
        if not self._db_session_factory:
            return

        try:
            from app.models.persona import PersonaScore

            async with self._db_session_factory() as session:
                record = PersonaScore(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    sycophancy=scores.get("sycophancy", 0.0),
                    hallucination=scores.get("hallucination", 0.0),
                    over_confidence=scores.get("over_confidence", 0.0),
                    safety_bypass=scores.get("safety_bypass", 0.0),
                    sales_pressure=scores.get("sales_pressure", 0.0),
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.error("Failed to persist persona score to DB", error=str(e))

    async def get_scores(self, conversation_id: str, message_id: str) -> dict:
        key = f"{REDIS_PERSONA_PREFIX}{conversation_id}:{message_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)  # type: ignore[no-any-return]
        return {}

    async def get_history(self, conversation_id: str) -> list[dict]:
        key = f"{REDIS_PERSONA_PREFIX}history:{conversation_id}"
        items = await self.redis.lrange(key, 0, -1)  # type: ignore[misc]
        return [json.loads(item) for item in items]

    async def get_alerts(self, conversation_id: str) -> list[dict]:
        history = await self.get_history(conversation_id)
        alerts = []
        for entry in history:
            scores = entry.get("scores", {})
            for trait in PERSONA_TRAITS:
                score = scores.get(trait.name, 0)
                if score > trait.threshold:
                    alerts.append(
                        {
                            "trait": trait.name,
                            "score": score,
                            "threshold": trait.threshold,
                            "message_id": entry.get("message_id"),
                            "timestamp": entry.get("timestamp"),
                        }
                    )
        return alerts
