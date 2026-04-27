# app/routers/chat.py

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.chat import (
    ChatRequest,
    ChatResponse,
    IntentResult,
    RAGContextItem,
)
from app.services.book_appointment import book_appointment
from app.services.database_agent import DatabaseAgent
from app.services.intent_extractor import IntentExtractor
from app.services.rag_service import RAGService


router = APIRouter()
logger = logging.getLogger(__name__)


# =====================================================================
# Fallback appointment intent detector
# =====================================================================

def is_appointment_intent(message: str) -> bool:
    """
    Rule-based fallback if LLM is unavailable.

    This keeps your original logic alive:
    appointment/book/schedule/consultation/visit.
    """
    keywords = ["appointment", "book", "schedule", "consultation", "visit", "doctor", "checkup"]
    text = message.lower()
    return any(word in text for word in keywords)


def _intent_to_model(intent_payload: Dict[str, Any]) -> IntentResult:
    """
    Converts dict returned by IntentExtractor into Pydantic model.
    """
    return IntentResult(
        intent=intent_payload.get("intent", "general_query"),
        confidence=float(intent_payload.get("confidence", 0.0) or 0.0),
        entities=intent_payload.get("entities", {}) or {},
        needs_rag=bool(intent_payload.get("needs_rag", False)),
        needs_appointment_booking=bool(intent_payload.get("needs_appointment_booking", False)),
        raw_response=intent_payload.get("raw_response"),
    )


def _context_to_models(context_items: List[Dict[str, Any]]) -> List[RAGContextItem]:
    """
    Converts raw RAG context dicts into response models.
    """
    output: List[RAGContextItem] = []

    for item in context_items or []:
        output.append(
            RAGContextItem(
                source=str(item.get("source", "unknown")),
                content=str(item.get("content", "")),
                score=item.get("score"),
                metadata=item.get("metadata", {}) or {},
            )
        )

    return output


def _extract_source_tables(context_items: List[Dict[str, Any]]) -> List[str]:
    """
    Returns unique source names used by RAG.
    """
    sources = []
    for item in context_items or []:
        source = item.get("source")
        if source and source not in sources:
            sources.append(source)
    return sources


# =====================================================================
# POST /chat/send
# =====================================================================

@router.post("/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Main endpoint for chat interactions.

    Upgraded workflow:
    1. Receive frontend message.
    2. Use LLM intent extraction if enabled.
    3. Fall back to keyword/rule-based detection if LLM unavailable.
    4. Retrieve RAG context when useful.
    5. Route to:
       - appointment booking service
       - database patient-record service
       - RAG answer generation
    6. Return response with optional debug details.
    """

    try:
        message = request.message.strip()
        patient_id = request.patient_id or str(settings.DEFAULT_PATIENT_ID)

        logger.info("Chat request received | patient_id=%s | message=%s", patient_id, message)

        debug: Dict[str, Any] = {}
        used_llm = False
        used_rag = False
        rag_context_raw: List[Dict[str, Any]] = []

        # ---------------------------------------------------------
        # 1. Intent extraction: LLM first, deterministic fallback
        # ---------------------------------------------------------
        intent_extractor = IntentExtractor()
        intent_payload = intent_extractor.extract_intent(
            message=message,
            conversation_history=request.conversation_history,
        )

        intent_model = _intent_to_model(intent_payload)
        used_llm = bool(intent_payload.get("used_llm", False))

        # If LLM confidence is weak, keep your original keyword fallback.
        if (
            intent_model.intent == "general_query"
            and is_appointment_intent(message)
        ):
            intent_model.intent = "book_appointment"
            intent_model.needs_appointment_booking = True
            intent_model.needs_rag = True
            intent_model.confidence = max(intent_model.confidence, 0.65)
            intent_model.entities["fallback_reason"] = "keyword_appointment_match"

        debug["intent_payload"] = intent_payload

        # ---------------------------------------------------------
        # 2. RAG retrieval
        # ---------------------------------------------------------
        should_use_rag = (
            settings.USE_RAG
            and (
                intent_model.needs_rag
                or intent_model.intent in {
                    "patient_history_query",
                    "prescription_query",
                    "lab_results_query",
                    "billing_query",
                    "book_appointment",
                    "general_healthcare_query",
                }
            )
        )

        if should_use_rag:
            rag_service = RAGService()
            rag_context_raw = rag_service.retrieve_context(
                query=message,
                patient_id=str(patient_id),
                intent=intent_model.intent,
                entities=intent_model.entities,
            )
            used_rag = len(rag_context_raw) > 0
            debug["rag_context_count"] = len(rag_context_raw)

        # ---------------------------------------------------------
        # 3. Route to appointment booking
        # ---------------------------------------------------------
        if intent_model.needs_appointment_booking or intent_model.intent == "book_appointment":
            logger.info("Routing to appointment booking service")

            result = book_appointment(
                message=message,
                patient_id=str(patient_id),
                intent_entities=intent_model.entities,
                rag_context=rag_context_raw,
            )

            if isinstance(result, dict):
                response_message = result.get("message", "")
                success = bool(result.get("success", True))
                debug["booking_result"] = result
            else:
                response_message = str(result)
                success = True
                debug["booking_result"] = {"raw": str(result)}

            return ChatResponse(
                message=response_message,
                formatted_response={"success": success},
                patient_id=str(patient_id),
                intent=intent_model,
                rag_context=_context_to_models(rag_context_raw) if request.include_debug else None,
                source_tables=_extract_source_tables(rag_context_raw),
                used_llm=used_llm,
                used_rag=used_rag,
                debug=debug if request.include_debug else None,
            )

        # ---------------------------------------------------------
        # 4. Route to patient database agent
        # ---------------------------------------------------------
        if intent_model.intent in {
            "patient_history_query",
            "prescription_query",
            "lab_results_query",
            "billing_query",
            "appointment_history_query",
            "vitals_query",
            "feedback_query",
        }:
            logger.info("Routing to DatabaseAgent | intent=%s", intent_model.intent)

            database_agent = DatabaseAgent(patient_id=str(patient_id))
            result = database_agent.run_query(
                query=message,
                intent=intent_model.intent,
                entities=intent_model.entities,
                rag_context=rag_context_raw,
            )

            if isinstance(result, dict):
                response_message = result.get("message", "")
                formatted_response = result.get("formatted_response")
                debug["database_agent_result"] = result
            else:
                response_message = str(result)
                formatted_response = None
                debug["database_agent_result"] = {"raw": str(result)}

            return ChatResponse(
                message=response_message,
                formatted_response=formatted_response,
                patient_id=str(patient_id),
                intent=intent_model,
                rag_context=_context_to_models(rag_context_raw) if request.include_debug else None,
                source_tables=_extract_source_tables(rag_context_raw),
                used_llm=used_llm,
                used_rag=used_rag,
                debug=debug if request.include_debug else None,
            )

        # ---------------------------------------------------------
        # 5. General RAG-grounded answer
        # ---------------------------------------------------------
        if used_rag:
            rag_service = RAGService()
            answer = rag_service.generate_answer(
                query=message,
                patient_id=str(patient_id),
                context_items=rag_context_raw,
            )

            return ChatResponse(
                message=answer,
                formatted_response=None,
                patient_id=str(patient_id),
                intent=intent_model,
                rag_context=_context_to_models(rag_context_raw) if request.include_debug else None,
                source_tables=_extract_source_tables(rag_context_raw),
                used_llm=used_llm,
                used_rag=used_rag,
                debug=debug if request.include_debug else None,
            )

        # ---------------------------------------------------------
        # 6. Final fallback
        # ---------------------------------------------------------
        fallback_agent = DatabaseAgent(patient_id=str(patient_id))
        fallback_response = fallback_agent.run_query(message)

        return ChatResponse(
            message=str(fallback_response.get("message", fallback_response))
            if isinstance(fallback_response, dict)
            else str(fallback_response),
            formatted_response=fallback_response.get("formatted_response")
            if isinstance(fallback_response, dict)
            else None,
            patient_id=str(patient_id),
            intent=intent_model,
            rag_context=None,
            source_tables=None,
            used_llm=used_llm,
            used_rag=used_rag,
            debug=debug if request.include_debug else None,
        )

    except Exception as exc:
        logger.error("Error in /chat/send: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))