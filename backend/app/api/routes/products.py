import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models.product import Product

logger = structlog.get_logger()

router = APIRouter(prefix="/products", tags=["products"])


class ProductResponse(BaseModel):
    id: str
    openbf_code: str
    name: str
    brand: str | None
    categories: list
    ingredients: list
    ingredients_text: str | None
    image_url: str | None
    safety_score: float | None

    model_config = {"from_attributes": True}


@router.get("/search")
async def search_products(
    q: str = "",
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session),
) -> list[ProductResponse]:
    limit = max(1, min(limit, 100))
    stmt = select(Product)
    if q:
        # Escape ILIKE wildcards in user input
        escaped_q = q.replace("%", r"\%").replace("_", r"\_")
        stmt = stmt.where(
            Product.name.ilike(f"%{escaped_q}%") | Product.brand.ilike(f"%{escaped_q}%")
        )
    stmt = stmt.order_by(Product.safety_score.desc().nullslast()).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ProductResponse(
            id=str(p.id),
            openbf_code=p.openbf_code,
            name=p.name,
            brand=p.brand,
            categories=list(p.categories or []),
            ingredients=list(p.ingredients or []),
            ingredients_text=p.ingredients_text,
            image_url=p.image_url,
            safety_score=p.safety_score,
        )
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        id=str(product.id),
        openbf_code=product.openbf_code,
        name=product.name,
        brand=product.brand,
        categories=list(product.categories or []),
        ingredients=list(product.ingredients or []),
        ingredients_text=product.ingredients_text,
        image_url=product.image_url,
        safety_score=product.safety_score,
    )
