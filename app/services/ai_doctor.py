import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import openai
from openai import OpenAI

from app.config import settings
from app.schemas.chat import Message, MessageRole, ChatRequest, ChatResponse, SafetyAlert
from app.services.safety_monitor import SafetyMonitor
from app.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class AIDoctorService:
    """Core AI Doctor service for professional medical chat interactions."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.safety_monitor = SafetyMonitor()
        self.conversation_manager = ConversationManager()
        
        # Medical conversation templates
        self.medical_templates = {
            "greeting": "Hello, I'm Dr. Sarah Chen. I'm here to help answer your health-related questions and provide educational information. How can I assist you today?",
            "disclaimer": "I want to remind you that I'm an AI assistant providing educational information only. For medical advice, diagnosis, or treatment, please consult with a qualified healthcare provider.",
            "emergency": "I'm concerned about what you're describing. If you're experiencing a medical emergency, please call emergency services (911 in the US) or go to the nearest emergency room immediately.",
            "follow_up": "It would be helpful to know more about your situation. Could you tell me a bit more about your symptoms and when they started?",
            "referral": "Based on what you've shared, I'd recommend consulting with a healthcare provider who can properly evaluate your situation and provide appropriate care."
        }
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Process a chat message and generate a professional medical response."""
        start_time = time.time()
        
        try:
            # 1. Safety check
            safety_result = await self.safety_monitor.check_message_safety(request.message)
            
            if safety_result.is_emergency:
                return await self._handle_emergency_situation(request, safety_result)
            
            # 2. Get conversation context
            conversation_context = await self.conversation_manager.get_conversation_context(
                request.conversation_id, request.session_id
            )
            
            # 3. Build conversation history
            messages = self._build_conversation_messages(conversation_context, request)
            
            # 4. Generate AI response
            ai_response = await self._generate_ai_response(messages, request)
            
            # 5. Safety check on AI response
            response_safety = await self.safety_monitor.check_message_safety(ai_response)
            
            # 6. Calculate response metrics
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 7. Save conversation
            conversation_id, message_id = await self.conversation_manager.save_conversation(
                request, ai_response, response_time_ms, safety_result, response_safety
            )
            
            # 8. Build response
            response = ChatResponse(
                message=ai_response,
                conversation_id=conversation_id,
                message_id=message_id,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time_ms,
                safety_score=safety_result.safety_score,
                flagged_content=safety_result.flagged_content,
                emergency_detected=safety_result.is_emergency,
                suggested_next_steps=self._generate_next_steps(request, ai_response)
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return await self._handle_error_response(request)
    
    async def _generate_ai_response(self, messages: List[Dict[str, str]], request: ChatRequest) -> str:
        """Generate AI response using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add medical disclaimer if this is a new conversation
            if not request.conversation_id:
                ai_response += f"\n\n{self.medical_templates['disclaimer']}"
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response()
    
    def _build_conversation_messages(self, context: Dict[str, Any], request: ChatRequest) -> List[Dict[str, str]]:
        """Build the conversation messages for the AI model."""
        messages = [
            {"role": "system", "content": settings.medical_system_prompt}
        ]
        
        # Add conversation history
        if context.get("messages"):
            for msg in context["messages"][-settings.max_conversation_history:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        return messages
    
    async def _handle_emergency_situation(self, request: ChatRequest, safety_result: Any) -> ChatResponse:
        """Handle emergency situations with appropriate response."""
        emergency_response = (
            f"{self.medical_templates['emergency']}\n\n"
            f"If you need immediate medical attention, please call emergency services or go to the nearest emergency room."
        )
        
        # Log emergency situation
        await self.safety_monitor.log_safety_alert(
            SafetyAlert(
                alert_type="emergency_keyword",
                severity="critical",
                description=f"Emergency keywords detected: {safety_result.flagged_keywords}",
                timestamp=datetime.utcnow(),
                conversation_id=request.conversation_id or 0
            )
        )
        
        return ChatResponse(
            message=emergency_response,
            conversation_id=request.conversation_id or 0,
            message_id=0,
            timestamp=datetime.utcnow(),
            emergency_detected=True,
            flagged_content=True
        )
    
    async def _handle_error_response(self, request: ChatRequest) -> ChatResponse:
        """Handle error situations with a fallback response."""
        fallback_response = (
            "I apologize, but I'm experiencing technical difficulties right now. "
            "Please try again in a moment, or if you have an urgent medical concern, "
            "please contact a healthcare provider directly."
        )
        
        return ChatResponse(
            message=fallback_response,
            conversation_id=request.conversation_id or 0,
            message_id=0,
            timestamp=datetime.utcnow(),
            emergency_detected=False
        )
    
    def _get_fallback_response(self) -> str:
        """Get a fallback response when AI generation fails."""
        return (
            "I understand you have health-related questions, and I want to help. "
            "However, I'm currently experiencing technical difficulties. "
            "Please try again in a moment, or consider consulting with a healthcare provider "
            "for immediate assistance."
        )
    
    def _generate_next_steps(self, request: ChatRequest, ai_response: str) -> List[str]:
        """Generate suggested next steps based on the conversation."""
        next_steps = []
        
        # Add general next steps
        next_steps.append("Consider scheduling an appointment with a healthcare provider")
        next_steps.append("Keep track of your symptoms and their progression")
        
        # Add specific steps based on response content
        if any(keyword in ai_response.lower() for keyword in ["symptoms", "condition", "diagnosis"]):
            next_steps.append("Prepare a list of your symptoms and when they started")
        
        if any(keyword in ai_response.lower() for keyword in ["medication", "treatment", "prescription"]):
            next_steps.append("Discuss any current medications with your healthcare provider")
        
        return next_steps
    
    async def get_conversation_summary(self, conversation_id: int) -> Dict[str, Any]:
        """Get a summary of a conversation."""
        return await self.conversation_manager.get_conversation_summary(conversation_id)
    
    async def end_conversation(self, conversation_id: int) -> bool:
        """End a conversation session."""
        return await self.conversation_manager.end_conversation(conversation_id) 