import requests
import logging
import time
from textwrap import shorten
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseAgent:
    """
    Handles patient-specific data queries via API or local SQL.
    Uses table mapping and outputs neatly formatted results.
    """

    def __init__(self, patient_id: int):
        self.patient_id = patient_id
        self.api_url = settings.DATABASE_API_URL
        self.sql_uri = settings.SQL_URI
        self.use_api = settings.USE_DB_API or (self.api_url and self.api_url.startswith("http"))
        logger.info(f"🧠 DatabaseAgent initialized for patient {self.patient_id}")

    # -------------------- Query Runner --------------------
    def run_query(self, user_query: str):
        start_time = time.time()
        logger.info(f"🚀 Starting query: {user_query}")

        # Map to table
        table_name = self.map_query_to_table(user_query)
        logger.info(f"🎯 Mapped query → table: {table_name}")

        params = {"patient_id": str(self.patient_id)}
        if self.use_api:
            url = f"{self.api_url}/table/{table_name}"
        else:
            url = f"{self.sql_uri}/table/{table_name}"

        logger.info(f"🔗 Routing to API: {url} params={params}")

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get("records") or data.get("data") or []
            logger.info(f"✅ Query completed for table {table_name}")
        except Exception as e:
            logger.error(f"❌ Error executing query: {e}", exc_info=True)
            return f"⚠️ Could not fetch records from {table_name}."

        formatted = self.format_table_pretty(table_name, records)
        logger.info(f"🏁 DatabaseAgent completed in {time.time() - start_time:.2f}s")
        return formatted

    # -------------------- Table Mapper --------------------
    def map_query_to_table(self, query: str) -> str:
        q = query.lower()
        if "treatment" in q or "medical" in q or "history" in q:
            return "medical_history"
        if "prescription" in q or "medicine" in q:
            return "prescription"
        if "appointment" in q or "visit" in q:
            return "appointments"
        if "lab" in q or "test" in q or "pathology" in q:
            return "lab_tests"
        if "billing" in q or "payment" in q:
            return "billing_records"
        if "feedback" in q:
            return "patient_feedback"
        if "vital" in q:
            return "vitals_history"
        return "medical_history"

    # -------------------- Pretty Table Formatter --------------------
    def format_table_pretty(self, table_name: str, records: list) -> str:
        """Formats records in a readable fixed-width table (for plain text UIs)."""
        if not records:
            return f"No records found for {table_name.replace('_', ' ')}."

        if table_name == "medical_history":
            headers = ["Diagnosis Date", "Condition", "Status", "Severity", "Doctor", "Follow-up"]
            rows = []
            for r in records[:10]:  # show top 10 for brevity
                rows.append([
                    r.get("diagnosis_date", "—"),
                    r.get("condition", "—"),
                    r.get("status", "—"),
                    r.get("severity", "—"),
                    f"Dr.{r.get('diagnosed_by', '—')}",
                    "Yes" if r.get("followup_required") else "No"
                ])
            return self.make_ascii_table(headers, rows, title="📋 Treatment History")

        # Generic for others
        headers = list(records[0].keys())
        rows = [[str(v) for v in rec.values()] for rec in records[:10]]
        return self.make_ascii_table(headers, rows, title=f"📊 {table_name.replace('_', ' ').title()}")

    # -------------------- ASCII Table Maker --------------------
    def make_ascii_table(self, headers, rows, title=""):
        """Formats data into fixed-width ASCII table."""
        col_widths = [max(len(str(col)) for col in [h] + [r[i] for r in rows]) + 2 for i, h in enumerate(headers)]

        output = [f"{title}\n"]
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        divider = "-+-".join("-" * w for w in col_widths)
        output.append(header_line)
        output.append(divider)

        for row in rows:
            output.append(" | ".join(shorten(str(c), width=col_widths[i] - 2) for i, c in enumerate(row)))

        return "\n".join(output)
