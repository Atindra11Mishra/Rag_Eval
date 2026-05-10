"""Orchestrates the full ingestion flow for one document."""
import uuid
import logging
from pathlib import Path
from dataclasses import dataclass

from app.config import settings
from app.core.ingestion.parser import parse_file
from app.core.ingestion.cleaner import clean_text
from app.core.ingestion.chunker import chunk_document
from app.core.ingestion.vector_store import index_chunks
from app.core.ingestion.corpus_store import append_chunks
from app.core.retrieval.bm25_retriever import invalidate as bm25_invalidate

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    document_id: str
    file_name: str
    parse_status: str
    num_chunks: int
    error: str | None = None


def ingest_file(file_path: Path) -> IngestionResult:
    document_id = str(uuid.uuid4())
    logger.info("Ingesting %s (doc_id=%s)", file_path.name, document_id)

    # 1. Parse
    parsed = parse_file(file_path)
    if parsed.parse_status != "ok":
        return IngestionResult(
            document_id=document_id,
            file_name=file_path.name,
            parse_status=parsed.parse_status,
            num_chunks=0,
            error=parsed.error,
        )

    # 2. Clean
    clean = clean_text(parsed.text)
    if not clean.strip():
        return IngestionResult(
            document_id=document_id,
            file_name=file_path.name,
            parse_status="empty",
            num_chunks=0,
            error="Document produced no text after cleaning.",
        )

    # 3. Chunk
    chunks = chunk_document(
        text=clean,
        document_id=document_id,
        file_name=file_path.name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # 4. Embed + index into ChromaDB
    indexed = index_chunks(chunks)

    # 5. Append to BM25 corpus and invalidate cached index
    append_chunks(chunks)
    bm25_invalidate()

    return IngestionResult(
        document_id=document_id,
        file_name=file_path.name,
        parse_status="ok",
        num_chunks=indexed,
    )
