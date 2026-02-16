import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

BASE_URL = "https://world.openbeautyfacts.org"


class OpenBFProduct(BaseModel):
    code: str
    product_name: str = ""
    brands: str = ""
    categories: str = ""
    ingredients_text: str = ""
    image_url: str = ""


class OpenBeautyFactsClient:
    def __init__(self, timeout: float = 30.0):
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "BeautyConcierge/0.1"},
        )

    async def search(
        self,
        query: str = "",
        categories: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> list[OpenBFProduct]:
        params = {
            "action": "process",
            "json": "true",
            "page": page,
            "page_size": page_size,
            "fields": "code,product_name,brands,categories,ingredients_text,image_url",
        }
        if query:
            params["search_terms"] = query
        if categories:
            params["tagtype_0"] = "categories"
            params["tag_contains_0"] = "contains"
            params["tag_0"] = categories

        try:
            response = await self.client.get("/cgi/search.pl", params=params)
            response.raise_for_status()
            data = response.json()
            products = []
            for item in data.get("products", []):
                try:
                    products.append(
                        OpenBFProduct(
                            code=item.get("code", ""),
                            product_name=item.get("product_name", ""),
                            brands=item.get("brands", ""),
                            categories=item.get("categories", ""),
                            ingredients_text=item.get("ingredients_text", ""),
                            image_url=item.get("image_url", ""),
                        )
                    )
                except Exception:
                    continue
            return products
        except Exception as e:
            logger.error("OpenBeautyFacts search failed", error=str(e))
            return []

    async def get_by_barcode(self, barcode: str) -> OpenBFProduct | None:
        try:
            response = await self.client.get(f"/api/v2/product/{barcode}")
            response.raise_for_status()
            data = response.json()
            product = data.get("product", {})
            if not product:
                return None
            return OpenBFProduct(
                code=product.get("code", barcode),
                product_name=product.get("product_name", ""),
                brands=product.get("brands", ""),
                categories=product.get("categories", ""),
                ingredients_text=product.get("ingredients_text", ""),
                image_url=product.get("image_url", ""),
            )
        except Exception as e:
            logger.error("OpenBeautyFacts barcode lookup failed", barcode=barcode, error=str(e))
            return None

    async def close(self):
        await self.client.aclose()
