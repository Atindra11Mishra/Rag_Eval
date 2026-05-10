"""Vector retrieval from ChromaDB."""
import time
import logging

from app.config import settings
from app.core.ingestion.vector_store import similarity_search

logger = logging.getLogger(__name__)


def retrieve_vector(query: str, k: int | None = None) -> tuple[list[dict], float]:
    """
    Retrieve top-k vector matches for a query.

    Returns (candidates, latency_ms).
    Each candidate: {text, metadata, score, retriever}
    """
    k = k or settings.retrieval_top_k
    start = time.perf_counter()
    results = similarity_search(query, k=k)
    latency_ms = (time.perf_counter() - start) * 1000
    logger.info("Vector retrieval: %d results in %.0fms", len(results), latency_ms)
    return results, round(latency_ms, 1)
