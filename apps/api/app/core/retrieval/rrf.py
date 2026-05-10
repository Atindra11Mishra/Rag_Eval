"""
Reciprocal Rank Fusion (RRF) for merging ranked result lists.

Formula: RRF(d) = sum_r( 1 / (k + rank_r(d)) )
where k is the fusion constant (default 60, standard in literature).

Each candidate list must be pre-sorted best-first.
Candidates are identified by chunk_id from metadata.
"""
from app.config import settings


def reciprocal_rank_fusion(
    *ranked_lists: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Merge N ranked candidate lists using RRF.

    Args:
        *ranked_lists: Any number of candidate lists, each sorted best-first.
                       Each item must have metadata['chunk_id'].
        k: Fusion constant. Higher k reduces the impact of top ranks.

    Returns:
        Merged list sorted by RRF score descending.
        Each item includes:
          text, metadata, rrf_score, retriever (comma-joined source retrievers),
          vector_rank, bm25_rank (1-based, None if not in that list).
    """
    # Accumulate RRF scores and provenance per chunk_id
    scores: dict[str, float] = {}
    provenance: dict[str, dict] = {}  # chunk_id -> merged record

    for ranked_list in ranked_lists:
        for rank_0, candidate in enumerate(ranked_list):
            chunk_id = candidate["metadata"].get("chunk_id", "")
            if not chunk_id:
                continue
            rank_1 = rank_0 + 1  # 1-based
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank_1)

            if chunk_id not in provenance:
                provenance[chunk_id] = {
                    "text": candidate["text"],
                    "metadata": candidate["metadata"],
                    "source_retrievers": [],
                    "source_ranks": {},
                    "source_scores": {},
                }

            retriever = candidate.get("retriever", "unknown")
            provenance[chunk_id]["source_retrievers"].append(retriever)
            provenance[chunk_id]["source_ranks"][retriever] = rank_1
            provenance[chunk_id]["source_scores"][retriever] = candidate["score"]

    # Sort by RRF score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    result = []
    for chunk_id, rrf_score in ranked:
        p = provenance[chunk_id]
        result.append(
            {
                "text": p["text"],
                "metadata": p["metadata"],
                "score": round(rrf_score, 6),
                "retriever": "hybrid",
                # Debug fields
                "source_retrievers": p["source_retrievers"],
                "source_ranks": p["source_ranks"],
                "source_scores": p["source_scores"],
            }
        )

    return result
