# app/services/intent_extractor.py

import json
import logging
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.services.llm_utilities import LLMClient
from app.services.prompt_templates import INTENT_PROMPT

logger = logging.getLogger(__name__)


class IntentExtractor:

    def __init__(self):
        self.llm = LLMClient()

    def extract_intent(
        self,
        message: str,
        conversation_history: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:

        if not settings.USE_LLM_INTENT or not self.llm.enabled:
            return self._fallback_intent(message)

        prompt = INTENT_PROMPT.format(message=message)

        response = self.llm.chat_completion(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.1,
        )

        if not response:
            return self._fallback_intent(message)

        try:
            parsed = json.loads(response)

            return {
                "intent": parsed.get("intent", "general_query"),
                "confidence": parsed.get("confidence", 0.7),
                "entities": parsed.get("entities", {}),
                "needs_rag": parsed.get("needs_rag", True),
                "needs_appointment_booking": parsed.get("needs_appointment_booking", False),
                "used_llm": True,
                "raw_response": parsed,
            }

        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}")
            return self._fallback_intent(message)

    def _fallback_intent(self, message: str) -> Dict[str, Any]:
        text = message.lower()

        if any(k in text for k in ["appointment", "book", "schedule"]):
            return {
                "intent": "book_appointment",
                "confidence": 0.6,
                "entities": {},
                "needs_rag": True,
                "needs_appointment_booking": True,
                "used_llm": False,
            }

        if "prescription" in text:
            intent = "prescription_query"
        elif "lab" in text:
            intent = "lab_results_query"
        elif "billing" in text:
            intent = "billing_query"
        else:
            intent = "patient_history_query"

        return {
            "intent": intent,
            "confidence": 0.5,
            "entities": {},
            "needs_rag": True,
            "needs_appointment_booking": False,
            "used_llm": False,
        }