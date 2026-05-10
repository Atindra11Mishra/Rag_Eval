"""Query endpoint: vector | BM25 | hybrid retrieval → rerank → grounded answer."""
import time
import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.retrieval.vector_retriever import retrieve_vector
from app.core.retrieval.bm25_retriever import retrieve_bm25
from app.core.retrieval.hybrid_retriever import retrieve_hybrid
from app.core.reranking.reranker import rerank
from app.core.generation.generator import generate_answer
from app.core.telemetry.logger import log_query
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
    RetrievalDebug,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_schema(chunks: list[dict]) -> list[RetrievedChunk]:
    result = []
    for chunk in chunks:
        meta = chunk["metadata"]
        result.append(
            RetrievedChunk(
                chunk_id=meta.get("chunk_id", ""),
                file_name=meta.get("file_name", ""),
                chunk_index=meta.get("chunk_index", -1),
                text=chunk["text"],
                score=chunk.get("rerank_score", chunk["score"]),
                retriever=chunk.get("retriever", "unknown"),
                source_retrievers=chunk.get("source_retrievers", []),
                source_ranks=chunk.get("source_ranks", {}),
                source_scores=chunk.get("source_scores", {}),
            )
        )
    return result


@router.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    top_k = request.top_k or settings.retrieval_top_k
    mode = request.retrieval_mode or settings.retrieval_mode
    total_start = time.perf_counter()

    vec_candidates: list[dict] = []
    bm25_candidates: list[dict] = []
    active_candidates: list[dict] = []
    retrieval_latency_ms = 0.0

    if mode == "vector":
        vec_candidates, retrieval_latency_ms = retrieve_vector(question, k=top_k)
        active_candidates = vec_candidates

    elif mode == "bm25":
        bm25_candidates, retrieval_latency_ms = retrieve_bm25(question, k=top_k)
        active_candidates = bm25_candidates

    elif mode == "hybrid":
        fused, debug_info = retrieve_hybrid(
            question, k=top_k, rrf_k=settings.rrf_k
        )
        vec_candidates = debug_info["vector_candidates"]
        bm25_candidates = debug_info["bm25_candidates"]
        retrieval_latency_ms = debug_info["total_latency_ms"]
        active_candidates = fused

    else:
        raise HTTPException(status_code=400, detail=f"Unknown retrieval_mode: {mode}")

    if not active_candidates:
        raise HTTPException(
            status_code=404,
            detail=f"No results found. Upload documents first. (mode={mode})",
        )

    # Reranking step — applied to top candidate_depth candidates
    rerank_latency_ms = 0.0
    if settings.reranker_enabled:
        candidate_pool = active_candidates[: settings.reranker_candidate_depth]
        final_chunks, rerank_latency_ms = rerank(
            question, candidate_pool, top_n=settings.reranker_top_n
        )
    else:
        final_chunks = active_candidates[: settings.final_top_k]

    # Include rerank latency in retrieval total for simplicity in response
    retrieval_latency_ms = round(retrieval_latency_ms + rerank_latency_ms, 1)

    gen_result = generate_answer(question, final_chunks)
    total_latency_ms = round((time.perf_counter() - total_start) * 1000, 1)

    # Fire-and-forget telemetry (errors are logged but don't fail the request)
    try:
        log_query(
            query_text=question,
            answer_text=gen_result.answer,
            retrieval_mode=mode,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=gen_result.latency_ms,
            total_latency_ms=total_latency_ms,
            input_tokens=gen_result.input_tokens,
            output_tokens=gen_result.output_tokens,
            llm_model=gen_result.model,
            final_chunks=final_chunks,
            all_candidates=active_candidates,
        )
    except Exception as exc:
        logger.warning("Telemetry log failed (non-fatal): %s", exc)

    return QueryResponse(
        question=question,
        answer=gen_result.answer,
        retrieval_mode=mode,
        sources=_to_schema(final_chunks),
        debug=RetrievalDebug(
            vector_candidates=_to_schema(vec_candidates),
            bm25_candidates=_to_schema(bm25_candidates),
        ),
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=gen_result.latency_ms,
        total_latency_ms=total_latency_ms,
        input_tokens=gen_result.input_tokens,
        output_tokens=gen_result.output_tokens,
        model=gen_result.model,
    )
