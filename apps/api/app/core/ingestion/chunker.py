"""Text chunking with configurable size and overlap."""
import uuid
from dataclasses import dataclass, field
from langchain.text_splitter import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    file_name: str
    chunk_index: int
    text: str
    # optional metadata filled in by parser if available
    page_number: int | None = None
    section_title: str | None = None
    token_count: int = 0
    extra: dict = field(default_factory=dict)


def chunk_document(
    text: str,
    document_id: str,
    file_name: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)
    chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        chunks.append(
            Chunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                file_name=file_name,
                chunk_index=idx,
                text=chunk_text,
                token_count=len(chunk_text.split()),  # rough word count proxy
            )
        )
    return chunks
