#!/usr/bin/env python3
"""Migrate Redis-backed memories to LangMem AsyncPostgresStore.

Maps Redis namespaces to LangMem namespaces:
  memory:{user_id}:semantic    → ("user_facts", user_id)
  memory:{user_id}:constraints → ("constraints", user_id)
  memory:{user_id}:preferences → ("user_facts", user_id)
  memory:{user_id}:episodic    → ("episodes", user_id)

Usage:
    python scripts/migrate_redis_to_langmem.py
"""

import asyncio
import json
import sys

import redis.asyncio as aioredis

sys.path.insert(0, ".")

from app.config import settings  # noqa: E402
from app.memory.langmem_config import get_store_context  # noqa: E402

NAMESPACE_MAP = {
    "semantic": "user_facts",
    "constraints": "constraints",
    "preferences": "user_facts",
    "episodic": "episodes",
}


async def migrate():
    redis_client = aioredis.from_url(settings.redis_url)
    migrated = 0
    skipped = 0
    errors = 0

    async with get_store_context() as store:
        await store.setup()

        async for key in redis_client.scan_iter(match="memory:*"):
            key_str = key.decode() if isinstance(key, bytes) else key
            parts = key_str.split(":")
            # Expected: memory:{user_id}:{category}:{memory_id}
            if len(parts) < 4:
                skipped += 1
                continue

            user_id = parts[1]
            category = parts[2]
            memory_id = parts[3]

            langmem_ns_name = NAMESPACE_MAP.get(category)
            if not langmem_ns_name:
                skipped += 1
                continue

            try:
                data = await redis_client.get(key)
                if not data:
                    skipped += 1
                    continue

                memory = json.loads(data)
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})

                ns = (langmem_ns_name, user_id)

                # Check if already migrated (idempotent)
                existing = await store.aget(ns, memory_id)
                if existing is not None:
                    skipped += 1
                    continue

                value = {
                    "content": content,
                    "category": category,
                    "migrated_from": "redis",
                    **metadata,
                }

                # For constraints, add structured fields
                if category == "constraints":
                    value["ingredient"] = content
                    value["severity"] = metadata.get("severity", "absolute")
                    value["source"] = "migrated_redis"

                await store.aput(ns, memory_id, value)
                migrated += 1
            except Exception as e:
                print(f"Error migrating {key_str}: {e}")
                errors += 1

    await redis_client.aclose()

    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped:  {skipped}")
    print(f"  Errors:   {errors}")


if __name__ == "__main__":
    asyncio.run(migrate())
