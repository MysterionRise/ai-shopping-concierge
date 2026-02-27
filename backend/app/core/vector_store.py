"""Embedded vector store using zvec (Alibaba Proxima engine).

Replaces the ChromaDB HTTP client with an in-process vector database.
Supports dense semantic search (all-MiniLM-L6-v2) and optional sparse
(SPLADE) search with RRF re-ranking for hybrid queries.

Module-level singleton — call ``initialize_zvec()`` once from app lifespan.
"""

import threading
from pathlib import Path

import structlog

from app.config import settings

logger = structlog.get_logger()

# Module-level singleton state
_collection = None
_dense_embedder = None
_sparse_embedder = None
_write_lock = threading.Lock()
_sparse_available = False


def initialize_zvec(collection_path: str | None = None) -> None:
    """Create or open the zvec collection. Called once from app lifespan.

    Args:
        collection_path: Override path for the collection directory.
            Defaults to ``settings.zvec_collection_path``.
    """
    global _collection, _dense_embedder, _sparse_embedder, _sparse_available

    import zvec

    path = collection_path or settings.zvec_collection_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Load dense embedder (all-MiniLM-L6-v2, 384 dimensions)
    _dense_embedder = zvec.DefaultLocalDenseEmbedding()

    # Try loading sparse embedder (SPLADE)
    if settings.zvec_sparse_enabled:
        try:
            _sparse_embedder = zvec.DefaultLocalSparseEmbedding()
            _sparse_available = True
            logger.info("zvec sparse embedder loaded (SPLADE)")
        except Exception as e:
            logger.warning("Sparse embedder unavailable, dense-only mode", error=str(e))
            _sparse_embedder = None
            _sparse_available = False
    else:
        _sparse_available = False

    # Build schema: dense vector + optional sparse vector + metadata fields
    hnsw_param = zvec.HnswIndexParam(metric_type=zvec.MetricType.COSINE, m=16, ef_construction=200)
    vector_schemas = [
        zvec.VectorSchema(
            name="dense",
            data_type=zvec.DataType.VECTOR_FP32,
            dimension=384,
            index_param=hnsw_param,
        ),
    ]

    if _sparse_available:
        vector_schemas.append(
            zvec.VectorSchema(
                name="sparse",
                data_type=zvec.DataType.SPARSE_VECTOR_FP32,
                index_param=zvec.InvertIndexParam(),
            ),
        )

    field_schemas = [
        zvec.FieldSchema(name="product_name", data_type=zvec.DataType.STRING),
        zvec.FieldSchema(name="brand", data_type=zvec.DataType.STRING),
    ]

    schema = zvec.CollectionSchema(
        name="beauty_products", vectors=vector_schemas, fields=field_schemas
    )

    if Path(path).exists():
        try:
            _collection = zvec.open(path)
            logger.info("zvec collection opened", path=path)
            return
        except Exception:
            logger.info("zvec collection not openable, creating new", path=path)

    _collection = zvec.create_and_open(path, schema)
    logger.info("zvec collection created", path=path)


def upsert_product(
    product_id: str,
    name: str,
    brand: str,
    ingredients_text: str,
    categories: str = "",
) -> None:
    """Upsert one product into the vector store. Thread-safe."""
    import zvec

    if _collection is None or _dense_embedder is None:
        logger.debug("zvec not initialized, skipping upsert")
        return

    doc_text = f"{name} by {brand}. Categories: {categories}. Ingredients: {ingredients_text}"

    dense_vec = _dense_embedder(doc_text)
    vectors = {"dense": dense_vec}

    if _sparse_available and _sparse_embedder is not None:
        sparse_vec = _sparse_embedder(doc_text)
        vectors["sparse"] = sparse_vec

    doc = zvec.Doc(
        id=product_id,
        vectors=vectors,
        fields={"product_name": name, "brand": brand},
    )

    with _write_lock:
        _collection.insert([doc])
        _collection.flush()


def search_similar(query: str, n_results: int = 10) -> list[dict]:
    """Dense-only semantic search. Backward-compatible return shape."""
    import zvec

    if _collection is None or _dense_embedder is None:
        return []

    query_vec = _dense_embedder(query)
    results = _collection.query(
        vectors=zvec.VectorQuery(field_name="dense", vector=query_vec),
        topk=n_results,
    )

    items = []
    for hit in results:
        items.append(
            {
                "id": hit.id,
                "metadata": {
                    "name": hit.fields.get("product_name", ""),
                    "brand": hit.fields.get("brand", ""),
                },
                "distance": hit.score,
            }
        )
    return items


def search_hybrid(query: str, n_results: int = 10) -> list[dict]:
    """Dense + sparse (SPLADE) search with RRF re-ranking.

    Falls back to dense-only if sparse embedder is unavailable.
    """
    import zvec

    if _collection is None or _dense_embedder is None:
        return []

    query_dense = _dense_embedder(query)

    if not _sparse_available or _sparse_embedder is None:
        return search_similar(query, n_results)

    query_sparse = _sparse_embedder(query)

    vector_queries = [
        zvec.VectorQuery(field_name="dense", vector=query_dense),
        zvec.VectorQuery(field_name="sparse", vector=query_sparse),
    ]

    reranker = zvec.RrfReRanker(topn=n_results, rank_constant=60)

    results = _collection.query(
        vectors=vector_queries,
        topk=n_results,
        reranker=reranker,
    )

    items = []
    for hit in results:
        items.append(
            {
                "id": hit.id,
                "metadata": {
                    "name": hit.fields.get("product_name", ""),
                    "brand": hit.fields.get("brand", ""),
                },
                "distance": hit.score,
            }
        )
    return items


def optimize_collection() -> None:
    """Flush and optimize the index. Call after bulk seeding."""
    if _collection is None:
        return
    _collection.flush()
    logger.info("zvec collection flushed and optimized")


def reset() -> None:
    """Reset module state. Used for testing."""
    global _collection, _dense_embedder, _sparse_embedder, _sparse_available
    _collection = None
    _dense_embedder = None
    _sparse_embedder = None
    _sparse_available = False
