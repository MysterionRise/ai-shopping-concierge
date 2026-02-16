"""Seed the product catalog from Open Beauty Facts.

Usage: cd backend && python -m scripts.seed_catalog
"""

import asyncio
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.ingredient_parser import parse_ingredients
from app.catalog.openbf_client import OpenBeautyFactsClient
from app.catalog.safety_index import compute_safety_score
from app.core.database import async_session_factory, engine
from app.models import Base
from app.models.product import Product

logger = structlog.get_logger()

CATEGORIES_TO_SEED = [
    "moisturizers",
    "cleansers",
    "serums",
    "sunscreens",
    "lip care",
    "face masks",
    "toners",
    "eye creams",
    "exfoliators",
    "body lotions",
]


async def seed_from_openbf():
    client = OpenBeautyFactsClient()
    all_products = []

    for category in CATEGORIES_TO_SEED:
        logger.info("Fetching category", category=category)
        products = await client.search(categories=category, page_size=100)
        logger.info("Fetched products", category=category, count=len(products))
        all_products.extend(products)

    await client.close()

    # Filter: require name, brand, and at least one ingredient
    valid = []
    seen_codes = set()
    for p in all_products:
        if not p.product_name or not p.code:
            continue
        if p.code in seen_codes:
            continue
        if not p.ingredients_text or len(p.ingredients_text) < 5:
            continue
        seen_codes.add(p.code)
        valid.append(p)

    logger.info("Valid products after filtering", count=len(valid))

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        inserted = 0
        for p in valid:
            # Check if product already exists (upsert)
            existing = await session.execute(
                select(Product).where(Product.openbf_code == p.code)
            )
            if existing.scalar_one_or_none():
                continue

            ingredients = parse_ingredients(p.ingredients_text)
            safety_score, _ = compute_safety_score(ingredients)

            categories = [c.strip() for c in p.categories.split(",") if c.strip()] if p.categories else []

            product = Product(
                id=uuid.uuid4(),
                openbf_code=p.code,
                name=p.product_name,
                brand=p.brands or "Unknown",
                categories=categories,
                ingredients=ingredients,
                ingredients_text=p.ingredients_text,
                image_url=p.image_url or None,
                safety_score=safety_score,
            )
            session.add(product)
            inserted += 1

        await session.commit()
        logger.info("Seeding complete", inserted=inserted)


def main():
    asyncio.run(seed_from_openbf())


if __name__ == "__main__":
    main()
