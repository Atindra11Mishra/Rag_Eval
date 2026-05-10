from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    file_name: str
    parse_status: str
    num_chunks: int
    error: str | None = None
