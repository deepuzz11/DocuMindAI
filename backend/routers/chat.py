from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.rag_engine import query_documents, stream_query_documents

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    stream: bool = False


class SourceChunk(BaseModel):
    filename: str
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    result = query_documents(request.question)
    return ChatResponse(
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result["sources"]],
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Server-Sent Events streaming endpoint.
    Frontend consumes with EventSource or fetch + ReadableStream.
    """
    def event_generator():
        for chunk in stream_query_documents(request.question):
            # SSE format: data: <payload>\n\n
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
