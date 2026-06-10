from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class Visibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="")
    visibility = Column(SAEnum(Visibility), default=Visibility.PRIVATE, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", backref="knowledge_bases")
    categories = relationship("Category", back_populates="knowledge_base", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    sort_order = Column(Integer, default=0)

    knowledge_base = relationship("KnowledgeBase", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="category")
