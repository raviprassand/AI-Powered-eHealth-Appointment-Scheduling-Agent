# app/services/book_appointment.py

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from dateutil import parser
import pytz

from app.core.config import settings
from app.core.database import get_db, get_designated_doctor

logger = logging.getLogger(__name__)


# =====================================================================
# Date/time parsing
# =====================================================================

def parse_datetime_from_message(
    message: str,
    intent_entities: Optional[Dict[str, Any]] = None,
) -> datetime:
    """
    Parses flexible date/time expressions from:
    1. LLM-extracted entities if available
    2. User raw message fallback

    Supported examples:
    - tomorrow at 4pm
    - next Monday morning
    - Monday 10:30 am
    - book appointment
    """

    timezone = pytz.timezone("America/Toronto")
    now = datetime.now(timezone)
    message_lower = (message or "").lower()
    intent_entities = intent_entities or {}

    # ---------------------------------------------------------
    # 1. Prefer LLM-extracted date/time fields if available
    # ---------------------------------------------------------
    date_text = str(
        intent_entities.get("date")
        or intent_entities.get("date_text")
        or intent_entities.get("requested_date")
        or ""
    ).lower()

    time_text = str(
        intent_entities.get("time")
        or intent_entities.get("time_text")
        or intent_entities.get("requested_time")
        or intent_entities.get("time_preference")
        or ""
    ).lower()

    combined_text = f"{date_text} {time_text} {message_lower}".strip()

    target_datetime = None

    # ---------------------------------------------------------
    # 2. Parse relative date
    # ---------------------------------------------------------
    if "tomorrow" in combined_text:
        target_datetime = now + timedelta(days=1)

    elif "today" in combined_text:
        target_datetime = now

    elif "next" in combined_text:
        # Example: next monday
        for i in range(1, 8):
            candidate = now + timedelta(days=i)
            weekday = candidate.strftime("%A").lower()
            if weekday in combined_text:
                target_datetime = candidate + timedelta(weeks=1)
                break

    else:
        # Example: monday/tuesday within next 7 days
        for i in range(0, 8):
            candidate = now + timedelta(days=i)
            weekday = candidate.strftime("%A").lower()
            if weekday in combined_text:
                target_datetime = candidate
                break

    # ---------------------------------------------------------
    # 3. Try dateutil parser for explicit dates
    # ---------------------------------------------------------
    if not target_datetime and date_text:
        try:
            parsed = parser.parse(date_text, fuzzy=True)
            target_datetime = timezone.localize(parsed) if parsed.tzinfo is None else parsed.astimezone(timezone)
        except Exception:
            target_datetime = None

    # ---------------------------------------------------------
    # 4. Default date = tomorrow
    # ---------------------------------------------------------
    if not target_datetime:
        target_datetime = now + timedelta(days=1)

    # ---------------------------------------------------------
    # 5. Parse time
    # ---------------------------------------------------------
    hour = settings.DEFAULT_APPOINTMENT_HOUR
    minute = 0

    time_source = f"{time_text} {message_lower}"

    # Morning / afternoon / evening preference
    if "morning" in time_source:
        hour, minute = 9, 0
    elif "afternoon" in time_source:
        hour, minute = 14, 0
    elif "evening" in time_source:
        hour, minute = 17, 0

    # Explicit time like 4pm, 10:30 am
    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", time_source)
    if time_match:
        possible_hour = int(time_match.group(1))
        possible_minute = int(time_match.group(2)) if time_match.group(2) else 0
        meridian = time_match.group(3)

        # Avoid accidentally treating dates like 2026 as time.
        if 0 <= possible_hour <= 23 and 0 <= possible_minute <= 59:
            hour = possible_hour
            minute = possible_minute

            if meridian == "pm" and hour != 12:
                hour += 12
            elif meridian == "am" and hour == 12:
                hour = 0

    return target_datetime.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )


# =====================================================================
# Appointment utilities
# =====================================================================

def extract_requested_doctor_name(
    message: str,
    intent_entities: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Extract requested doctor name from:
    1. LLM entities
    2. Regex fallback: "Dr. Robin"
    """

    intent_entities = intent_entities or {}

    doctor_from_llm = (
        intent_entities.get("doctor")
        or intent_entities.get("doctor_name")
        or intent_entities.get("provider")
    )

    if doctor_from_llm:
        doctor_text = str(doctor_from_llm).lower().replace("dr.", "").replace("dr ", "").strip()
        return doctor_text or None

    match = re.search(r"dr\.?\s*([a-zA-Z]+)", (message or "").lower())
    if match:
        return match.group(1)

    return None


def check_conflict(doctor_id: Any, appointment_datetime: datetime) -> bool:
    """
    Prevents double booking.

    Current method:
    - Fetch existing appointments for the doctor
    - Compare time distance
    - If within conflict window, treat as conflict

    Production alternative:
    - Add DB unique constraint or PostgreSQL exclusion constraint.
    """

    try:
        db = get_db()
        appointments = db.fetch_all(
            table="appointments",
            where={"doctor_id": doctor_id}
        )

        conflict_window_seconds = settings.APPOINTMENT_CONFLICT_WINDOW_MINUTES * 60

        for appt in appointments:
            time_str = appt.get("datetime") or appt.get("appointment_datetime")

            if not time_str:
                continue

            try:
                existing_time = parser.parse(str(time_str))

                if existing_time.tzinfo is None:
                    existing_time = pytz.timezone("America/Toronto").localize(existing_time)

                if appointment_datetime.tzinfo is None:
                    appointment_datetime = pytz.timezone("America/Toronto").localize(appointment_datetime)

                if abs((existing_time - appointment_datetime).total_seconds()) < conflict_window_seconds:
                    return True

            except (ValueError, TypeError):
                continue

        return False

    except Exception as exc:
        logger.error("Conflict check failed: %s", exc, exc_info=True)

        # Safer for healthcare scheduling:
        # if we cannot verify availability, do not book silently.
        return True


def _extract_reason(
    message: str,
    intent_entities: Optional[Dict[str, Any]] = None,
    rag_context: Optional[List[Dict[str, Any]]] = None,
) -> Optional[str]:
    """
    Extract visit reason from LLM entities or user message.
    """

    intent_entities = intent_entities or {}

    reason = (
        intent_entities.get("reason")
        or intent_entities.get("symptom")
        or intent_entities.get("symptoms")
        or intent_entities.get("visit_reason")
    )

    if isinstance(reason, list):
        return ", ".join(str(x) for x in reason)

    if reason:
        return str(reason)

    # Simple fallback: after "because"
    if "because" in message.lower():
        return message.split("because", 1)[-1].strip()

    return None


# =====================================================================
# Main booking function
# =====================================================================

def book_appointment(
    message: str,
    patient_id: str,
    intent_entities: Optional[Dict[str, Any]] = None,
    rag_context: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Books a new appointment.

    AI-safe design:
    - LLM can suggest date/time/reason.
    - Backend still validates patient doctor and conflicts.
    - LLM never directly writes appointment.
    """

    logger.info("Booking request | patient_id=%s | message=%s", patient_id, message)

    intent_entities = intent_entities or {}
    rag_context = rag_context or []

    # ---------------------------------------------------------
    # 1. Parse appointment datetime
    # ---------------------------------------------------------
    appointment_datetime = parse_datetime_from_message(
        message=message,
        intent_entities=intent_entities,
    )

    # ---------------------------------------------------------
    # 2. Get designated family doctor
    # ---------------------------------------------------------
    try:
        db = get_db()
        family_doc_id, family_doc_name = get_designated_doctor(
            str(patient_id),
            db
        )

        if not family_doc_id:
            return {
                "success": False,
                "message": "⚠️ I could not find a designated family doctor for your records.",
                "appointment": None,
            }

    except Exception as exc:
        logger.error("Designated doctor lookup failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "message": "⚠️ Error accessing patient records while checking your designated family doctor.",
            "appointment": None,
        }

    # ---------------------------------------------------------
    # 3. Doctor authorization check
    # ---------------------------------------------------------
    requested_name = extract_requested_doctor_name(
        message=message,
        intent_entities=intent_entities,
    )

    if requested_name and requested_name not in family_doc_name.lower():
        return {
            "success": False,
            "message": (
                f"⚠️ Authorization Error: You are registered with {family_doc_name}. "
                f"You cannot book appointments with Dr. {requested_name.capitalize()}."
            ),
            "appointment": None,
        }

    # ---------------------------------------------------------
    # 4. Conflict check
    # ---------------------------------------------------------
    if check_conflict(family_doc_id, appointment_datetime):
        return {
            "success": False,
            "message": (
                f"⚠️ Sorry, {family_doc_name}'s slot on "
                f"{appointment_datetime.strftime('%A, %B %d at %I:%M %p')} "
                "is unavailable or could not be safely verified. Please pick another time."
            ),
            "appointment": None,
        }

    # ---------------------------------------------------------
    # 5. Create appointment
    # ---------------------------------------------------------
    visit_reason = _extract_reason(
        message=message,
        intent_entities=intent_entities,
        rag_context=rag_context,
    )

    payload = {
        "patient_id": str(patient_id),
        "doctor_id": family_doc_id,
        "datetime": appointment_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Scheduled",
    }

    # Add reason only if your API accepts extra fields.
    # If the API rejects unknown fields, remove this.
    if visit_reason:
        payload["reason"] = visit_reason

    try:
        db = get_db()
        insert_result = db.insert_one(
            table="appointments",
            values=payload,
        )

        return {
            "success": True,
            "message": (
                f"✅ Appointment booked successfully with {family_doc_name} "
                f"on {appointment_datetime.strftime('%A, %B %d at %I:%M %p')}."
                + (f" Reason noted: {visit_reason}." if visit_reason else "")
            ),
            "appointment": payload,
            "raw_insert_result": insert_result,
        }

    except Exception as exc:
        logger.error("Booking insert failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "message": f"❌ Error booking appointment: {exc}",
            "appointment": None,
        }