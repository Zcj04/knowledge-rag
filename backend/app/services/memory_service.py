from typing import Any
from sqlalchemy.orm import Session
from app.models import User, UserPreference, Conversation, Message
from app.config import settings


class MemoryService:
    """Short-term (session window) and long-term (persistent conversation + preferences) memory."""

    # ---- Short-term memory ----

    def get_conversation_context(self, db: Session, conversation_id: int,
                                  max_rounds: int | None = None) -> list[dict]:
        """Return recent messages within the short-term window."""
        if max_rounds is None:
            max_rounds = settings.SHORT_TERM_ROUNDS
        max_messages = max_rounds * 2  # user + assistant per round
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(max_messages)
            .all()
        )
        messages.reverse()  # chronological order
        return [{"role": m.role, "content": m.content} for m in messages]

    def clear_short_term_context(self, conversation_id: int) -> None:
        """Short-term context is inherently transient; no explicit clear needed beyond trimming."""
        pass

    # ---- Long-term memory ----

    def save_user_message(self, db: Session, conversation_id: int, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role="user", content=content)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def save_assistant_message(self, db: Session, conversation_id: int, content: str,
                               citations: list | None = None, confidence: float | None = None) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            citations=citations,
            confidence=confidence,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def list_conversations(self, db: Session, user: User, kb_id: int | None = None) -> list[dict]:
        q = db.query(Conversation).filter(Conversation.user_id == user.id)
        if kb_id is not None:
            q = q.filter(Conversation.kb_id == kb_id)
        conversations = q.order_by(Conversation.created_at.desc()).all()
        result = []
        for conv in conversations:
            msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
            result.append({
                "id": conv.id,
                "title": conv.title,
                "kb_id": conv.kb_id,
                "created_at": conv.created_at,
                "message_count": msg_count,
            })
        return result

    def get_conversation_detail(self, db: Session, conv_id: int, user: User) -> dict | None:
        conv = db.query(Conversation).filter(
            Conversation.id == conv_id, Conversation.user_id == user.id
        ).first()
        if not conv:
            return None
        messages = db.query(Message).filter(
            Message.conversation_id == conv_id
        ).order_by(Message.created_at).all()
        return {
            "id": conv.id,
            "title": conv.title,
            "kb_id": conv.kb_id,
            "created_at": conv.created_at,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "citations": m.citations,
                    "confidence": m.confidence,
                    "created_at": m.created_at,
                }
                for m in messages
            ],
        }

    def delete_conversation(self, db: Session, conv_id: int, user: User) -> bool:
        conv = db.query(Conversation).filter(
            Conversation.id == conv_id, Conversation.user_id == user.id
        ).first()
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

    def export_conversation(self, db: Session, conv_id: int, user: User) -> str | None:
        conv = self.get_conversation_detail(db, conv_id, user)
        if not conv:
            return None
        lines = [f"# {conv['title']}", f"Date: {conv['created_at']}", ""]
        for m in conv["messages"]:
            role_label = "**User**" if m["role"] == "user" else "**Assistant**"
            lines.append(f"### {role_label}")
            lines.append(m["content"])
            if m.get("citations"):
                lines.append("")
                lines.append("*Sources:*")
                for c in m["citations"]:
                    lines.append(f"- {c.get('document_title', 'Unknown')} (similarity: {c.get('similarity', 0):.2f})")
            lines.append("")
        return "\n".join(lines)

    # ---- User preferences ----

    def get_preferences(self, db: Session, user: User) -> dict:
        prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).all()
        return {p.key: p.value for p in prefs}

    def get_preference(self, db: Session, user: User, key: str) -> Any | None:
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user.id, UserPreference.key == key
        ).first()
        return pref.value if pref else None

    def set_preference(self, db: Session, user: User, key: str, value: Any):
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user.id, UserPreference.key == key
        ).first()
        if pref:
            pref.value = value
        else:
            pref = UserPreference(user_id=user.id, key=key, value=value)
            db.add(pref)
        db.commit()
