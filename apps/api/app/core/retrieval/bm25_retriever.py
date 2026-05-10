"""
BM25 lexical retrieval service.

The BM25 index is built in memory from the JSONL corpus on first use,
then cached for the lifetime of the process. Call invalidate() after
new documents are ingested so the next query rebuilds the index.
"""
import time
import logging
from typing import Optional

from rank_bm25 import BM25Okapi

from app.config import settings
from app.core.ingestion.corpus_store import load_corpus

logger = logging.getLogger(__name__)

# Module-level cache
_index: Optional[BM25Okapi] = None
_corpus_records: list[dict] = []


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return text.lower().split()


def _build_index() -> None:
    global _index, _corpus_records
    _corpus_records = load_corpus()
    if not _corpus_records:
        _index = None
        logger.warning("BM25 corpus is empty — no documents ingested yet.")
        return
    tokenized = [_tokenize(r["text"]) for r in _corpus_records]
    _index = BM25Okapi(tokenized)
    logger.info("BM25 index built over %d chunks.", len(_corpus_records))


def invalidate() -> None:
    """Force index rebuild on next query (call after new ingestion)."""
    global _index, _corpus_records
    _index = None
    _corpus_records = []


def retrieve_bm25(query: str, k: int | None = None) -> tuple[list[dict], float]:
    """
    Retrieve top-k BM25 candidates for a query.

    Returns (candidates, latency_ms).
    Each candidate: {text, metadata, score, retriever}
    """
    global _index, _corpus_records

    k = k or settings.retrieval_top_k

    start = time.perf_counter()

    if _index is None:
        _build_index()

    if _index is None or not _corpus_records:
        return [], round((time.perf_counter() - start) * 1000, 1)

    tokens = _tokenize(query)
    scores = _index.get_scores(tokens)

    # Pair each score with its corpus record and sort descending
    ranked = sorted(
        zip(scores, _corpus_records),
        key=lambda x: x[0],
        reverse=True,
    )
    top = ranked[:k]

    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    candidates = []
    for score, record in top:
        if score <= 0:
            # BM25 score of 0 means no term overlap — skip
            continue
        candidates.append(
            {
                "text": record["text"],
                "metadata": {
                    "chunk_id": record["chunk_id"],
                    "document_id": record["document_id"],
                    "file_name": record["file_name"],
                    "chunk_index": record["chunk_index"],
                },
                "score": round(float(score), 4),
                "retriever": "bm25",
            }
        )

    logger.info(
        "BM25 retrieval: %d results (of %d non-zero) in %.0fms",
        len(candidates),
        sum(1 for s, _ in ranked if s > 0),
        latency_ms,
    )
    return candidates, latency_ms
