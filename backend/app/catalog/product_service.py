import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.ingredient_interactions import find_ingredient_interactions
from app.catalog.ingredient_parser import find_allergen_matches, parse_ingredients
from app.core.vector_store import get_or_create_collection, search_similar
from app.models.product import Product

logger = structlog.get_logger()


async def search_products(
    db: AsyncSession,
    query: str = "",
    limit: int = 10,
) -> list[Product]:
    stmt = select(Product)
    if query:
        escaped = query.replace("%", r"\%").replace("_", r"\_")
        stmt = stmt.where(
            Product.name.ilike(f"%{escaped}%")
            | Product.brand.ilike(f"%{escaped}%")
            | Product.ingredients_text.ilike(f"%{escaped}%")
        )
    stmt = stmt.order_by(Product.safety_score.desc().nullslast()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def search_products_safe(
    db: AsyncSession,
    query: str = "",
    allergens: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    products = await search_products(db, query, limit=limit * 2)

    results = []
    for product in products:
        ingredients = parse_ingredients(product.ingredients_text or "")
        if allergens:
            matches = find_allergen_matches(ingredients, allergens)
            if matches:
                logger.info(
                    "Product filtered by allergen",
                    product=product.name,
                    matches=matches,
                )
                continue

        results.append(
            {
                "id": str(product.id),
                "name": product.name,
                "brand": product.brand,
                "ingredients": ingredients[:10],
                "safety_score": product.safety_score,
                "image_url": product.image_url,
            }
        )
        if len(results) >= limit:
            break

    return results


def _product_to_result(product: Product) -> dict:
    """Convert a Product model to a result dict with all frontend-needed fields."""
    ingredients = parse_ingredients(product.ingredients_text or "")
    has_ingredients = bool(ingredients)

    if not has_ingredients:
        safety_badge = "unverified"
        safety_check_passed = None
    elif product.safety_score is not None and product.safety_score >= 7.0:
        safety_badge = "safe"
        safety_check_passed = True
    else:
        safety_badge = "safe"
        safety_check_passed = True

    # Check for ingredient interactions within the product
    interactions = find_ingredient_interactions(ingredients) if ingredients else []

    return {
        "id": str(product.id),
        "name": product.name,
        "brand": product.brand,
        "image_url": product.image_url,
        "key_ingredients": ingredients[:5],
        "categories": product.categories or [],
        "safety_score": product.safety_score,
        "safety_badge": safety_badge,
        "safety_check_passed": safety_check_passed,
        "data_completeness": product.data_completeness or 0.0,
        "ingredient_interactions": interactions,
        "fit_reasons": [],
    }


async def hybrid_search(
    db: AsyncSession,
    query: str,
    allergens: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Hybrid search: Postgres ILIKE (primary) + ChromaDB vector (secondary).

    Results are merged with deduplication, allergen-filtered, and enriched.
    """
    seen_ids: set[str] = set()
    results: list[dict] = []

    # 1. Postgres keyword search (primary — reliable, handles partial data)
    keyword_products = await search_products(db, query, limit=limit * 2)
    for product in keyword_products:
        pid = str(product.id)
        if pid in seen_ids:
            continue
        seen_ids.add(pid)

        result = _product_to_result(product)

        # Allergen pre-filtering
        if allergens and result["key_ingredients"]:
            ingredients = parse_ingredients(product.ingredients_text or "")
            matches = find_allergen_matches(ingredients, allergens)
            if matches:
                logger.info(
                    "Product filtered by allergen",
                    product=product.name,
                    matches=[m["ingredient"] for m in matches],
                )
                continue

        results.append(result)

    # 2. ChromaDB vector search (secondary — handles "vibes" queries)
    try:
        collection = get_or_create_collection()
        vector_results = search_similar(collection, query, n_results=limit)
        for vr in vector_results:
            vid = vr["id"]
            if vid in seen_ids:
                continue
            seen_ids.add(vid)

            # Look up the full product from Postgres
            stmt = select(Product).where(Product.id == vid)
            db_result = await db.execute(stmt)
            product = db_result.scalar_one_or_none()  # type: ignore[assignment]
            if not product:
                continue

            result = _product_to_result(product)

            # Allergen pre-filtering
            if allergens and result["key_ingredients"]:
                ingredients = parse_ingredients(product.ingredients_text or "")
                matches = find_allergen_matches(ingredients, allergens)
                if matches:
                    continue

            results.append(result)
    except Exception as e:
        logger.warning("ChromaDB vector search failed, using keyword only", error=str(e))

    return results[:limit]
