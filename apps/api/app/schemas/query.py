from typing import Literal
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None
    retrieval_mode: Literal["vector", "bm25", "hybrid"] | None = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    file_name: str
    chunk_index: int
    text: str
    score: float
    retriever: str
    # RRF provenance (populated for hybrid mode, empty otherwise)
    source_retrievers: list[str] = []
    source_ranks: dict[str, int] = {}
    source_scores: dict[str, float] = {}


class RetrievalDebug(BaseModel):
    vector_candidates: list[RetrievedChunk]
    bm25_candidates: list[RetrievedChunk]


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieval_mode: str
    sources: list[RetrievedChunk]
    debug: RetrievalDebug
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    input_tokens: int
    output_tokens: int
    model: str
