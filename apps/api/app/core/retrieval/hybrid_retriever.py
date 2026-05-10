"""
Hybrid retrieval orchestrator: vector + BM25 → RRF fusion.
"""
import time
import logging

from app.config import settings
from app.core.retrieval.vector_retriever import retrieve_vector
from app.core.retrieval.bm25_retriever import retrieve_bm25
from app.core.retrieval.rrf import reciprocal_rank_fusion

logger = logging.getLogger(__name__)


def retrieve_hybrid(
    query: str,
    k: int | None = None,
    rrf_k: int = 60,
) -> tuple[list[dict], dict]:
    """
    Run vector and BM25 retrieval, fuse with RRF.

    Returns:
        (fused_candidates, debug_info)

        fused_candidates: list sorted by RRF score, each item has
            text, metadata, score (rrf), retriever="hybrid",
            source_retrievers, source_ranks, source_scores

        debug_info: {
            vector_candidates, bm25_candidates,
            vec_latency_ms, bm25_latency_ms, fusion_latency_ms,
            total_latency_ms
        }
    """
    k = k or settings.retrieval_top_k

    vec_candidates, vec_latency = retrieve_vector(query, k=k)
    bm25_candidates, bm25_latency = retrieve_bm25(query, k=k)

    fusion_start = time.perf_counter()
    fused = reciprocal_rank_fusion(vec_candidates, bm25_candidates, k=rrf_k)
    fusion_latency = round((time.perf_counter() - fusion_start) * 1000, 1)

    total_latency = round(vec_latency + bm25_latency + fusion_latency, 1)

    logger.info(
        "Hybrid retrieval: vec=%d bm25=%d fused=%d | latency=%.0fms",
        len(vec_candidates),
        len(bm25_candidates),
        len(fused),
        total_latency,
    )

    debug_info = {
        "vector_candidates": vec_candidates,
        "bm25_candidates": bm25_candidates,
        "vec_latency_ms": vec_latency,
        "bm25_latency_ms": bm25_latency,
        "fusion_latency_ms": fusion_latency,
        "total_latency_ms": total_latency,
    }

    return fused, debug_info
