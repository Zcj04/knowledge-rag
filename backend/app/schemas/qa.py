from pydantic import BaseModel, Field
from datetime import datetime


class QuestionRequest(BaseModel):
    conversation_id: int | None = None
    kb_id: int | None = None
    question: str = Field(min_length=1, max_length=5000)


class Citation(BaseModel):
    document_title: str
    chunk_text: str
    similarity: float


class AnswerResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    citations: list[Citation] = []
    confidence: float | None = None


class ConversationResponse(BaseModel):
    id: int
    title: str
    kb_id: int | None = None
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: list | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []
