import hashlib
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.models import User, KnowledgeBase, Conversation
from app.schemas import AnswerResponse, Citation
from app.services.memory_service import MemoryService
from app.services.document_service import DocumentService


class QAService:
    def __init__(self):
        self.memory = MemoryService()
        self.doc_service = DocumentService()
        self._chroma_client = chromadb.PersistentClient(
            path=settings.effective_chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def ask(self, db: Session, user: User, question: str,
            conversation_id: int | None = None, kb_id: int | None = None) -> AnswerResponse:
        # Resolve or create conversation
        if conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id, Conversation.user_id == user.id
            ).first()
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            title = question[:100] + ("..." if len(question) > 100 else "")
            conv = Conversation(user_id=user.id, kb_id=kb_id, title=title)
            db.add(conv)
            db.commit()
            db.refresh(conv)
            conversation_id = conv.id

        # Save user message
        self.memory.save_user_message(db, conversation_id, question)

        # Retrieve relevant context
        citations = []
        knowledge_context = ""
        if kb_id:
            citations, knowledge_context = self._retrieve(question, kb_id)

        # Build short-term memory context
        history = self.memory.get_conversation_context(db, conversation_id)

        # Generate answer
        answer, confidence = self._generate(question, knowledge_context, history)

        # Build citation objects
        citation_objs = [
            Citation(
                document_title=c.get("document_title", "Unknown"),
                chunk_text=c.get("chunk_text", "")[:300],
                similarity=c.get("similarity", 0),
            )
            for c in citations
        ]

        # Save assistant message
        msg = self.memory.save_assistant_message(
            db, conversation_id, answer,
            citations=[c.model_dump() for c in citation_objs],
            confidence=confidence,
        )

        return AnswerResponse(
            conversation_id=conversation_id,
            message_id=msg.id,
            answer=answer,
            citations=citation_objs,
            confidence=confidence,
        )

    def _retrieve(self, question: str, kb_id: int) -> tuple[list[dict], str]:
        # When no API key, use keyword-based search
        if not settings.DEEPSEEK_API_KEY:
            citations = self.doc_service.keyword_search(kb_id, question, top_k=settings.RETRIEVAL_TOP_K)
            if not citations:
                return [], ""
            context_parts = [
                f"[Source: {c['document_title']}]\n{c['chunk_text']}"
                for c in citations
            ]
            return citations, "\n\n---\n\n".join(context_parts)

        # With API key: use vector similarity search
        try:
            collection = self._chroma_client.get_collection(name=f"kb_{kb_id}")
        except Exception:
            # Fall back to keyword search if collection doesn't exist
            citations = self.doc_service.keyword_search(kb_id, question, top_k=settings.RETRIEVAL_TOP_K)
            if not citations:
                return [], ""
            context_parts = [
                f"[Source: {c['document_title']}]\n{c['chunk_text']}"
                for c in citations
            ]
            return citations, "\n\n---\n\n".join(context_parts)

        # Embed the question
        query_embedding = self._embed_query(question)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=settings.RETRIEVAL_TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return [], ""

        citations = []
        context_parts = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 0
            similarity = 1.0 - min(distance, 1.0)
            if similarity < settings.RETRIEVAL_THRESHOLD:
                continue
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            text = results["documents"][0][i] if results.get("documents") else ""
            citations.append({
                "document_id": metadata.get("document_id", ""),
                "document_title": metadata.get("title", "Unknown"),
                "chunk_text": text,
                "similarity": round(similarity, 4),
            })
            context_parts.append(f"[Source: {metadata.get('title', 'Unknown')}]\n{text}")

        if not citations:
            return [], ""

        knowledge_context = "\n\n---\n\n".join(context_parts)
        return citations, knowledge_context

    def _embed_query(self, text: str) -> list[float]:
        """Generate embedding for a query string."""
        if not settings.DEEPSEEK_API_KEY:
            # Hash-based fallback -- matches _embed_chunks scheme (without chunk index)
            h = hashlib.sha256(text.encode("utf-8")).digest()
            vec = [((b / 255.0) * 2 - 1) for b in h]
            while len(vec) < 1024:
                vec.append(0.0)
            return vec[:1024]

        url = f"{settings.DEEPSEEK_BASE_URL}/v1/embeddings"
        headers = {"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        resp = httpx.post(url, json={"model": settings.DEEPSEEK_EMBED_MODEL, "input": [text]},
                          headers=headers, timeout=30.0)
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding API error: {resp.text}")
        data = resp.json()
        return data["data"][0]["embedding"]

    def _generate(self, question: str, knowledge_context: str, history: list[dict]) -> tuple[str, float]:
        system_prompt = (
            "You are an enterprise knowledge assistant. Answer questions based on the provided knowledge base context. "
            "If the context does not contain relevant information, say so clearly rather than guessing. "
            "Cite specific sources when possible. Respond in the same language as the user's question."
        )

        messages = [{"role": "system", "content": system_prompt}]

        if knowledge_context:
            messages.append({
                "role": "system",
                "content": f"Relevant knowledge from the knowledge base:\n\n{knowledge_context}"
            })

        # Add short-term memory history
        for h in history[:-1]:  # exclude the last message (current question)
            messages.append({"role": h["role"], "content": h["content"]})

        messages.append({"role": "user", "content": question})

        if not settings.DEEPSEEK_API_KEY:
            # Dev mode response without API key
            has_knowledge = bool(knowledge_context)
            if has_knowledge:
                answer = (
                    f"[Dev mode - no API key configured]\n\n"
                    f"Based on the knowledge base, here are the relevant passages:\n\n"
                    f"{knowledge_context[:1500]}\n\n"
                    f"---\n"
                    f"To get AI-generated answers, set DEEPSEEK_API_KEY in your .env file."
                )
                confidence = 0.5
            else:
                answer = (
                    f"[Dev mode] No relevant content found in the knowledge base for: \"{question}\".\n\n"
                    f"Make sure you have uploaded documents and they are in 'completed' status."
                )
                confidence = 0.1
            return answer, confidence

        url = f"{settings.DEEPSEEK_BASE_URL}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        resp = httpx.post(
            url,
            json={
                "model": settings.DEEPSEEK_CHAT_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            },
            headers=headers,
            timeout=120.0,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Chat API error: {resp.text}")

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]

        # Confidence estimation
        has_knowledge = bool(knowledge_context)
        confidence = 0.85 if has_knowledge else 0.3

        return answer, confidence
