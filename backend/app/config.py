from pydantic_settings import BaseSettings
from pathlib import Path

# Base directory = backend/ (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Knowledge RAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = ""

    @property
    def effective_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = BASE_DIR / "knowledge_rag.db"
        return f"sqlite:///{db_path.as_posix()}"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_CHAT_MODEL: str = "deepseek-chat"
    DEEPSEEK_EMBED_MODEL: str = "deepseek-embedding"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = ""

    @property
    def effective_chroma_dir(self) -> str:
        if self.CHROMA_PERSIST_DIR:
            return self.CHROMA_PERSIST_DIR
        return str(BASE_DIR / "chroma_data")

    # Upload
    UPLOAD_DIR: str = ""

    @property
    def effective_upload_dir(self) -> str:
        if self.UPLOAD_DIR:
            return self.UPLOAD_DIR
        return str(BASE_DIR / "uploads")

    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_BATCH_FILES: int = 20

    # RAG
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_THRESHOLD: float = 0.3

    # Memory
    SHORT_TERM_ROUNDS: int = 10

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
