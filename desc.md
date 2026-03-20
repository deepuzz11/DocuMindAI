# DocuMindAI — Detailed Project Description

---

## What it is

A **RAG (Retrieval-Augmented Generation) chatbot** that lets you upload PDF documents and ask questions about them. Instead of an LLM guessing answers from training data, it retrieves actual content from your documents and generates answers grounded in that content — no hallucination.

---

## How it works (end to end)

### Ingestion Pipeline (when you upload a PDF)

1. **PDF Upload** — FastAPI receives the file, validates type and size, saves it to disk
2. **Text Extraction** — PyMuPDF (`fitz`) reads every page and pulls out raw text
3. **Chunking** — `RecursiveCharacterTextSplitter` breaks the text into overlapping chunks of 1000 characters with 200 character overlap. Overlap ensures a sentence split across two chunks still appears fully in both
4. **Embedding** — Each chunk is converted into a vector (a list of numbers representing its meaning) using `BAAI/bge-small-en-v1.5` from HuggingFace, running locally on CPU for free
5. **Storage** — All vectors are stored in a **FAISS index** saved to disk, so they persist between server restarts

### Query Pipeline (when you ask a question)

1. **Embed the question** — The question is converted to a vector using the same embedding model
2. **Similarity search** — FAISS finds the top 5 chunks whose vectors are closest to the question vector (cosine similarity)
3. **Prompt injection** — Those 5 chunks are injected into a prompt template as context
4. **LLM generation** — Groq's `llama3-8b-8192` reads the context and generates an answer, strictly told not to use outside knowledge
5. **Response** — Answer + source citations (filename, chunk index, similarity score) sent back to the frontend

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                      │
│                                                             │
│  PDF Upload ──► PyMuPDF ──► Chunking ──► Embeddings ──► FAISS │
│  (FastAPI)     (extract)   (1000 chars)  (BGE local)  (disk) │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      QUERY PIPELINE                         │
│                                                             │
│  Question ──► Embed ──► FAISS search ──► Prompt ──► LLaMA3  │
│  (React)     (BGE)    (top-5 chunks)   (inject)   (Groq)   │
│                                                      │      │
│                                               Answer + Sources │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Technology | Role | Why chosen |
|---|---|---|
| **FastAPI** | Backend API | Async, fast, auto Swagger docs at `/docs` |
| **LangChain** | RAG orchestration | Connects embeddings, vectorstore, and LLM cleanly |
| **FAISS** | Vector database | Local, no cloud needed, blazing fast similarity search |
| **PyMuPDF** | PDF parsing | Best-in-class text extraction quality |
| **HuggingFace BGE** | Embeddings | Free, runs locally on CPU, high quality vectors |
| **Groq + LLaMA3** | LLM | Free API, extremely fast inference |
| **React + Vite** | Frontend | Fast dev server, modern component-based UI |
| **pydantic-settings** | Config management | Type-safe environment variable loading |
| **python-dotenv** | Env loading | Reads `.env` file on startup |

---

## Project Structure

```
DocuMindAI/
├── backend/
│   ├── main.py                 — FastAPI app, registers routers, sets up CORS
│   ├── core/
│   │   ├── config.py           — All settings loaded from .env
│   │   └── rag_engine.py       — The entire RAG brain: ingest + query + delete + list
│   ├── routers/
│   │   ├── upload.py           — POST /upload: validates file, calls ingest_document()
│   │   ├── chat.py             — POST /chat + SSE streaming endpoint
│   │   └── documents.py        — GET /documents, DELETE /documents/{id}
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx             — Full UI: sidebar (upload + doc list) + chat panel
    │   └── main.jsx            — React entry point
    ├── index.html
    └── vite.config.js          — Proxies /api calls to localhost:8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/upload` | Upload and ingest a document |
| `POST` | `/api/v1/chat` | Ask a question, get JSON response |
| `POST` | `/api/v1/chat/stream` | Ask a question, get SSE streamed response |
| `GET` | `/api/v1/documents` | List all indexed documents |
| `DELETE` | `/api/v1/documents/{id}` | Remove a document from the index |
| `GET` | `/health` | Health check |

---

## Key Design Decisions

### Why FAISS over Pinecone / Weaviate / ChromaDB?
FAISS runs fully locally with zero infrastructure. It persists to just two files on disk (`index.faiss` + `index.pkl`), requires no API key, and costs nothing. For a portfolio project where you want to own and explain the full stack, FAISS is the right choice.

### Why `chunk_overlap=200`?
If a sentence falls exactly on a chunk boundary, it gets cut in half and loses meaning. A 200-character overlap ensures that sentence fully appears in at least one chunk, preserving context for the retriever.

### Why `RecursiveCharacterTextSplitter`?
It tries to split on natural boundaries in order: `\n\n` (paragraphs) → `\n` (lines) → `.` (sentences) → ` ` (words) → characters as last resort. This preserves semantic units far better than naive fixed-size splitting.

### Why the same embedding model for ingestion and querying?
Similarity search works by measuring distance between vectors. Document chunks and the query must live in the **same vector space**. Using different models would make the search completely meaningless — like comparing measurements in meters vs miles.

### Why rebuild FAISS on document deletion?
FAISS is an append-only data structure — it doesn't support deleting individual vectors by design (it's optimised for speed, not mutability). The correct approach is to filter out the deleted document's chunks and rebuild the index from the remaining ones. This is standard practice for small-to-medium corpora.

### Why SSE (Server-Sent Events) for streaming?
The `/chat/stream` endpoint streams LLM tokens one by one to the frontend as they're generated, rather than waiting for the full response. This makes the UI feel significantly faster and more responsive — users see the answer being typed out in real time.

### Why Groq + LLaMA3 instead of OpenAI?
Groq provides a free API tier with extremely fast inference (they use custom LPU hardware). LLaMA3-8B is a capable open-source model. Together they give you a production-quality LLM pipeline at zero cost, which is ideal for development and portfolio demonstration.

### Why `BAAI/bge-small-en-v1.5` for embeddings?
It consistently ranks at the top of the MTEB (Massive Text Embedding Benchmark) leaderboard for its size class. It's small enough to run on CPU in reasonable time, produces high-quality semantic vectors, and requires no API key since it runs locally via `sentence-transformers`.

---

## Data Flow (detailed)

```
User uploads "research_paper.pdf"
        │
        ▼
FastAPI /upload endpoint
  - Validates: extension must be .pdf/.txt/.md
  - Validates: file size < 50MB
  - Saves to: ./data/uploads/research_paper.pdf
        │
        ▼
ingest_document() in rag_engine.py
  - PyMuPDF opens file, extracts text page by page
  - Assigns unique doc_id (UUID4)
        │
        ▼
RecursiveCharacterTextSplitter
  - chunk_size=1000, chunk_overlap=200
  - Produces N chunks, each with metadata:
    {doc_id, filename, chunk_index, total_chunks}
        │
        ▼
HuggingFaceEmbeddings (BAAI/bge-small-en-v1.5)
  - Converts each chunk to a 384-dimensional vector
        │
        ▼
FAISS index
  - Stores vectors + metadata
  - Saved to ./data/faiss_index/ on disk
  - Persists across server restarts
        │
        ▼
Response: {doc_id, filename, chunks_created, total_characters}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User asks: "What methodology did the paper use?"
        │
        ▼
FastAPI /chat endpoint
        │
        ▼
query_documents() in rag_engine.py
  - Embeds question → 384-dimensional vector
  - FAISS.similarity_search_with_score(question, k=5)
  - Returns top 5 most semantically similar chunks
        │
        ▼
Prompt template injection:
  "Answer using ONLY this context: [chunk1]...[chunk5]
   Question: What methodology did the paper use?"
        │
        ▼
ChatGroq (llama3-8b-8192)
  - Reads context + question
  - Generates grounded answer
        │
        ▼
Response: {
  answer: "The paper used a mixed-methods approach...",
  sources: [
    {filename: "research_paper.pdf", chunk_index: 4, score: 0.312},
    ...
  ]
}
```

---

## Limitations & Possible Improvements

| Limitation | Improvement |
|---|---|
| FAISS rebuild on delete is slow for large corpora | Switch to ChromaDB or Qdrant which support native deletion |
| No multi-user isolation | Add session IDs to metadata, filter by user on query |
| Single FAISS index for all docs | Namespace by user or project |
| No conversation memory | Add `ConversationBufferMemory` from LangChain |
| No re-ranking | Add a cross-encoder re-ranker after retrieval for better accuracy |
| PDF tables/images ignored | Add `pdfplumber` for table extraction, vision model for images |
| No evaluation metrics | Integrate RAGAs for faithfulness, answer relevancy scores |

---

## Resume Line

> Built **DocuMindAI**, a production-grade RAG chatbot using **LangChain** and **FAISS** for context-aware PDF querying, with a **FastAPI** backend featuring SSE streaming, and a **React** frontend. Implemented the full ingestion pipeline: PDF extraction (PyMuPDF) → recursive chunking → local HuggingFace embeddings (BGE) → FAISS vector similarity search → grounded LLaMA3 generation via Groq API.

---

## Skills Demonstrated

- **LangChain** — chains, prompt templates, document loaders, text splitters, vector stores
- **RAG architecture** — full ingestion and retrieval pipeline from scratch
- **FAISS** — vector indexing, similarity search, persistence, index rebuilding
- **FastAPI** — async endpoints, file uploads, SSE streaming, pydantic models, CORS
- **Prompt engineering** — grounded generation, hallucination prevention
- **HuggingFace** — local embedding models, sentence-transformers
- **React** — component state, file drag-and-drop, fetch API, real-time UI updates
- **Python best practices** — pydantic settings, environment variables, singleton patterns, type hints