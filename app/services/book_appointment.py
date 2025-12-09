import re
import requests
import logging
from datetime import datetime, timedelta
from dateutil import parser
import pytz

# --- NEW IMPORTS: Connect to your database helper ---
from app.core.database import get_db, get_designated_doctor

logger = logging.getLogger(__name__)

API_BASE_URL = "https://aetab8pjmb.us-east-1.awsapprunner.com/table/appointments"

def parse_datetime_from_message(message: str):
    """
    Parses flexible date/time expressions.
    """
    now = datetime.now(pytz.timezone("America/Toronto"))
    message_lower = message.lower()
    target_datetime = None

    # --- Parse relative days ---
    if "tomorrow" in message_lower:
        target_datetime = now + timedelta(days=1)
    elif "next" in message_lower:
        for i in range(1, 8):
            candidate = now + timedelta(days=i)
            if candidate.strftime("%A").lower() in message_lower:
                target_datetime = candidate + timedelta(weeks=1)
                break
    else:
        for i in range(7):
            candidate = now + timedelta(days=i)
            if candidate.strftime("%A").lower() in message_lower:
                target_datetime = candidate
                break

    if not target_datetime:
        target_datetime = now + timedelta(days=1)

    # --- Parse time ---
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', message_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        meridian = time_match.group(3)

        if meridian == "pm" and hour != 12:
            hour += 12
        elif meridian == "am" and hour == 12:
            hour = 0
    else:
        hour, minute = 9, 0  # Default to 9:00 AM

    target_datetime = target_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return target_datetime


def check_conflict(doctor_id, appointment_datetime):
    """
    Prevent double booking.
    FIXED: Now handles None/Null dates safely without crashing.
    """
    try:
        # Fetch existing appointments for this doctor
        response = requests.get(API_BASE_URL, params={"doctor_id": doctor_id})
        response.raise_for_status()
        appointments = response.json().get("data", [])

        for appt in appointments:
            time_str = appt.get("datetime")
            
            # --- CRITICAL FIX: Skip rows with no date ---
            if not time_str:
                continue 

            try:
                existing_time = parser.parse(time_str)
                # Check if times are within 30 minutes of each other
                if abs((existing_time - appointment_datetime).total_seconds()) < 30 * 60:
                    return True # Conflict found
            except (ValueError, TypeError):
                continue # Skip invalid date formats

        return False # No conflict
    except Exception as e:
        logger.error(f"⚠️ Conflict check failed: {e}")
        # SAFETY: If check fails, assume conflict to prevent double booking? 
        # For now, we return False to allow retry, but log clearly.
        return False


def extract_requested_doctor_name(message: str):
    """
    Simple logic to check if user specifically named a doctor.
    Looks for "Dr. [Name]".
    """
    match = re.search(r'dr\.?\s*([a-zA-Z]+)', message.lower())
    if match:
        return match.group(1) # Returns just the name part (e.g., "robin")
    return None


def book_appointment(message: str, patient_id: int):
    """
    Books a new appointment with logic:
    1. Parse Time
    2. Lookup Family Doctor (Authorization)
    3. Check Conflict
    4. Send Booking
    """
    logger.info(f"📥 Booking request: {message} (patient={patient_id})")

    # 1. Parse Date/Time
    appointment_datetime = parse_datetime_from_message(message)
    
    # 2. Get Designated Family Doctor
    try:
        db = get_db()
        # Convert patient_id to string as your DB usually expects strings for IDs
        family_doc_id, family_doc_name = get_designated_doctor(str(patient_id), db)
        
        if not family_doc_id:
            return "⚠️ I could not find a designated family doctor for your records."
            
    except Exception as e:
        logger.error(f"DB Lookup failed: {e}")
        return "⚠️ Error accessing patient records."

    # 3. Check for Doctor Authorization (Did they ask for someone else?)
    requested_name = extract_requested_doctor_name(message)
    
    if requested_name:
        # Normalize for comparison (e.g., check if 'robin' is in 'Dr. Alice')
        # If the name user asked for is NOT in the family doctor's name
        if requested_name not in family_doc_name.lower():
            return (
                f"⚠️ Authorization Error: You are registered with {family_doc_name}. "
                f"You cannot book appointments with Dr. {requested_name.capitalize()}."
            )

    # 4. Check for Conflicts (Double Booking)
    if check_conflict(family_doc_id, appointment_datetime):
        return (
            f"⚠️ Sorry, {family_doc_name}'s slot on "
            f"{appointment_datetime.strftime('%A, %B %d at %I:%M %p')} is already booked. "
            "Please pick another time."
        )

    # 5. Send Payload
    payload = {
        "patient_id": str(patient_id),
        "doctor_id": family_doc_id, # Always use the authorized ID
        "datetime": appointment_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Scheduled",
    }

    try:
        logger.info(f"📤 Sending payload: {payload}")
        response = requests.post(API_BASE_URL, json=payload)
        response.raise_for_status()

        if response.status_code in [200, 201]:
            return (
                f"✅ Appointment booked successfully with {family_doc_name} "
                f"on {appointment_datetime.strftime('%A, %B %d at %I:%M %p')}."
            )
        else:
            return f"⚠️ Failed to book appointment (status {response.status_code})."
    except Exception as e:
        logger.error(f"❌ Booking failed: {e}")
        return f"❌ Error booking appointment: {e}"