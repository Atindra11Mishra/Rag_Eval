"""ChromaDB vector store wrapper."""
from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.core.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

_chroma_client: chromadb.PersistentClient | None = None
_vector_store: Chroma | None = None
_embedding_model: SentenceTransformer | None = None


class LocalSentenceTransformerEmbeddings(Embeddings):
    def _get_model(self) -> SentenceTransformer:
        global _embedding_model
        if _embedding_model is None:
            logger.info("Loading embedding model: %s", settings.embedding_model)
            _embedding_model = SentenceTransformer(settings.embedding_model)
        return _embedding_model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self._get_model().encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._get_model().encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vector.tolist()


def _get_embeddings() -> Embeddings:
    return LocalSentenceTransformerEmbeddings()


def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        _vector_store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=_get_embeddings(),
            persist_directory=settings.chroma_persist_dir,
        )
        logger.info("ChromaDB loaded from %s", settings.chroma_persist_dir)
    return _vector_store


def index_chunks(chunks: list[Chunk]) -> int:
    """Embed and store chunks. Returns number of chunks indexed."""
    if not chunks:
        return 0

    store = get_vector_store()

    texts = [c.text for c in chunks]
    metadatas = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "file_name": c.file_name,
            "chunk_index": c.chunk_index,
            "page_number": c.page_number or -1,
            "token_count": c.token_count,
        }
        for c in chunks
    ]
    ids = [c.chunk_id for c in chunks]

    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    logger.info("Indexed %d chunks into ChromaDB", len(chunks))
    return len(chunks)


def similarity_search(query: str, k: int) -> list[dict]:
    """Return top-k chunks with text, metadata, and similarity score."""
    store = get_vector_store()
    results = store.similarity_search_with_relevance_scores(query, k=k)

    output = []
    for doc, score in results:
        output.append(
            {
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": round(score, 4),
                "retriever": "vector",
            }
        )
    return output
