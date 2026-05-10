"""Document parsing: PDF and plain text."""
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    text: str
    file_name: str
    num_pages: int | None = None
    parse_status: str = "ok"
    error: str | None = None


def parse_file(file_path: Path) -> ParsedDocument:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(file_path)
    elif suffix in {".txt", ".md"}:
        return _parse_text(file_path)
    else:
        return ParsedDocument(
            text="",
            file_name=file_path.name,
            parse_status="unsupported",
            error=f"Unsupported file type: {suffix}",
        )


def _parse_pdf(file_path: Path) -> ParsedDocument:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(file_path))
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        raw_text = "\n".join(pages_text)
        num_pages = len(doc)
        doc.close()
        return ParsedDocument(
            text=raw_text,
            file_name=file_path.name,
            num_pages=num_pages,
            parse_status="ok",
        )
    except Exception as exc:
        logger.error("PDF parse failed for %s: %s", file_path.name, exc)
        return ParsedDocument(
            text="",
            file_name=file_path.name,
            parse_status="error",
            error=str(exc),
        )


def _parse_text(file_path: Path) -> ParsedDocument:
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return ParsedDocument(
            text=text,
            file_name=file_path.name,
            parse_status="ok",
        )
    except Exception as exc:
        logger.error("Text parse failed for %s: %s", file_path.name, exc)
        return ParsedDocument(
            text="",
            file_name=file_path.name,
            parse_status="error",
            error=str(exc),
        )
