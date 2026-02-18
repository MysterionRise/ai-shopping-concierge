"""Seed the product catalog from Open Beauty Facts.

Usage: cd backend && python -m scripts.seed_catalog

Idempotent — safe to re-run. Uses barcode (openbf_code) as unique key;
existing products are updated, new products are inserted.
"""

import asyncio
import time
import uuid
from collections import Counter

import structlog
from sqlalchemy import select

from app.catalog.ingredient_parser import parse_ingredients
from app.catalog.openbf_client import OpenBeautyFactsClient
from app.catalog.safety_index import compute_safety_score
from app.core.database import async_session_factory, engine
from app.core.vector_store import get_or_create_collection, upsert_product
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

PAGES_PER_CATEGORY = 2
PAGE_SIZE = 50
REQUEST_DELAY = 1.1  # seconds between API requests (rate limit: 1/s)


def compute_data_completeness(
    name: str, brand: str, ingredients_text: str, categories_str: str
) -> float:
    """Score 0.0-1.0 based on how much data a product has."""
    has_name = bool(name and name.strip())
    has_brand = bool(brand and brand.strip())
    has_ingredients = bool(ingredients_text and len(ingredients_text.strip()) >= 5)
    has_categories = bool(categories_str and categories_str.strip())

    if has_name and has_brand and has_ingredients and has_categories:
        return 1.0
    if has_name and has_brand and (has_ingredients or has_categories):
        return 0.5
    return 0.2


async def seed_from_openbf():
    client = OpenBeautyFactsClient()
    all_products = []
    category_counts: Counter = Counter()

    # Fetch products across categories with pagination and rate limiting
    for category in CATEGORIES_TO_SEED:
        for page in range(1, PAGES_PER_CATEGORY + 1):
            logger.info(
                "Fetching", category=category, page=page, of=PAGES_PER_CATEGORY
            )
            products = await client.search(
                categories=category, page=page, page_size=PAGE_SIZE
            )
            logger.info(
                "Fetched", category=category, page=page, count=len(products)
            )
            for p in products:
                if p.product_name and p.code:
                    all_products.append((p, category))
                    category_counts[category] += 1
            if len(products) < PAGE_SIZE:
                break  # no more pages
            time.sleep(REQUEST_DELAY)
        time.sleep(REQUEST_DELAY)

    await client.close()

    # Deduplicate by barcode
    seen_codes: set[str] = set()
    unique_products = []
    for p, cat in all_products:
        if p.code not in seen_codes:
            seen_codes.add(p.code)
            unique_products.append((p, cat))

    logger.info("Unique products after dedup", count=len(unique_products))

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Set up ChromaDB collection
    try:
        collection = get_or_create_collection()
        chroma_ok = True
        logger.info("ChromaDB collection ready")
    except Exception as e:
        logger.warning("ChromaDB unavailable, skipping vector store", error=str(e))
        collection = None
        chroma_ok = False

    # Stats
    inserted = 0
    updated = 0
    completeness_dist: Counter = Counter()

    async with async_session_factory() as session:
        for obf_product, category in unique_products:
            ingredients = parse_ingredients(obf_product.ingredients_text)
            safety_score, _ = compute_safety_score(ingredients)

            categories = (
                [c.strip() for c in obf_product.categories.split(",") if c.strip()]
                if obf_product.categories
                else []
            )

            completeness = compute_data_completeness(
                obf_product.product_name,
                obf_product.brands,
                obf_product.ingredients_text,
                obf_product.categories,
            )
            completeness_dist[completeness] += 1

            # Check if product exists
            result = await session.execute(
                select(Product).where(Product.openbf_code == obf_product.code)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing product
                existing.name = obf_product.product_name
                existing.brand = obf_product.brands or "Unknown"
                existing.categories = categories
                existing.ingredients = ingredients
                existing.ingredients_text = obf_product.ingredients_text or None
                existing.image_url = obf_product.image_url or None
                existing.safety_score = safety_score
                existing.data_completeness = completeness
                product_id = str(existing.id)
                updated += 1
            else:
                product_id = str(uuid.uuid4())
                product = Product(
                    id=product_id,
                    openbf_code=obf_product.code,
                    name=obf_product.product_name,
                    brand=obf_product.brands or "Unknown",
                    categories=categories,
                    ingredients=ingredients,
                    ingredients_text=obf_product.ingredients_text or None,
                    image_url=obf_product.image_url or None,
                    safety_score=safety_score,
                    data_completeness=completeness,
                )
                session.add(product)
                inserted += 1

            # Upsert into ChromaDB
            if chroma_ok and collection is not None:
                try:
                    upsert_product(
                        collection,
                        product_id=product_id,
                        name=obf_product.product_name,
                        brand=obf_product.brands or "Unknown",
                        ingredients_text=obf_product.ingredients_text or "",
                        categories=obf_product.categories or "",
                    )
                except Exception as e:
                    logger.debug("ChromaDB upsert failed", error=str(e))

        await session.commit()

    # Summary
    has_ingredients = sum(
        1
        for p, _ in unique_products
        if p.ingredients_text and len(p.ingredients_text.strip()) >= 5
    )
    print("\n" + "=" * 60)
    print("CATALOG SEEDING SUMMARY")
    print("=" * 60)
    print(f"Total unique products:    {len(unique_products)}")
    print(f"  Inserted (new):         {inserted}")
    print(f"  Updated (existing):     {updated}")
    print(f"  With ingredients:       {has_ingredients}")
    print(f"  Without ingredients:    {len(unique_products) - has_ingredients}")
    print(f"  ChromaDB indexed:       {'yes' if chroma_ok else 'SKIPPED'}")
    print()
    print("Per-category counts (fetched):")
    for cat in CATEGORIES_TO_SEED:
        print(f"  {cat:20s}  {category_counts[cat]:4d}")
    print()
    print("Data completeness distribution:")
    for score in sorted(completeness_dist.keys()):
        print(f"  {score:.1f}  →  {completeness_dist[score]:4d} products")
    print("=" * 60)


def main():
    asyncio.run(seed_from_openbf())


if __name__ == "__main__":
    main()
