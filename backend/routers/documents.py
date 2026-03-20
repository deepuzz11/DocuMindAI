from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.rag_engine import list_documents, delete_document

router = APIRouter()


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    total_chunks: int


@router.get("/documents", response_model=list[DocumentInfo])
def get_documents():
    return list_documents()


@router.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": f"Document {doc_id} removed successfully."}
