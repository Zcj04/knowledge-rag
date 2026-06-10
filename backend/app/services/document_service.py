import os
import uuid
import re
from pathlib import Path
from typing import Iterator
import httpx
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.models import Document, DocumentStatus, Tag, DocumentTag, User, KnowledgeBase


class DocumentService:
    def __init__(self):
        os.makedirs(settings.effective_upload_dir, exist_ok=True)
        os.makedirs(settings.effective_chroma_dir, exist_ok=True)
        self._chroma_client = chromadb.PersistentClient(
            path=settings.effective_chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _get_collection(self, kb_id: int):
        name = f"kb_{kb_id}"
        return self._chroma_client.get_or_create_collection(name=name)

    def _delete_collection(self, kb_id: int):
        try:
            self._chroma_client.delete_collection(name=f"kb_{kb_id}")
        except Exception:
            pass

    def upload_file(self, db: Session, kb_id: int, file: UploadFile, user: User,
                    category_id: int | None = None) -> Document:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        ext = Path(file.filename).suffix.lower()
        allowed = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        file_data = file.file.read()
        file_size = len(file_data)
        if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400,
                                detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

        file_type = ext.lstrip(".")
        if file_type in ("jpg", "jpeg", "bmp", "tiff", "png"):
            file_type = "image"

        safe_name = f"{uuid.uuid4().hex}{ext}"
        upload_path = os.path.join(settings.effective_upload_dir, safe_name)
        with open(upload_path, "wb") as f:
            f.write(file_data)

        doc = Document(
            title=file.filename,
            file_path=upload_path,
            file_type=file_type,
            kb_id=kb_id,
            category_id=category_id,
            uploader_id=user.id,
            status=DocumentStatus.PENDING,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        self._process_document(db, doc)
        return doc

    def upload_files_batch(self, db: Session, kb_id: int, files: list[UploadFile],
                           user: User, category_id: int | None = None) -> list[Document]:
        if len(files) > settings.MAX_BATCH_FILES:
            raise HTTPException(status_code=400,
                                detail=f"Maximum {settings.MAX_BATCH_FILES} files per batch")
        docs = []
        for file in files:
            doc = self.upload_file(db, kb_id, file, user, category_id)
            docs.append(doc)
        return docs

    def _process_document(self, db: Session, doc: Document):
        try:
            doc.status = DocumentStatus.PROCESSING
            db.commit()

            text = self._parse_file(doc.file_path, doc.file_type)
            if not text.strip():
                doc.status = DocumentStatus.COMPLETED
                doc.chunk_count = 0
                db.commit()
                return

            chunks = list(self._chunk_text(text))
            if not chunks:
                doc.status = DocumentStatus.COMPLETED
                doc.chunk_count = 0
                db.commit()
                return

            embeddings = self._embed_chunks(chunks)
            collection = self._get_collection(doc.kb_id)

            ids = [f"doc_{doc.id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"document_id": str(doc.id), "chunk_index": i, "title": doc.title}
                         for i in range(len(chunks))]

            collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

            doc.chunk_count = len(chunks)
            doc.status = DocumentStatus.COMPLETED
            db.commit()
        except Exception as e:
            db.refresh(doc)
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.commit()

    def delete_document(self, db: Session, doc_id: int, user: User) -> bool:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        kb = doc.knowledge_base
        if kb.owner_id != user.id and user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        try:
            collection = self._get_collection(doc.kb_id)
            ids = [f"doc_{doc.id}_chunk_{i}" for i in range(doc.chunk_count)]
            if ids:
                collection.delete(ids=ids)
        except Exception:
            pass

        try:
            os.remove(doc.file_path)
        except Exception:
            pass

        db.delete(doc)
        db.commit()
        return True

    def _parse_file(self, file_path: str, file_type: str) -> str:
        ext_map = {
            "pdf": self._parse_pdf,
            "docx": self._parse_docx,
            "txt": self._parse_txt,
            "md": self._parse_txt,
            "image": self._parse_image,
        }
        parser = ext_map.get(file_type)
        if parser:
            return parser(file_path)
        return ""

    def _parse_pdf(self, file_path: str) -> str:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def _parse_docx(self, file_path: str) -> str:
        from docx import Document as DocxDoc
        doc = DocxDoc(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _parse_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _parse_image(self, file_path: str) -> str:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            return pytesseract.image_to_string(img, lang="chi_sim+eng")
        except ImportError:
            return "[OCR not available - install pytesseract]"

    def _chunk_text(self, text: str) -> Iterator[str]:
        """Split text into overlapping chunks, respecting sentence boundaries."""
        # Split on Chinese + English sentence-ending punctuation and newlines
        sentences = re.split(r'(?<=[。！？!?\n])\s*', text)
        current_chunk = ""
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            s_len = len(sentence)
            if current_len + s_len > settings.CHUNK_SIZE and current_chunk:
                yield current_chunk.strip()
                # Overlap: keep tail of previous chunk
                overlap_point = max(0, len(current_chunk) - settings.CHUNK_OVERLAP)
                current_chunk = current_chunk[overlap_point:] + " " + sentence
                current_len = len(current_chunk)
            else:
                current_chunk += (" " if current_chunk else "") + sentence
                current_len += s_len

        if current_chunk.strip():
            yield current_chunk.strip()

    def _embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        if not settings.DEEPSEEK_API_KEY:
            # Use consistent hash-based vectors when no API key available.
            # These are deterministic per chunk content, enabling basic retrieval.
            import hashlib
            embeddings = []
            for chunk in chunks:
                h = hashlib.sha256(chunk.encode("utf-8")).digest()
                vec = [((b / 255.0) * 2 - 1) for b in h]
                while len(vec) < 1024:
                    vec.append(0.0)
                embeddings.append(vec[:1024])
            return embeddings

        url = f"{settings.DEEPSEEK_BASE_URL}/v1/embeddings"
        headers = {"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        all_embeddings = []
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            resp = httpx.post(url, json={"model": settings.DEEPSEEK_EMBED_MODEL, "input": batch},
                              headers=headers, timeout=60.0)
            if resp.status_code != 200:
                raise RuntimeError(f"Embedding API error: {resp.text}")
            data = resp.json()
            all_embeddings.extend([item["embedding"] for item in data["data"]])
        return all_embeddings

    def keyword_search(self, kb_id: int, query: str, top_k: int = 5) -> list[dict]:
        """Keyword-based search fallback when no embedding API is available."""
        try:
            collection = self._get_collection(kb_id)
            all_data = collection.get(include=["documents", "metadatas"])
        except Exception:
            return []

        if not all_data["ids"]:
            return []

        query_terms = set(query.lower().split())
        # Also split CJK text into bigrams for better matching
        cjk_bigrams = set()
        cjk_run = ""
        for ch in query:
            if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff':
                cjk_run += ch
            else:
                if len(cjk_run) >= 2:
                    for i in range(len(cjk_run) - 1):
                        cjk_bigrams.add(cjk_run[i:i + 2])
                cjk_run = ""
        if len(cjk_run) >= 2:
            for i in range(len(cjk_run) - 1):
                cjk_bigrams.add(cjk_run[i:i + 2])

        scored = []
        for i, doc_id in enumerate(all_data["ids"]):
            text = all_data["documents"][i] if all_data.get("documents") else ""
            metadata = all_data["metadatas"][i] if all_data.get("metadatas") else {}

            # Word overlap score
            text_lower = text.lower()
            word_score = sum(1 for t in query_terms if t in text_lower) / max(len(query_terms), 1)

            # CJK bigram overlap
            bigram_score = 0.0
            if cjk_bigrams:
                text_bigrams = set()
                cjk_run_t = ""
                for ch in text:
                    if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff':
                        cjk_run_t += ch
                    else:
                        if len(cjk_run_t) >= 2:
                            for j in range(len(cjk_run_t) - 1):
                                text_bigrams.add(cjk_run_t[j:j + 2])
                        cjk_run_t = ""
                if len(cjk_run_t) >= 2:
                    for j in range(len(cjk_run_t) - 1):
                        text_bigrams.add(cjk_run_t[j:j + 2])
                if cjk_bigrams:
                    bigram_score = len(cjk_bigrams & text_bigrams) / len(cjk_bigrams)

            score = 0.4 * word_score + 0.6 * bigram_score  # CJK bigrams weighted higher
            if score > 0:
                scored.append({
                    "document_id": metadata.get("document_id", ""),
                    "document_title": metadata.get("title", "Unknown"),
                    "chunk_text": text,
                    "similarity": round(min(score, 0.99), 4),
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def update_document_category(self, db: Session, doc_id: int, category_id: int | None,
                                  user: User) -> Document:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        kb = doc.knowledge_base
        if kb.owner_id != user.id and user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        doc.category_id = category_id
        db.commit()
        db.refresh(doc)
        return doc

    def update_tags(self, db: Session, doc_id: int, tag_ids: list[int], user: User) -> Document:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        kb = doc.knowledge_base
        if kb.owner_id != user.id and user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db.query(DocumentTag).filter(DocumentTag.document_id == doc_id).delete()
        for tid in tag_ids:
            db.add(DocumentTag(document_id=doc_id, tag_id=tid))
        db.commit()
        db.refresh(doc)
        return doc

    def list_documents(self, db: Session, kb_id: int, user: User,
                       category_id: int | None = None, status: str | None = None,
                       search: str | None = None, offset: int = 0, limit: int = 20):
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if kb.owner_id != user.id and kb.visibility.value != "public" and user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        q = db.query(Document).filter(Document.kb_id == kb_id)
        if category_id is not None:
            q = q.filter(Document.category_id == category_id)
        if status:
            q = q.filter(Document.status == status)
        if search:
            q = q.filter(Document.title.ilike(f"%{search}%"))

        total = q.count()
        docs = q.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
        return total, docs
