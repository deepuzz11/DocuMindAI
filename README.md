# DocuMindAI 

> RAG-based Document Intelligence Chatbot — upload PDFs, ask questions, get grounded answers.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?logo=chainlink)](https://langchain.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Store-blue)](https://faiss.ai)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)

## Architecture

```
PDF Upload → PyMuPDF (extract) → RecursiveCharacterTextSplitter (chunk)
          → OpenAI Embeddings → FAISS (store)

User Query → Embed → FAISS similarity search (top-k)
           → Prompt injection → LLM (GPT-4o) → Streamed answer
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| RAG Framework | LangChain |
| Vector Store | FAISS (CPU) |
| PDF Parsing | PyMuPDF (fitz) |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | GPT-4o (configurable) |
| Frontend | React 18 |
| Containerisation | Docker + Docker Compose |

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/deepuzz11/DocuMindAI.git
cd DocuMindAI

cp backend/.env.example backend/.env
# Edit backend/.env → add your OPENAI_API_KEY
```

### 2. Run with Docker (recommended)

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### 3. Run locally (dev)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload` | Upload & ingest a document |
| `POST` | `/api/v1/chat` | Ask a question (JSON response) |
| `POST` | `/api/v1/chat/stream` | Ask a question (SSE streaming) |
| `GET`  | `/api/v1/documents` | List all indexed documents |
| `DELETE` | `/api/v1/documents/{id}` | Remove a document from the index |

## Key Design Decisions

**Why FAISS over Pinecone/Weaviate?**  
Zero infra overhead, runs locally, persists to disk. Perfect for a portfolio project — you control everything.

**Why RecursiveCharacterTextSplitter?**  
Respects natural text boundaries (paragraphs → sentences → words) before falling back to character splits. Better context coherence than naive fixed-size splitting.

**Why chunk_overlap=200?**  
Prevents cutting off context at chunk boundaries — a sentence split across two chunks is still fully represented in both.

**Document deletion via rebuild?**  
FAISS doesn't support per-vector deletion. The rebuild-on-delete pattern is correct for small-to-medium corpora and keeps the implementation simple.

## Configuration

All settings live in `backend/.env`:

```env
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o            # or gpt-3.5-turbo, mistral, etc.
CHUNK_SIZE=1000              # characters per chunk
CHUNK_OVERLAP=200            # overlap between consecutive chunks
TOP_K=5                      # number of chunks retrieved per query
```

## Upgrading to Local Embeddings (No OpenAI)

1. `pip install sentence-transformers`
2. In `rag_engine.py`, replace `OpenAIEmbeddings` with:

```python
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
```

## Resume Line

> Built **DocuMindAI**, a production-grade RAG chatbot using **LangChain** and **FAISS** for context-aware PDF querying, with a **FastAPI** backend, streaming SSE responses, and a **React** frontend. Implemented the full ingestion pipeline: PDF extraction (PyMuPDF) → recursive chunking → OpenAI embeddings → vector similarity search → grounded LLM generation.

## License

MIT