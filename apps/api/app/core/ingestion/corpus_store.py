"""
Persists chunk text and metadata to a JSONL file so the BM25 index
can be rebuilt on restart without re-embedding anything.

One JSON object per line: {chunk_id, document_id, file_name, chunk_index, text}
"""
import json
import logging
from pathlib import Path

from app.config import settings
from app.core.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)


def _corpus_path() -> Path:
    path = Path(settings.bm25_corpus_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_chunks(chunks: list[Chunk]) -> None:
    """Append new chunks to the corpus JSONL file."""
    path = _corpus_path()
    with path.open("a", encoding="utf-8") as f:
        for chunk in chunks:
            record = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "file_name": chunk.file_name,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Appended %d chunks to BM25 corpus at %s", len(chunks), path)


def load_corpus() -> list[dict]:
    """Load all corpus records from the JSONL file."""
    path = _corpus_path()
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed corpus line: %s", line[:80])
    return records
