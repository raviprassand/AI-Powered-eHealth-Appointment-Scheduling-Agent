# app/models/chat.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Represents one message in a conversation.
    Useful later if you want to send chat history to the LLM.
    """
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """
    Request body received from the frontend.

    Example:
    {
        "message": "Book me an appointment next Monday morning",
        "patient_id": "143",
        "include_debug": true
    }
    """
    message: str = Field(..., description="User's message")
    patient_id: Optional[str] = Field(default=None, description="Patient ID")
    include_debug: bool = Field(
        default=False,
        description="If true, backend returns LLM/RAG/debug metadata"
    )
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional previous messages for future conversational memory"
    )


class IntentResult(BaseModel):
    """
    Structured result from LLM/intent extraction.
    """
    intent: str = Field(
        default="general_query",
        description="Detected user intent"
    )
    confidence: float = Field(
        default=0.0,
        description="Intent confidence between 0 and 1"
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted fields like date, time, doctor, table, symptoms"
    )
    needs_rag: bool = Field(
        default=False,
        description="Whether the query needs patient/context retrieval"
    )
    needs_appointment_booking: bool = Field(
        default=False,
        description="Whether appointment booking flow should run"
    )
    raw_response: Optional[Any] = Field(
        default=None,
        description="Raw LLM output or fallback output"
    )


class RAGContextItem(BaseModel):
    """
    One retrieved context item used by RAG.
    """
    source: str = Field(..., description="Source table or document")
    content: str = Field(..., description="Retrieved text content")
    score: Optional[float] = Field(default=None, description="Similarity/relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """
    Response returned to frontend.
    """
    message: str
    formatted_response: Optional[Dict[str, Any]] = None
    audio_url: Optional[str] = None
    patient_id: Optional[str] = None

    intent: Optional[IntentResult] = None
    rag_context: Optional[List[RAGContextItem]] = None
    source_tables: Optional[List[str]] = None
    used_llm: bool = False
    used_rag: bool = False

    debug: Optional[Dict[str, Any]] = None