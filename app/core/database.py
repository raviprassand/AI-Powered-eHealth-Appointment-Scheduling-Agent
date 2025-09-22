# app/core/database.py
import os
import time
import logging
from typing import Optional, Dict, Any

import requests
from requests import Response

# If you still want to support direct DB mode as a fallback:
try:
    from langchain_community.utilities.sql_database import SQLDatabase  # noqa
    _HAS_SQL = True
except Exception:
    _HAS_SQL = False

from app.core.config import settings

logger = logging.getLogger(__name__)

def _bool_env(v: Optional[str], default: bool = True) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

class APIBackedSQLShim:
    """
    A tiny shim that emulates the parts of LangChain's SQLDatabase you actually
    use (typically .run(<sql>) and maybe get_table_info), but forwards to your
    Database API instead of opening a SQL connection.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # --- common helpers ---
    def _get(self, path: str, **kwargs) -> Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        return requests.get(url, timeout=self.timeout, **kwargs)

    def _post(self, path: str, json: Dict[str, Any]) -> Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        return requests.post(url, json=json, timeout=self.timeout)

    # --- methods mimicking SQLDatabase usage patterns ---

    def run(self, sql: str) -> Any:
        """
        Emulate SQLDatabase.run(sql): forward a raw SQL string to your API.
        Your API should accept { "sql": "<query>" } and return JSON rows.
        Adjust the payload/endpoint if your API is different.
        """
        resp = self._post("/query", json={"sql": sql})
        resp.raise_for_status()
        # Expecting rows or a structured JSON; return as-is for your caller
        return resp.json()

    def get_table_info(self, table_names=None) -> str:
        """
        If your app/LLM needs schema info, expose an endpoint that returns
        DDL/columns. Return a string (like SQLDatabase.get_table_info does).
        """
        params = {}
        if table_names:
            params["tables"] = ",".join(table_names)
        resp = self._get("/schema", params=params)
        resp.raise_for_status()
        data = resp.json()
        # Convert JSON schema to a textual description if needed:
        # Here we just pretty-format; tune to match your LLM prompts.
        lines = []
        for tbl in data.get("tables", []):
            cols = ", ".join(f"{c['name']} {c.get('type','')}".strip()
                             for c in tbl.get("columns", []))
            lines.append(f"Table: {tbl['name']}({cols})")
        return "\n".join(lines)

    def get_usable_table_names(self) -> set:
        """Optional: list tables if your code calls this."""
        resp = self._get("/tables")
        resp.raise_for_status()
        data = resp.json()
        return set(data.get("tables", []))

class DatabaseManager:
    """Singleton selector that provides either the API-backed shim or real SQL DB."""
    _instance: Optional["DatabaseManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Lazy init: don't hit network on import
        self._db = None
        self._init_done = False
        self._mode_api = bool(getattr(settings, "USE_DB_API", False))
        self._sql_uri = getattr(settings, "SQL_URI", None)
        self._api_url = getattr(settings, "DATABASE_API_URL", "http://127.0.0.1:5000/api")
        
    def _initialize(self):
        if self._init_done:
            return

        start = time.time()
        if self._mode_api:
            logger.info(f"🔄 Initializing Database API client @ {self._api_url}")
            self._db = APIBackedSQLShim(base_url=self._api_url, timeout=30.0)
            logger.info(f"✅ Database API client ready in {(time.time() - start) * 1000:.0f}ms")
        else:
            #if not _HAS_SQL:
             #   raise RuntimeError("Direct SQL mode requested but langchain SQLDatabase not available.")

            # Pick URI: SQLite if given, otherwise MySQL from settings
            if self._sql_uri:
                uri = self._sql_uri  
            else:
                uri = (
            f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
            f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
                )
            logger.info(f"🔄 Initializing direct SQL connection with {uri}")
            self._db = SQLDatabase.from_uri(uri)

        self._init_done = True

    def get_database(self):
        """Return the underlying handle (API shim or SQLDatabase)."""
        if self._db is None:
            self._initialize()
        return self._db

    # --- Convenience utilities used elsewhere in your app ---

    def test_connection(self) -> bool:
        try:
            if self._mode_api:
                # Expect API /health to return 200 with {"status":"ok"} or similar
                resp = requests.get(f"{self._api_url.rstrip('/')}/health", timeout=5)
                resp.raise_for_status()
                logger.info(f"✅ API health: {resp.text}")
                return True
            else:
                if self._db is None:
                    self._initialize()
                result = self._db.run("SELECT 1 as test")
                logger.info(f"✅ SQL test result: {result}")
                return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    def get_pool_status(self) -> dict:
        try:
            if self._mode_api:
                return {"status": "connected", "mode": "api", "endpoint": self._api_url}
            else:
                return {
                    "status": "connected" if self._db else "not_initialized",
                    "mode": "sql",
                    "database": getattr(settings, "DATABASE_NAME", None),
                }
        except Exception as e:
            logger.error(f"❌ Error getting connection status: {e}")
            return {"status": "error", "error": str(e)}

    def close_connections(self):
        # Nothing to close explicitly in API mode.
        self._db = None
        self._init_done = False
        logger.info("🔐 Connection handle released")

# Global instance, but lazy-inits on first use
db_manager = DatabaseManager()
