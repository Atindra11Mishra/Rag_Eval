from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Retrieval
    # Mode options: "vector" | "bm25" | "hybrid"
    retrieval_mode: str = "hybrid"
    retrieval_top_k: int = 10
    final_top_k: int = 4  # chunks sent to generation

    # BM25
    bm25_corpus_path: str = str(BASE_DIR / "data" / "bm25_corpus.jsonl")

    # RRF
    rrf_k: int = 60  # fusion constant

    # Reranking
    reranker_enabled: bool = True
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_top_n: int = 4    # final chunks after reranking
    reranker_candidate_depth: int = 20  # max candidates sent to reranker

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 150

    # ChromaDB
    chroma_persist_dir: str = str(BASE_DIR / "data" / "chroma")
    chroma_collection_name: str = "rag_chunks"

    # Supabase (Phase 7 — optional now)
    supabase_url: str = ""
    supabase_key: str = ""


settings = Settings()
