"""
RAG Engine — DocuMindAI
FREE setup: HuggingFace embeddings (local) + Groq LLM (free API)
"""

import os
import uuid
from pathlib import Path
from typing import Generator

import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

from core.config import get_settings

settings = get_settings()

# ── Prompt template ──────────────────────────────────────────────────────────

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are DocuMindAI, an intelligent document assistant.
Answer the question using ONLY the context provided below.
If the answer is not in the context, say "I couldn't find that in the uploaded documents."
Never hallucinate or use outside knowledge.

Context:
{context}

Question: {question}

Answer:""",
)

# ── Singleton FAISS store ────────────────────────────────────────────────────

_vector_store: FAISS | None = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    """Free local embeddings. Downloads ~130MB on first run, cached after."""
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def _get_llm(streaming: bool = False) -> ChatGroq:
    """Free LLM via Groq API (get key at console.groq.com)."""
    return ChatGroq(
        model="llama3-8b-8192",
        temperature=settings.llm_temperature,
        api_key=os.getenv("GROQ_API_KEY"),
        streaming=streaming,
    )


def _get_vector_store() -> FAISS | None:
    global _vector_store
    if _vector_store is None:
        index_path = Path(settings.faiss_index_path)
        if index_path.exists():
            _vector_store = FAISS.load_local(
                str(index_path),
                _get_embeddings(),
                allow_dangerous_deserialization=True,
            )
    return _vector_store


def _save_vector_store(store: FAISS) -> None:
    global _vector_store
    Path(settings.faiss_index_path).mkdir(parents=True, exist_ok=True)
    store.save_local(settings.faiss_index_path)
    _vector_store = store


# ── Ingestion ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    doc.close()
    return text


def extract_text_from_file(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in {".txt", ".md"}:
        return Path(file_path).read_text(encoding="utf-8")
    raise ValueError(f"Unsupported file type: {ext}")


def ingest_document(file_path: str, filename: str) -> dict:
    doc_id = str(uuid.uuid4())

    raw_text = extract_text_from_file(file_path)
    if not raw_text.strip():
        raise ValueError("No extractable text found in document.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_text(raw_text)

    documents = [
        Document(
            page_content=chunk,
            metadata={
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    embeddings = _get_embeddings()
    existing_store = _get_vector_store()

    if existing_store:
        existing_store.add_documents(documents)
        _save_vector_store(existing_store)
    else:
        new_store = FAISS.from_documents(documents, embeddings)
        _save_vector_store(new_store)

    return {
        "doc_id": doc_id,
        "filename": filename,
        "chunks_created": len(chunks),
        "total_characters": len(raw_text),
    }


# ── Querying ─────────────────────────────────────────────────────────────────

def query_documents(question: str) -> dict:
    store = _get_vector_store()
    if not store:
        return {
            "answer": "No documents uploaded yet. Please upload a PDF first.",
            "sources": [],
        }

    docs_with_scores = store.similarity_search_with_score(question, k=settings.top_k)
    if not docs_with_scores:
        return {
            "answer": "I couldn't find relevant content for your question.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(doc.page_content for doc, _ in docs_with_scores)
    sources = [
        {
            "filename": doc.metadata.get("filename", "unknown"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "score": round(float(score), 4),
        }
        for doc, score in docs_with_scores
    ]

    llm = _get_llm()
    prompt = RAG_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": sources,
    }


def stream_query_documents(question: str) -> Generator[str, None, None]:
    store = _get_vector_store()
    if not store:
        yield "No documents uploaded yet."
        return

    docs_with_scores = store.similarity_search_with_score(question, k=settings.top_k)
    context = "\n\n---\n\n".join(doc.page_content for doc, _ in docs_with_scores)
    prompt = RAG_PROMPT.format(context=context, question=question)

    llm = _get_llm(streaming=True)
    for chunk in llm.stream(prompt):
        yield chunk.content


# ── Index management ─────────────────────────────────────────────────────────

def delete_document(doc_id: str) -> bool:
    store = _get_vector_store()
    if not store:
        return False

    all_docs = store.docstore._dict.values()
    remaining = [doc for doc in all_docs if doc.metadata.get("doc_id") != doc_id]

    if not remaining:
        import shutil
        shutil.rmtree(settings.faiss_index_path, ignore_errors=True)
        global _vector_store
        _vector_store = None
        return True

    embeddings = _get_embeddings()
    new_store = FAISS.from_documents(remaining, embeddings)
    _save_vector_store(new_store)
    return True


def list_documents() -> list[dict]:
    store = _get_vector_store()
    if not store:
        return []

    seen_ids: set[str] = set()
    result = []
    for doc in store.docstore._dict.values():
        doc_id = doc.metadata.get("doc_id")
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            result.append({
                "doc_id": doc_id,
                "filename": doc.metadata.get("filename"),
                "total_chunks": doc.metadata.get("total_chunks"),
            })
    return result
