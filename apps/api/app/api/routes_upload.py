"""Upload endpoint: receives a file, runs ingestion pipeline."""
import shutil
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.core.ingestion.pipeline import ingest_file
from app.schemas.upload import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
UPLOAD_DIR = Path(settings.chroma_persist_dir).parent / "raw"


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename

    # Save uploaded file to disk
    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save file.")
    finally:
        await file.close()

    # Run ingestion pipeline
    result = ingest_file(dest)

    return UploadResponse(
        document_id=result.document_id,
        file_name=result.file_name,
        parse_status=result.parse_status,
        num_chunks=result.num_chunks,
        error=result.error,
    )
