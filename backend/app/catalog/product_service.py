import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.ingredient_interactions import find_ingredient_interactions
from app.catalog.ingredient_parser import find_allergen_matches, parse_ingredients
from app.core.vector_store import search_hybrid as zvec_search
from app.models.product import Product

logger = structlog.get_logger()


async def search_products(
    db: AsyncSession,
    query: str = "",
    limit: int = 10,
) -> list[Product]:
    stmt = select(Product)
    if query:
        # Split multi-word queries into individual terms so each can match independently
        terms = query.split()
        term_filters = []
        for term in terms:
            escaped = term.replace("%", r"\%").replace("_", r"\_")
            term_filters.append(
                or_(
                    Product.name.ilike(f"%{escaped}%"),
                    Product.brand.ilike(f"%{escaped}%"),
                    Product.ingredients_text.ilike(f"%{escaped}%"),
                )
            )
        if term_filters:
            # Match any term (OR) to maximize recall
            stmt = stmt.where(or_(*term_filters))
    stmt = stmt.order_by(Product.safety_score.desc().nullslast()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


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
        safety_badge = "caution"
        safety_check_passed = False

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
    """Hybrid search: zvec vector (primary) + Postgres ILIKE (fallback).

    Results are merged with deduplication, allergen-filtered, and enriched.
    """
    seen_ids: set[str] = set()
    results: list[dict] = []

    # 1. zvec hybrid search (primary — semantic + lexical with RRF re-ranking)
    try:
        vector_results = zvec_search(query, n_results=limit)
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
        logger.warning("zvec vector search failed, using keyword only", error=str(e))

    # 2. Postgres keyword search (fallback — handles partial data)
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

    return results[:limit]
