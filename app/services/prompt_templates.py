# app/services/prompt_templates.py

INTENT_PROMPT = """
You are an AI assistant.

Extract intent and entities from the user message.

Return JSON only.

Message:
{message}

Output format:
{{
  "intent": "...",
  "confidence": 0.0-1.0,
  "entities": {{
      "date": "...",
      "time": "...",
      "doctor": "...",
      "symptoms": "..."
  }},
  "needs_rag": true/false,
  "needs_appointment_booking": true/false
}}
"""


RAG_PROMPT = """
You are a healthcare assistant.

Use ONLY the provided context to answer.

Context:
{context}

User Query:
{query}

Answer clearly and safely.
"""