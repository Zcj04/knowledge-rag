from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models import User, Tag
from app.schemas import DocumentResponse, DocumentListResponse, TagResponse, TagCreate, DocumentTagUpdate, DocumentCategoryUpdate
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/kb", tags=["documents"])
doc_service = DocumentService()


@router.post("/{kb_id}/documents/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    category_id: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat_id = int(category_id) if category_id and category_id.isdigit() else None
    doc = doc_service.upload_file(db, kb_id, file, current_user, cat_id)
    resp = DocumentResponse.model_validate(doc)
    resp.tags = [t.name for t in doc.tags]
    return resp


@router.post("/{kb_id}/documents/batch-upload")
def batch_upload(
    kb_id: int,
    files: list[UploadFile] = File(...),
    category_id: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat_id = int(category_id) if category_id and category_id.isdigit() else None
    docs = doc_service.upload_files_batch(db, kb_id, files, current_user, cat_id)
    return {
        "uploaded": len(docs),
        "documents": [
            {**DocumentResponse.model_validate(d).model_dump(), "tags": [t.name for t in d.tags]}
            for d in docs
        ],
    }


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
def list_documents(
    kb_id: int,
    category_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, docs = doc_service.list_documents(db, kb_id, current_user, category_id, status, search, offset, limit)
    items = []
    for d in docs:
        item = DocumentResponse.model_validate(d)
        item.tags = [t.name for t in d.tags]
        items.append(item)
    return DocumentListResponse(total=total, items=items)


@router.delete("/{kb_id}/documents/{doc_id}", status_code=204)
def delete_document(kb_id: int, doc_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    doc_service.delete_document(db, doc_id, current_user)


@router.put("/{kb_id}/documents/{doc_id}/tags", response_model=DocumentResponse)
def update_document_tags(kb_id: int, doc_id: int, data: DocumentTagUpdate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    doc = doc_service.update_tags(db, doc_id, data.tag_ids, current_user)
    resp = DocumentResponse.model_validate(doc)
    resp.tags = [t.name for t in doc.tags]
    return resp


@router.put("/{kb_id}/documents/{doc_id}/category", response_model=DocumentResponse)
def update_document_category(kb_id: int, doc_id: int, data: DocumentCategoryUpdate,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    doc = doc_service.update_document_category(db, doc_id, data.category_id, current_user)
    resp = DocumentResponse.model_validate(doc)
    resp.tags = [t.name for t in doc.tags]
    return resp


@router.get("/tags", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tags = db.query(Tag).all()
    return [TagResponse.model_validate(t) for t in tags]


@router.post("/tags", response_model=TagResponse, status_code=201)
def create_tag(data: TagCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tag = Tag(name=data.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return TagResponse.model_validate(tag)
