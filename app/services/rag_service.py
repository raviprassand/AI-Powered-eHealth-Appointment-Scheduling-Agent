# app/services/rag_service.py

import logging
from typing import List, Dict, Any

from app.core.database import fetch_patient_table
from app.core.config import settings
from app.services.llm_utilities import LLMClient
from app.services.prompt_templates import RAG_PROMPT

logger = logging.getLogger(__name__)


class RAGService:

    def __init__(self):
        self.llm = LLMClient()

    def retrieve_context(
        self,
        query: str,
        patient_id: str,
        intent: str,
        entities: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        tables = [
            "medical_history",
            "prescription",
            "lab_tests",
            "appointments",
        ]

        context = []

        for table in tables:
            try:
                records = fetch_patient_table(table, patient_id, limit=3)

                for r in records:
                    context.append({
                        "source": table,
                        "content": str(r),
                        "score": 1.0,
                        "metadata": r,
                    })

            except Exception as e:
                logger.warning(f"RAG fetch failed for {table}: {e}")

        return context[: settings.RAG_TOP_K]

    def generate_answer(
        self,
        query: str,
        patient_id: str,
        context_items: List[Dict[str, Any]],
    ) -> str:

        if not self.llm.enabled:
            return "⚠️ AI response unavailable."

        context_text = "\n".join([c["content"] for c in context_items])

        prompt = RAG_PROMPT.format(
            query=query,
            context=context_text,
        )

        response = self.llm.chat_completion(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2,
        )

        return response or "⚠️ Could not generate response."