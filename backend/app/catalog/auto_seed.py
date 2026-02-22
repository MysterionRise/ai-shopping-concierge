"""Auto-seed product catalog on startup if the products table is empty.

Loads a bundled JSON fixture with 75 beauty products. Computes safety scores
dynamically using the safety_index module and optionally indexes into ChromaDB.

Idempotent — only runs when the products table has zero rows.
"""

import json
import uuid
from pathlib import Path
from typing import cast

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.ingredient_parser import parse_ingredients
from app.catalog.safety_index import compute_safety_score
from app.models.product import Product

logger = structlog.get_logger()

FIXTURE_PATH = Path(__file__).parent / "seed_fixture.json"


def _compute_data_completeness(
    name: str,
    brand: str,
    ingredients_text: str,
    categories: list,
) -> float:
    has_name = bool(name and name.strip())
    has_brand = bool(brand and brand.strip())
    has_ingredients = bool(ingredients_text and len(ingredients_text.strip()) >= 5)
    has_categories = bool(categories)
    if has_name and has_brand and has_ingredients and has_categories:
        return 1.0
    if has_name and has_brand and (has_ingredients or has_categories):
        return 0.5
    return 0.2


async def auto_seed_catalog(session: AsyncSession) -> int:
    """Seed the product catalog from the bundled fixture if empty.

    Returns the number of products inserted (0 if table was already populated).
    """
    # Check if products table already has data
    result = await session.execute(select(func.count()).select_from(Product))
    count = result.scalar_one()
    if count > 0:
        logger.info("Product catalog already seeded", count=count)
        return 0

    # Load fixture
    if not FIXTURE_PATH.exists():
        logger.warning("Seed fixture not found", path=str(FIXTURE_PATH))
        return 0

    with open(FIXTURE_PATH) as f:
        fixture_data = json.load(f)

    logger.info("Seeding product catalog from fixture", products=len(fixture_data))

    inserted = 0
    for item in fixture_data:
        ingredients_text = item.get("ingredients_text", "")
        ingredients = parse_ingredients(ingredients_text)
        safety_score, _ = compute_safety_score(ingredients)
        categories = item.get("categories", [])
        name = item.get("name", "")
        brand = item.get("brand", "Unknown")

        completeness = _compute_data_completeness(
            name,
            brand,
            ingredients_text,
            categories,
        )

        product = Product(
            id=uuid.uuid4(),
            openbf_code=item["openbf_code"],
            name=name,
            brand=brand,
            categories=categories,
            ingredients=ingredients,
            ingredients_text=ingredients_text or None,
            image_url=item.get("image_url"),
            safety_score=safety_score,
            data_completeness=completeness,
        )
        session.add(product)
        inserted += 1

    await session.commit()
    logger.info("Product catalog seeded", inserted=inserted)

    # Optionally index into ChromaDB (best-effort, non-blocking)
    try:
        from app.core.vector_store import get_or_create_collection, upsert_product

        collection = get_or_create_collection()
        for item in fixture_data:
            ingredients_text = item.get("ingredients_text", "")
            categories_str = ", ".join(item.get("categories", []))
            # Look up the product ID we just inserted
            result = await session.execute(
                select(Product).where(Product.openbf_code == item["openbf_code"])
            )
            found = cast(Product | None, result.scalars().first())
            if found:
                upsert_product(
                    collection,
                    product_id=str(found.id),
                    name=item.get("name", ""),
                    brand=item.get("brand", "Unknown"),
                    ingredients_text=ingredients_text,
                    categories=categories_str,
                )
        logger.info("ChromaDB vector index populated", count=len(fixture_data))
    except Exception as e:
        logger.warning("ChromaDB indexing skipped (non-fatal)", error=str(e))

    return inserted
