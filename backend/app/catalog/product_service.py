import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.ingredient_parser import find_allergen_matches, parse_ingredients
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
