from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional, List
import json

from app.config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model for tracking patient interactions."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    """Conversation model for tracking chat sessions."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(255), index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Medical context
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(50), nullable=True)
    chief_complaint = Column(Text, nullable=True)
    medical_history = Column(JSON, nullable=True)  # Store as JSON
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Message model for individual chat messages."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(50))  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # AI response metadata
    response_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    
    # Safety flags
    flagged_content = Column(Boolean, default=False)
    safety_score = Column(Integer, nullable=True)  # 0-100, higher is safer
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class MedicalKnowledge(Base):
    """Medical knowledge base for the AI doctor."""
    __tablename__ = "medical_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), index=True)
    category = Column(String(100), index=True)
    content = Column(Text)
    source = Column(String(255), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class SafetyLog(Base):
    """Log for safety and compliance monitoring."""
    __tablename__ = "safety_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    event_type = Column(String(100))  # 'emergency_keyword', 'content_filter', etc.
    description = Column(Text)
    severity = Column(String(50))  # 'low', 'medium', 'high', 'critical'
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)


# Database dependency
def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine) 