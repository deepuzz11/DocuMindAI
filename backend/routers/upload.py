import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from core.config import get_settings
from core.rag_engine import ingest_document

router = APIRouter()
settings = get_settings()


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_created: int
    total_characters: int
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {settings.allowed_extensions}",
        )

    # Validate size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max allowed: {settings.max_file_size_mb} MB",
        )

    # Save to disk
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    file_path.write_bytes(contents)

    # Ingest
    try:
        result = ingest_document(str(file_path), file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return UploadResponse(
        **result,
        message=f"Successfully ingested '{file.filename}' into {result['chunks_created']} chunks.",
    )
