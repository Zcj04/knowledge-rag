from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import (
    QuestionRequest, AnswerResponse,
    ConversationResponse, ConversationDetailResponse,
    UserPreferenceUpdate, UserPreferenceResponse,
)
from app.services.qa_service import QAService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/qa", tags=["qa"])
qa_service = QAService()
memory_service = MemoryService()


@router.post("/ask", response_model=AnswerResponse)
def ask_question(
    data: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return qa_service.ask(
        db, current_user, data.question,
        conversation_id=data.conversation_id,
        kb_id=data.kb_id,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    kb_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return memory_service.list_conversations(db, current_user, kb_id)


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    detail = memory_service.get_conversation_detail(db, conv_id, current_user)
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return detail


@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not memory_service.delete_conversation(db, conv_id, current_user):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/conversations/{conv_id}/export", response_class=PlainTextResponse)
def export_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    markdown = memory_service.export_conversation(db, conv_id, current_user)
    if not markdown:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return markdown


# User preferences
@router.get("/preferences", response_model=list[UserPreferenceResponse])
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = memory_service.get_preferences(db, current_user)
    return [UserPreferenceResponse(key=k, value=v) for k, v in prefs.items()]


@router.put("/preferences", response_model=UserPreferenceResponse)
def update_preference(
    data: UserPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory_service.set_preference(db, current_user, data.key, data.value)
    return UserPreferenceResponse(key=data.key, value=data.value)
