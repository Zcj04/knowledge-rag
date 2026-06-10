from pydantic import BaseModel, Field
from datetime import datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    kb_id: int
    sort_order: int
    children: list["CategoryResponse"] = []

    model_config = {"from_attributes": True}


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    visibility: str = "private"


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None


class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: str
    visibility: str
    owner_id: int
    created_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


class KnowledgeBaseDetailResponse(KnowledgeBaseResponse):
    categories: list[CategoryResponse] = []
