"""ChromaDB vector store wrapper."""
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.config import settings
from app.core.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

_chroma_client: chromadb.PersistentClient | None = None
_vector_store: Chroma | None = None


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


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
