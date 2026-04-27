# app/services/database_agent.py

import logging
import time
from typing import Dict, Any, List, Optional
from textwrap import shorten

from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseAgent:
    """
    Handles patient-specific data queries.

    Upgraded capabilities:
    - Accepts LLM intent + entities
    - Uses RAG context if provided
    - Falls back to rule-based table mapping
    - Returns structured + formatted output
    """

    def __init__(self, patient_id: str):
        self.patient_id = str(patient_id)
        self.db = get_db()
        logger.info(f"🧠 DatabaseAgent initialized for patient {self.patient_id}")

    # =================================================================
    # MAIN ENTRY
    # =================================================================
    def run_query(
        self,
        query: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        rag_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        start_time = time.time()
        entities = entities or {}
        rag_context = rag_context or []

        logger.info(f"🚀 Running query: {query}")
        logger.info(f"📌 Intent: {intent}")

        # ---------------------------------------------------------
        # 1. Determine table
        # ---------------------------------------------------------
        table_name = self._resolve_table(query, intent)
        logger.info(f"🎯 Selected table: {table_name}")

        # ---------------------------------------------------------
        # 2. Fetch records from DB
        # ---------------------------------------------------------
        try:
            records = self.db.fetch_all(
                table=table_name,
                where={"patient_id": self.patient_id},
            )
            logger.info(f"✅ Retrieved {len(records)} records from {table_name}")
        except Exception as exc:
            logger.error(f"❌ DB fetch failed: {exc}", exc_info=True)
            return {
                "message": f"⚠️ Could not fetch records from {table_name}.",
                "formatted_response": None,
            }

        # ---------------------------------------------------------
        # 3. Merge with RAG context if available
        # ---------------------------------------------------------
        merged_records = self._merge_rag_context(records, rag_context)

        # ---------------------------------------------------------
        # 4. Format output
        # ---------------------------------------------------------
        formatted = self._format_table_pretty(table_name, merged_records)

        logger.info(f"🏁 Completed in {time.time() - start_time:.2f}s")

        return {
            "message": formatted,
            "formatted_response": {
                "table": table_name,
                "record_count": len(records),
            },
        }

    # =================================================================
    # TABLE RESOLUTION
    # =================================================================
    def _resolve_table(self, query: str, intent: Optional[str]) -> str:
        """
        Prefer LLM intent → fallback to keyword mapping
        """

        if intent:
            mapping = {
                "patient_history_query": "medical_history",
                "prescription_query": "prescription",
                "lab_results_query": "lab_tests",
                "billing_query": "billing_records",
                "appointment_history_query": "appointments",
                "vitals_query": "vitals_history",
                "feedback_query": "patient_feedback",
            }
            if intent in mapping:
                return mapping[intent]

        # fallback keyword mapping
        return self._map_query_to_table(query)

    def _map_query_to_table(self, query: str) -> str:
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

    # =================================================================
    # RAG MERGING
    # =================================================================
    def _merge_rag_context(
        self,
        records: List[Dict[str, Any]],
        rag_context: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Optionally enrich results using RAG context.

        Current simple approach:
        - Append RAG-derived info as synthetic records
        """

        if not settings.USE_RAG or not rag_context:
            return records

        enriched = list(records)

        for item in rag_context[: settings.RAG_TOP_K]:
            enriched.append({
                "rag_source": item.get("source"),
                "rag_content": item.get("content"),
                "rag_score": item.get("score"),
            })

        return enriched

    # =================================================================
    # FORMATTING
    # =================================================================
    def _format_table_pretty(self, table_name: str, records: list) -> str:
        if not records:
            return f"No records found for {table_name.replace('_', ' ')}."

        if table_name == "medical_history":
            headers = ["Diagnosis Date", "Condition", "Status", "Severity", "Doctor", "Follow-up"]

            rows = []
            for r in records[:10]:
                rows.append([
                    str(r.get("diagnosis_date", "—")),
                    str(r.get("condition", "—")),
                    str(r.get("status", "—")),
                    str(r.get("severity", "—")),
                    f"Dr.{r.get('diagnosed_by', '—')}",
                    "Yes" if r.get("followup_required") else "No",
                ])

            return self._make_ascii_table(headers, rows, title="📋 Treatment History")

        # generic fallback
        headers = list(records[0].keys())
        rows = [[str(v) for v in rec.values()] for rec in records[:10]]

        return self._make_ascii_table(
            headers,
            rows,
            title=f"📊 {table_name.replace('_', ' ').title()}",
        )

    def _make_ascii_table(self, headers, rows, title=""):
        col_widths = [
            max(len(str(col)) for col in [h] + [r[i] for r in rows]) + 2
            for i, h in enumerate(headers)
        ]

        output = [f"{title}\n"]

        header_line = " | ".join(
            h.ljust(col_widths[i]) for i, h in enumerate(headers)
        )
        divider = "-+-".join("-" * w for w in col_widths)

        output.append(header_line)
        output.append(divider)

        for row in rows:
            output.append(
                " | ".join(
                    shorten(str(c), width=col_widths[i] - 2)
                    for i, c in enumerate(row)
                )
            )

        return "\n".join(output)