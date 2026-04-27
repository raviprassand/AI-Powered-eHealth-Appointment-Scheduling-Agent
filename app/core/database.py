# app/core/database.py

import logging
from typing import Optional, Dict, Any, List
import requests
from requests import Response

from app.core.config import settings

logger = logging.getLogger(__name__)


# =====================================================================
# API-backed database shim
# =====================================================================

class APIBackedSQLShim:
    """
    This class behaves like a lightweight database wrapper,
    but internally it calls your hosted REST table API:

        GET  /table/<table_name>
        POST /table/<table_name>

    This keeps your existing project compatible while allowing services
    like appointment booking, DatabaseAgent, and RAG retrieval to access
    patient data through one common interface.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        if not base_url:
            raise ValueError("DATABASE_API_URL/base_url cannot be empty")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _build_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _get(self, path: str, **kwargs) -> Response:
        url = self._build_url(path)
        logger.debug("GET %s params=%s", url, kwargs.get("params"))
        return requests.get(url, timeout=self.timeout, **kwargs)

    def _post(self, path: str, json: Dict[str, Any]) -> Response:
        url = self._build_url(path)
        logger.debug("POST %s json=%s", url, json)
        return requests.post(url, json=json, timeout=self.timeout)

    @staticmethod
    def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
        """
        Your API has returned different shapes in different scripts:
        - {"data": [...]}
        - {"records": [...]}
        - [...] directly

        This normalizes all formats into a list of dictionaries.
        """
        if payload is None:
            return []

        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            if isinstance(payload.get("data"), list):
                return payload["data"]
            if isinstance(payload.get("records"), list):
                return payload["records"]
            if isinstance(payload.get("rows"), list):
                return payload["rows"]

        return []

    def fetch_all(self, table: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows matching query params from /table/<table>.
        """
        path = f"table/{table}"
        resp = self._get(path, params=where or {})
        resp.raise_for_status()
        return self._extract_rows(resp.json())

    def fetch_one(self, table: str, where: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch first row matching query params from /table/<table>.
        """
        rows = self.fetch_all(table=table, where=where or {})
        return rows[0] if rows else None

    def insert_one(self, table: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert one row into /table/<table>.
        """
        path = f"table/{table}"
        resp = self._post(path, json=values)
        resp.raise_for_status()

        try:
            payload = resp.json()
        except Exception:
            payload = {"status": "success", "raw_text": resp.text}

        return payload


# =====================================================================
# Database manager
# =====================================================================

class DatabaseManager:
    """
    Singleton-style manager.

    In this project, runtime database access is currently API-backed.
    This manager also includes compatibility methods expected by main.py:
    - test_connection()
    - get_pool_status()
    - close_connections()
    """

    _instance = None

    DEFAULT_API_URL = "https://aetab8pjmb.us-east-1.awsapprunner.com"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._db: Optional[APIBackedSQLShim] = None
        self._api_url = (
            settings.DATABASE_API_URL
            or self.DEFAULT_API_URL
        )

    def get_database(self) -> APIBackedSQLShim:
        if self._db is None:
            self._db = APIBackedSQLShim(base_url=self._api_url)
        return self._db

    def test_connection(self) -> bool:
        """
        Lightweight health check against the table API.
        """
        try:
            db = self.get_database()
            # Use a safe known table from your existing project.
            db.fetch_all("patients_registration", where={},)
            logger.info("Database API connection test successful")
            return True
        except Exception as exc:
            logger.warning("Database API connection test failed: %s", exc)
            return False

    def get_pool_status(self) -> Dict[str, Any]:
        """
        Compatibility method.
        Since this is API-backed, there is no SQL connection pool.
        """
        return {
            "mode": "api_backed",
            "base_url": self._api_url,
            "pooling": False,
            "status": "available" if self._db else "not_initialized",
        }

    def close_connections(self) -> None:
        """
        Compatibility method.
        No persistent DB pool is maintained here.
        """
        self._db = None
        logger.info("Database API shim closed/reset")


db_manager = DatabaseManager()


def get_db() -> APIBackedSQLShim:
    return db_manager.get_database()


# =====================================================================
# Shared patient/doctor helpers
# =====================================================================

def get_designated_doctor(patient_id: str, db: APIBackedSQLShim):
    """
    Returns:
        (doctor_id, doctor_name)

    Business rule:
    Patient should book appointments only with their designated family doctor.

    Data source:
    - patients_registration.family_doctor_id
    - doctors_registration.doctor_id / id
    """

    patient = db.fetch_one(
        table="patients_registration",
        where={"patient_id": patient_id}
    )

    if not patient or not patient.get("family_doctor_id"):
        return None, None

    doctor_id = patient["family_doctor_id"]

    # Attempt 1: filter by doctor_id
    doctor = db.fetch_one(
        table="doctors_registration",
        where={"doctor_id": doctor_id}
    )

    # Attempt 2: filter by id
    if not doctor:
        doctor = db.fetch_one(
            table="doctors_registration",
            where={"id": doctor_id}
        )

    # Attempt 3: brute force fallback
    if not doctor:
        logger.info(
            "Direct doctor lookup failed for doctor_id=%s. Trying fetch_all fallback.",
            doctor_id
        )
        all_doctors = db.fetch_all(
            table="doctors_registration",
            where={}
        )

        for doc in all_doctors:
            d_id = doc.get("doctor_id") or doc.get("id")
            if str(d_id) == str(doctor_id):
                doctor = doc
                break

    if not doctor:
        return doctor_id, "Unknown Doctor"

    full_name = doctor.get("name")
    first = doctor.get("first_name")
    last = doctor.get("last_name")

    if full_name:
        doctor_name = f"Dr. {full_name}".strip()
    elif first or last:
        doctor_name = f"Dr. {first or ''} {last or ''}".strip()
    else:
        doctor_name = "Dr. (Name Not Found)"

    doctor_name = doctor_name.replace("Dr. Dr.", "Dr.").strip()

    return doctor_id, doctor_name


def get_patient_profile(patient_id: str, db: Optional[APIBackedSQLShim] = None) -> Optional[Dict[str, Any]]:
    """
    Reusable helper for RAG and patient-context retrieval.
    """
    db = db or get_db()
    return db.fetch_one(
        table="patients_registration",
        where={"patient_id": patient_id}
    )


def fetch_patient_table(
    table: str,
    patient_id: str,
    db: Optional[APIBackedSQLShim] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Reusable helper used by DatabaseAgent and RAGService.

    It fetches patient-specific records from your API-backed tables.
    """
    db = db or get_db()

    rows = db.fetch_all(
        table=table,
        where={"patient_id": patient_id}
    )

    if limit is not None:
        return rows[:limit]

    return rows