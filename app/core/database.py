# app/core/database.py
import os
import logging
from typing import Optional, Dict, Any
import requests
from requests import Response
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Utility ---
def _bool_env(v: Optional[str], default: bool = True) -> bool:
    if v is None: return default
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

# --- API Shim ---
class APIBackedSQLShim:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, **kwargs) -> Response:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        return requests.get(url, timeout=self.timeout, **kwargs)

    def _post(self, path: str, json: Dict[str, Any]) -> Response:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        return requests.post(url, json=json, timeout=self.timeout)

    def fetch_one(self, table: str, where: Dict[str, Any]):
        path = f"table/{table}"
        resp = self._get(path, params=where)
        resp.raise_for_status()
        rows = resp.json().get("data", [])
        return rows[0] if rows else None

# --- Database Manager ---
class DatabaseManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        self._db = None
        self._api_url = getattr(settings, "DATABASE_API_URL", "https://aetab8pjmb.us-east-1.awsapprunner.com")
    def get_database(self) -> APIBackedSQLShim:
        if self._db is None:
            self._db = APIBackedSQLShim(base_url=self._api_url)
        return self._db

db_manager = DatabaseManager()
def get_db() -> APIBackedSQLShim: return db_manager.get_database()

# =====================================================================
#  Designated Doctor Lookup (STRICT FILTERING)
# =====================================================================
# app/core/database.py

def get_designated_doctor(patient_id: str, db: APIBackedSQLShim):
    """
    Returns (doctor_id, doctor_name)
    Uses a 'Brute Force' lookup if the API filter fails.
    """

    # 1. Fetch patient row
    patient = db.fetch_one(
        table="patients_registration", 
        where={"patient_id": patient_id}
    )

    if not patient or not patient.get("family_doctor_id"):
        return None, None

    doctor_id = patient["family_doctor_id"]

    # 2. Fetch doctor row
    # Attempt 1: Direct Lookup
    doctor = db.fetch_one(table="doctors_registration", where={"doctor_id": doctor_id})

    # Attempt 2: Direct Lookup with 'id'
    if not doctor:
        doctor = db.fetch_one(table="doctors_registration", where={"id": doctor_id})

    # Attempt 3: BRUTE FORCE (The "Nuclear Option")
    # If the API refuses to filter, we fetch EVERYONE and find ID 2 ourselves.
    if not doctor:
        logger.info(f"⚠️ Direct lookup failed for Doc {doctor_id}. Trying brute force list...")
        all_doctors = db.fetch_all(table="doctors_registration", where={})
        
        for doc in all_doctors:
            # Check both possible ID keys
            d_id = doc.get("doctor_id") or doc.get("id")
            if str(d_id) == str(doctor_id):
                doctor = doc
                break

    if not doctor:
        return doctor_id, "Unknown Doctor"

    # 3. Extract Name
    full_name = doctor.get('name')
    first = doctor.get('first_name')
    last = doctor.get('last_name')

    if full_name:
        doctor_name = f"Dr. {full_name}".strip()
    elif first or last:
        doctor_name = f"Dr. {first or ''} {last or ''}".strip()
    else:
        doctor_name = "Dr. (Name Not Found)"

    if "Dr. Dr." in doctor_name:
        doctor_name = doctor_name.replace("Dr. Dr.", "Dr.")

    return doctor_id, doctor_name