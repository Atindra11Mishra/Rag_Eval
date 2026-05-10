"""
Telemetry logger: persists query-level metrics and retrieval traces to Supabase.

If Supabase is not configured (empty URL/key), logs are emitted to the Python
logger only — the API continues to function without interruption.
"""
import logging
import uuid
from typing import Optional

from app.config import settings
from app.core.telemetry.cost import estimate_cost

logger = logging.getLogger(__name__)

_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if not settings.supabase_url or not settings.supabase_key:
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client connected.")
    except Exception as exc:
        logger.warning("Supabase connection failed: %s", exc)
        _supabase_client = None
    return _supabase_client


def log_query(
    query_text: str,
    answer_text: str,
    retrieval_mode: str,
    retrieval_latency_ms: float,
    generation_latency_ms: float,
    total_latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    llm_model: str,
    final_chunks: list[dict],
    all_candidates: Optional[list[dict]] = None,
) -> Optional[str]:
    """
    Log a query execution to Supabase (or just to Python logger if not configured).
    Returns the query_log_id (UUID string) or None.
    """
    cost = estimate_cost(llm_model, input_tokens, output_tokens)
    query_log_id = str(uuid.uuid4())

    log_msg = (
        f"Query logged | mode={retrieval_mode} "
        f"total={total_latency_ms:.0f}ms "
        f"tokens={input_tokens+output_tokens} cost=${cost:.6f}"
    )
    logger.info(log_msg)

    client = _get_supabase()
    if client is None:
        return query_log_id  # no-op persistence; ID still returned for tracing

    try:
        client.table("query_logs").insert({
            "id": query_log_id,
            "query_text": query_text,
            "answer_text": answer_text,
            "retrieval_mode": retrieval_mode,
            "retrieval_latency_ms": retrieval_latency_ms,
            "generation_latency_ms": generation_latency_ms,
            "total_latency_ms": total_latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": cost,
            "llm_model": llm_model,
            "embedding_model": settings.embedding_model,
        }).execute()

        # Log retrieval traces
        selected_ids = {c["metadata"].get("chunk_id") for c in final_chunks}
        candidate_pool = all_candidates or final_chunks

        trace_rows = []
        for rank, candidate in enumerate(candidate_pool, 1):
            meta = candidate.get("metadata", {})
            chunk_id = meta.get("chunk_id", "")
            trace_rows.append({
                "query_log_id": query_log_id,
                "retriever_type": candidate.get("retriever", "unknown"),
                "chunk_id": chunk_id,
                "file_name": meta.get("file_name", ""),
                "chunk_index": meta.get("chunk_index", -1),
                "retrieval_rank": rank,
                "retrieval_score": candidate.get("score", 0),
                "rerank_score": candidate.get("rerank_score"),
                "selected_for_generation": chunk_id in selected_ids,
            })

        if trace_rows:
            client.table("retrieval_logs").insert(trace_rows).execute()

    except Exception as exc:
        logger.error("Supabase logging failed: %s", exc)

    return query_log_id


def log_eval_run(run: dict) -> None:
    """Persist an eval run summary to Supabase."""
    client = _get_supabase()
    if client is None:
        return
    try:
        client.table("eval_runs").insert({
            "run_name": run["run_name"],
            "dataset_version": run["dataset_version"],
            "config_version": run["config_snapshot"],
            "created_at": run["created_at"],
            "mean_faithfulness": run.get("mean_faithfulness"),
            "mean_context_precision": run.get("mean_context_precision"),
            "mean_context_recall": run.get("mean_context_recall"),
            "mean_answer_relevance": run.get("mean_answer_relevance"),
            "pass_fail": run.get("pass_fail"),
        }).execute()
    except Exception as exc:
        logger.error("Supabase eval_run logging failed: %s", exc)
