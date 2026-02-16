from typing import Any

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = structlog.get_logger()

COLLECTION_NAME = "beauty_products"


def get_chroma_client() -> Any:
    return chromadb.HttpClient(
        host=settings.chromadb_host,
        port=settings.chromadb_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_or_create_collection(client: Any = None):
    if client is None:
        client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_product(
    collection,
    product_id: str,
    name: str,
    brand: str,
    ingredients_text: str,
    categories: str = "",
):
    doc = f"{name} by {brand}. Categories: {categories}. Ingredients: {ingredients_text}"
    collection.upsert(
        ids=[product_id],
        documents=[doc],
        metadatas=[{"name": name, "brand": brand}],
    )


def search_similar(collection, query: str, n_results: int = 10) -> list[dict]:
    results = collection.query(query_texts=[query], n_results=n_results)
    items = []
    for i, doc_id in enumerate(results["ids"][0]):
        items.append(
            {
                "id": doc_id,
                "document": results["documents"][0][i] if results.get("documents") else "",
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "distance": results["distances"][0][i] if results.get("distances") else None,
            }
        )
    return items
