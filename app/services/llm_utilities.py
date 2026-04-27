# app/services/llm_utilities.py

import logging
from typing import List, Dict, Any, Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)


# =====================================================================
# LLM CLIENT WRAPPER
# =====================================================================

class LLMClient:
    """
    Centralized OpenAI client wrapper.

    Handles:
    - Chat completions (intent extraction, RAG answers)
    - Embeddings (vector search)
    - Safe fallback if API key missing
    """

    def __init__(self):
        self.enabled = bool(settings.OPENAI_API_KEY)

        if self.enabled:
            openai.api_key = settings.OPENAI_API_KEY
            logger.info("LLMClient initialized with OpenAI key")
        else:
            logger.warning("⚠️ OpenAI API key not set — LLM features disabled")

    # -----------------------------------------------------------------
    # Chat completion
    # -----------------------------------------------------------------
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Optional[str]:

        if not self.enabled:
            return None

        try:
            response = openai.chat.completions.create(
                model=model or settings.LLM_MODEL,
                messages=messages,
                temperature=temperature,
            )

            return response.choices[0].message.content

        except Exception as exc:
            logger.error("LLM chat completion failed: %s", exc, exc_info=True)
            return None

    # -----------------------------------------------------------------
    # Embeddings (for RAG / vector search)
    # -----------------------------------------------------------------
    def get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.enabled:
            return None

        try:
            response = openai.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding

        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc, exc_info=True)
            return None


# =====================================================================
# AUDIO UTILITIES 
# =====================================================================

def transcribe_audio(
    openai_client,
    audio_path: str,
    model: str = "whisper-1",
    show_debug: bool = False,
):
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text",
            )

        if show_debug:
            logger.info(f"Transcription result: {transcript}")

        return transcript

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return "Error: Could not transcribe audio"


def synthesize_speech(
    polly_client,
    text,
    voice_id="Ruth",
    engine="neural",
    output_format="mp3",
    text_type="text",
):
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            VoiceId=voice_id,
            Engine=engine,
            OutputFormat=output_format,
            TextType=text_type,
        )
        return response["AudioStream"].read()

    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return None


def save_audio_file(audio_data, file_path):
    if audio_data:
        if not file_path.endswith((".mp3", ".wav", ".ogg")):
            logger.warning("Invalid file extension")
            return None
        try:
            with open(file_path, "wb") as file:
                file.write(audio_data)
            logger.info(f"Audio saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return False
    return False


def synthesize_speech_openai(
    openai_client,
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
):
    try:
        response = openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
        )
        return response.content

    except Exception as e:
        logger.error(f"Error synthesizing speech with OpenAI: {e}")
        return None