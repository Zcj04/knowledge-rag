from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_type: str
    kb_id: int
    category_id: int | None = None
    uploader_id: int
    status: str
    chunk_count: int
    error_message: str | None = None
    created_at: datetime
    tags: list[str] = []

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]


class DocumentCategoryUpdate(BaseModel):
    category_id: int | None = None


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str


class DocumentTagUpdate(BaseModel):
    tag_ids: list[int]
