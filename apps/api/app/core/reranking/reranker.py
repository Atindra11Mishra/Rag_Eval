"""
Cross-encoder reranking using BAAI/bge-reranker-base.

The model is loaded once and cached for the process lifetime.
Reranking runs on CPU by default; set device="cuda" if a GPU is available.
"""
import time
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_model: Any | None = None


def _get_model() -> Any:
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        logger.info("Loading reranker model: %s", settings.reranker_model)
        _model = CrossEncoder(settings.reranker_model, max_length=512)
        logger.info("Reranker model loaded.")
    return _model


def rerank(
    query: str,
    candidates: list[dict],
    top_n: int | None = None,
) -> tuple[list[dict], float]:
    """
    Rescore candidate chunks with the cross-encoder and return sorted results.

    Args:
        query: The user's question.
        candidates: List of candidate dicts (text, metadata, score, retriever, …).
        top_n: How many top chunks to return. Defaults to settings.final_top_k.

    Returns:
        (reranked_candidates, latency_ms)
        Each candidate gains a 'rerank_score' field and 'retriever' is updated
        to include "+reranker".
    """
    top_n = top_n or settings.final_top_k

    if not candidates:
        return [], 0.0

    model = _get_model()

    pairs = [(query, c["text"]) for c in candidates]

    start = time.perf_counter()
    scores = model.predict(pairs)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    # Attach rerank scores
    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    # Sort descending by rerank score
    reranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)

    # Tag retriever to reflect reranking
    for c in reranked:
        c["retriever"] = c.get("retriever", "unknown") + "+reranker"

    logger.info(
        "Reranked %d candidates → top %d in %.0fms",
        len(candidates),
        top_n,
        latency_ms,
    )

    return reranked[:top_n], latency_ms
