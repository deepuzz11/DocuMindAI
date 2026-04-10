# DocuMindAI 

> RAG-based Document Intelligence Chatbot — upload PDFs, ask questions, get grounded answers.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?logo=chainlink)](https://langchain.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Store-blue)](https://faiss.ai)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)

## Architecture

The system follows a standard RAG (Retrieval-Augmented Generation) pattern, optimized for low latency and high accuracy using local embeddings and high-performance inference.

```mermaid
graph TD
    User([User / Client]) <--> API[FastAPI Backend]
    
    subgraph "Ingestion Pipeline"
        API --> Extraction[PyMuPDF Text Extraction]
        Extraction --> Splitting[Recursive Character Splitting]
        Splitting --> HF_Embed[Local Embeddings: BAAI/bge-small-en]
        HF_Embed --> VectorStore[(FAISS Vector Store)]
    end
    
    subgraph "Retrieval Pipeline"
        API --> Search[Similarity Search]
        Search <--> VectorStore
        Search --> Context[Prompt Context Builder]
        Context --> Groq[Groq API: Llama 3 8B]
        Groq --> Response[Final Answer]
        Response --> API
    end
    
    style User fill:#ecf0f1,stroke:#2c3e50,stroke-width:2px
    style API fill:#3498db,stroke:#2c3e50,stroke-width:2px,color:#fff
    style VectorStore fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:#fff
    style Groq fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff
```

> [!TIP]
> You can find the editable diagram source at [diagrams/architecture.drawio](diagrams/architecture.drawio). Use [draw.io](https://app.diagrams.net/) to view or edit it.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| RAG Framework | LangChain |
| Vector Store | FAISS (CPU) |
| PDF Parsing | PyMuPDF (fitz) |
| Embeddings | BAAI/bge-small-en-v1.5 (Local HuggingFace) |
| LLM | Llama 3 8B (via Groq API) |
| Frontend | React 18 + Vite |
| Containerisation | Docker + Docker Compose |

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/deepuzz11/DocuMindAI.git
cd DocuMindAI

cp backend/.env.example backend/.env
# Edit backend/.env → add your GROQ_API_KEY (get it at https://console.groq.com)
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

## License

MIT