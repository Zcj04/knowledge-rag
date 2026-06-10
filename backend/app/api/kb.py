from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate,
    KnowledgeBaseResponse, KnowledgeBaseDetailResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
)
from app.services.kb_service import KnowledgeBaseService

router = APIRouter(prefix="/api/kb", tags=["knowledge-bases"])
kb_service = KnowledgeBaseService()


@router.get("", response_model=list[KnowledgeBaseResponse])
def list_kbs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return kb_service.list_kbs(db, current_user)


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
def create_kb(data: KnowledgeBaseCreate, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return kb_service.create_kb(db, current_user, data)


@router.get("/{kb_id}", response_model=KnowledgeBaseDetailResponse)
def get_kb(kb_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return kb_service.get_kb(db, kb_id, current_user)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_kb(kb_id: int, data: KnowledgeBaseUpdate, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return kb_service.update_kb(db, kb_id, current_user, data)


@router.delete("/{kb_id}", status_code=204)
def delete_kb(kb_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    kb_service.delete_kb(db, kb_id, current_user)


# Categories
@router.get("/{kb_id}/categories", response_model=list[CategoryResponse])
def list_categories(kb_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return kb_service.list_categories(db, kb_id, current_user)


@router.post("/{kb_id}/categories", response_model=CategoryResponse, status_code=201)
def create_category(kb_id: int, data: CategoryCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return kb_service.create_category(db, kb_id, current_user, data)


@router.put("/{kb_id}/categories/{cat_id}", response_model=CategoryResponse)
def update_category(kb_id: int, cat_id: int, data: CategoryUpdate,
                    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return kb_service.update_category(db, kb_id, cat_id, current_user, data)


@router.delete("/{kb_id}/categories/{cat_id}", status_code=204)
def delete_category(kb_id: int, cat_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    kb_service.delete_category(db, kb_id, cat_id, current_user)
