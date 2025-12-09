# app/routers/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.book_appointment import book_appointment
from app.services.database_agent import DatabaseAgent
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------
# 📦 Request / Response Models
# --------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    patient_id: str | None = None


class ChatResponse(BaseModel):
    success: bool
    message: str
    patient_id: str | None = None


# --------------------------------------------------------------------
# 🧠 Helper to detect "appointment" intent
# --------------------------------------------------------------------
def is_appointment_intent(message: str) -> bool:
    keywords = ["appointment", "book", "schedule", "consultation", "visit"]
    return any(word in message.lower() for word in keywords)


# --------------------------------------------------------------------
# 💬 POST /chat/send
# --------------------------------------------------------------------
@router.post("/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Main endpoint for chat interactions:
    - Detects if it's an appointment or database query.
    - Routes to book_appointment() or DatabaseAgent accordingly.
    """

    try:
        logger.info(f"🕐 REQUEST START: {request.message}...")
        patient_id = request.patient_id or str(settings.DEFAULT_PATIENT_ID)
        logger.info(f"👤 Using patient_id={patient_id}")

        # ✅ 1. Appointment Booking Intent
        if is_appointment_intent(request.message):
            logger.info("🗓 Detected appointment intent — routing to book_appointment service.")

            # book_appointment is synchronous
            result = book_appointment(request.message, patient_id)

        # ✅ 2. Database Query Intent
        else:
            logger.info("🔍 Starting DatabaseAgent...")
            database_agent = DatabaseAgent(patient_id)
            result = database_agent.run_query(request.message)

        # ----------------------------------------------------------------
        # 🧩 Normalize result to a proper ChatResponse
        # ----------------------------------------------------------------
        if isinstance(result, dict):
            # Example: {'success': True, 'message': '✅ Appointment booked ...'}
            return ChatResponse(
                success=result.get("success", True),
                message=result.get("message", ""),
                patient_id=str(patient_id),
            )
        else:
            # If book_appointment returned a plain string or object
            return ChatResponse(
                success=True,
                message=str(result),
                patient_id=str(patient_id),
            )

    except Exception as e:
        logger.error(f"❌ Error in send_message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
