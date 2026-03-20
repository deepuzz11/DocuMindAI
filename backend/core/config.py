from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Groq (free) — get key at console.groq.com
    groq_api_key: str = ""
    llm_model: str = "llama3-8b-8192"
    llm_temperature: float = 0.1

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval
    top_k: int = 5

    # FAISS storage
    faiss_index_path: str = "./data/faiss_index"

    # Upload
    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf", ".txt", ".md"]

    class Config:
        env_file = ".env"
        extra = "ignore"   # ignore any extra keys in .env


@lru_cache()
def get_settings() -> Settings:
    return Settings()