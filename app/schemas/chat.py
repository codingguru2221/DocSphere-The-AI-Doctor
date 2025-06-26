from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message schema for chat interactions."""
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=4000)
    timestamp: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class ChatRequest(BaseModel):
    """Request schema for chat interactions."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    conversation_id: Optional[int] = None
    
    # Patient context (optional)
    patient_age: Optional[int] = Field(None, ge=0, le=120)
    patient_gender: Optional[str] = None
    medical_history: Optional[Dict[str, Any]] = None
    
    @validator('patient_gender')
    def validate_gender(cls, v):
        if v is not None:
            valid_genders = ['male', 'female', 'other', 'prefer_not_to_say']
            if v.lower() not in valid_genders:
                raise ValueError(f'Gender must be one of: {valid_genders}')
        return v


class ChatResponse(BaseModel):
    """Response schema for chat interactions."""
    message: str
    conversation_id: int
    message_id: int
    timestamp: datetime
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    
    # Safety information
    safety_score: Optional[int] = Field(None, ge=0, le=100)
    flagged_content: bool = False
    emergency_detected: bool = False
    
    # Medical guidance
    medical_disclaimer: str = "This information is for educational purposes only. Please consult with a qualified healthcare provider for medical advice, diagnosis, or treatment."
    suggested_next_steps: Optional[List[str]] = None


class ConversationHistory(BaseModel):
    """Schema for conversation history."""
    conversation_id: int
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_active: bool
    messages: List[Message]
    
    # Medical context
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    chief_complaint: Optional[str] = None


class SafetyAlert(BaseModel):
    """Schema for safety alerts."""
    alert_type: str
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    description: str
    timestamp: datetime
    conversation_id: int
    message_id: Optional[int] = None
    resolved: bool = False


class MedicalContext(BaseModel):
    """Schema for medical context information."""
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    chief_complaint: Optional[str] = None
    symptoms: Optional[List[str]] = None
    medical_history: Optional[Dict[str, Any]] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None:
            valid_genders = ['male', 'female', 'other', 'prefer_not_to_say']
            if v.lower() not in valid_genders:
                raise ValueError(f'Gender must be one of: {valid_genders}')
        return v


class ConversationSummary(BaseModel):
    """Schema for conversation summary."""
    conversation_id: int
    session_id: str
    summary: str
    key_topics: List[str]
    patient_concerns: List[str]
    suggested_follow_up: List[str]
    created_at: datetime 