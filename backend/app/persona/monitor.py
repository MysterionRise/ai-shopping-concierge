"""Persona monitoring — runs asynchronously after response generation.

Fire-and-forget: does not block the response pipeline.
Scores are stored in Redis for fast writes, periodically flushed to Postgres.
"""

import asyncio
import json
from datetime import datetime

import redis.asyncio as aioredis
import structlog

from app.config import settings
from app.persona.traits import PERSONA_TRAITS

logger = structlog.get_logger()

REDIS_PERSONA_PREFIX = "persona:"


class PersonaMonitor:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self._extractor = None

    def _get_extractor(self):
        if self._extractor is None and settings.persona_enabled:
            try:
                from app.persona.vector_extractor import PersonaVectorExtractor

                self._extractor = PersonaVectorExtractor()
                self._extractor.load_precomputed_vectors()
            except Exception as e:
                logger.error("Failed to initialize persona extractor", error=str(e))
        return self._extractor

    async def evaluate_async(
        self,
        prompt: str,
        response: str,
        conversation_id: str,
        message_id: str,
    ):
        """Fire-and-forget persona evaluation."""
        if not settings.persona_enabled:
            return

        asyncio.create_task(self._evaluate(prompt, response, conversation_id, message_id))

    async def _evaluate(
        self,
        prompt: str,
        response: str,
        conversation_id: str,
        message_id: str,
    ):
        try:
            extractor = self._get_extractor()
            if not extractor:
                return

            # Run in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                extractor.score_response,
                prompt,
                response,
            )

            # Store in Redis
            score_data = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "scores": scores,
                "timestamp": datetime.utcnow().isoformat(),
            }

            key = f"{REDIS_PERSONA_PREFIX}{conversation_id}:{message_id}"
            await self.redis.set(key, json.dumps(score_data), ex=86400)

            # Also append to conversation history
            history_key = f"{REDIS_PERSONA_PREFIX}history:{conversation_id}"
            await self.redis.rpush(history_key, json.dumps(score_data))

            # Check thresholds
            for trait in PERSONA_TRAITS:
                score = scores.get(trait.name, 0)
                if score > trait.threshold:
                    logger.warning(
                        "Persona threshold exceeded",
                        trait=trait.name,
                        score=score,
                        threshold=trait.threshold,
                        conversation_id=conversation_id,
                    )

        except Exception as e:
            logger.error("Persona evaluation failed", error=str(e))

    async def get_scores(self, conversation_id: str, message_id: str) -> dict:
        key = f"{REDIS_PERSONA_PREFIX}{conversation_id}:{message_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return {}

    async def get_history(self, conversation_id: str) -> list[dict]:
        key = f"{REDIS_PERSONA_PREFIX}history:{conversation_id}"
        items = await self.redis.lrange(key, 0, -1)
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
