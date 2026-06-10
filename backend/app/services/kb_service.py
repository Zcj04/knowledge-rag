from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status
from app.models import KnowledgeBase, Category, Document, User
from app.schemas import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate,
    KnowledgeBaseResponse, KnowledgeBaseDetailResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
)


class KnowledgeBaseService:
    def _can_access(self, kb: KnowledgeBase, user: User) -> bool:
        if user.role.value == "admin":
            return True
        if kb.visibility.value == "public":
            return True
        return kb.owner_id == user.id

    def _can_edit(self, kb: KnowledgeBase, user: User) -> bool:
        if user.role.value == "admin":
            return True
        return kb.owner_id == user.id

    def _to_tree(self, categories: list[Category], parent_id: int | None = None) -> list[CategoryResponse]:
        result = []
        for cat in categories:
            if cat.parent_id == parent_id:
                resp = CategoryResponse.model_validate(cat)
                resp.children = self._to_tree(categories, cat.id)
                result.append(resp)
        return result

    def list_kbs(self, db: Session, user: User) -> list[KnowledgeBaseResponse]:
        if user.role.value == "admin":
            kbs = db.query(KnowledgeBase).all()
        else:
            kbs = db.query(KnowledgeBase).filter(
                (KnowledgeBase.owner_id == user.id) | (KnowledgeBase.visibility == "public")
            ).all()
        result = []
        for kb in kbs:
            doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
            resp = KnowledgeBaseResponse.model_validate(kb)
            resp.document_count = doc_count
            result.append(resp)
        return result

    def create_kb(self, db: Session, user: User, data: KnowledgeBaseCreate) -> KnowledgeBaseResponse:
        kb = KnowledgeBase(
            name=data.name,
            description=data.description,
            visibility=data.visibility,
            owner_id=user.id,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return KnowledgeBaseResponse.model_validate(kb)

    def get_kb(self, db: Session, kb_id: int, user: User) -> KnowledgeBaseDetailResponse:
        kb = db.query(KnowledgeBase).options(joinedload(KnowledgeBase.categories)).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if not self._can_access(kb, user):
            raise HTTPException(status_code=403, detail="Access denied")
        doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
        resp = KnowledgeBaseDetailResponse.model_validate(kb)
        resp.document_count = doc_count
        resp.categories = self._to_tree(kb.categories)
        return resp

    def update_kb(self, db: Session, kb_id: int, user: User, data: KnowledgeBaseUpdate) -> KnowledgeBaseResponse:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if not self._can_edit(kb, user):
            raise HTTPException(status_code=403, detail="Access denied")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kb, key, value)
        db.commit()
        db.refresh(kb)
        return KnowledgeBaseResponse.model_validate(kb)

    def delete_kb(self, db: Session, kb_id: int, user: User):
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if not self._can_edit(kb, user):
            raise HTTPException(status_code=403, detail="Access denied")
        db.delete(kb)
        db.commit()

    def create_category(self, db: Session, kb_id: int, user: User, data: CategoryCreate) -> CategoryResponse:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb or not self._can_edit(kb, user):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        cat = Category(name=data.name, parent_id=data.parent_id, kb_id=kb_id, sort_order=data.sort_order)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return CategoryResponse.model_validate(cat)

    def update_category(self, db: Session, kb_id: int, cat_id: int, user: User, data: CategoryUpdate) -> CategoryResponse:
        cat = db.query(Category).filter(Category.id == cat_id, Category.kb_id == kb_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        kb = cat.knowledge_base
        if not self._can_edit(kb, user):
            raise HTTPException(status_code=403, detail="Access denied")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cat, key, value)
        db.commit()
        db.refresh(cat)
        return CategoryResponse.model_validate(cat)

    def delete_category(self, db: Session, kb_id: int, cat_id: int, user: User):
        cat = db.query(Category).filter(Category.id == cat_id, Category.kb_id == kb_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        if not self._can_edit(cat.knowledge_base, user):
            raise HTTPException(status_code=403, detail="Access denied")
        db.delete(cat)
        db.commit()

    def list_categories(self, db: Session, kb_id: int, user: User) -> list[CategoryResponse]:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb or not self._can_access(kb, user):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        categories = db.query(Category).filter(Category.kb_id == kb_id).all()
        return self._to_tree(categories)
