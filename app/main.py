# app/main.py

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import db_manager
from app.routers import chat


# =====================================================================
# Load environment
# =====================================================================

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(base_dir)
env_path = os.path.join(project_root, ".env")

load_dotenv(dotenv_path=env_path, override=True)


# =====================================================================
# Logging
# =====================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================================================================
# App lifecycle
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Application starting up...")

    # ---------------------------------------------------------
    # DB health check
    # ---------------------------------------------------------
    try:
        if db_manager.test_connection():
            logger.info("✅ Database API connection ready")
            logger.info(f"📊 DB Status: {db_manager.get_pool_status()}")
        else:
            logger.warning("⚠️ Database connection not verified")
    except Exception as exc:
        logger.error(f"❌ DB initialization error: {exc}")

    # ---------------------------------------------------------
    # LLM / RAG status logging
    # ---------------------------------------------------------
    logger.info(f"🤖 LLM Enabled: {settings.USE_LLM_INTENT}")
    logger.info(f"📚 RAG Enabled: {settings.USE_RAG}")
    logger.info(f"🔎 Vector Search Enabled: {settings.USE_VECTOR_SEARCH}")

    logger.info(f"🌐 Running on port: {os.environ.get('PORT', '8080')}")

    yield

    logger.info("🔄 Application shutting down...")
    db_manager.close_connections()
    logger.info("✅ Shutdown complete")


# =====================================================================
# FastAPI app
# =====================================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)


# =====================================================================
# CORS
# =====================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# Routes
# =====================================================================

app.include_router(chat.router, prefix=settings.API_V1_STR)


# =====================================================================
# Root endpoint
# =====================================================================

@app.get("/")
def root():
    return {
        "message": "AI-powered Health Informatics API",
        "status": "healthy",
        "features": {
            "llm_intent": settings.USE_LLM_INTENT,
            "rag": settings.USE_RAG,
            "vector_search": settings.USE_VECTOR_SEARCH,
        },
    }


# =====================================================================
# Health check
# =====================================================================

@app.get("/health")
def health_check():
    db_healthy = db_manager.test_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": db_manager.get_pool_status(),
        "llm_enabled": bool(settings.OPENAI_API_KEY),
        "rag_enabled": settings.USE_RAG,
    }


# =====================================================================
# Debug endpoints
# =====================================================================

@app.get("/debug/system")
def system_debug():
    return {
        "env_loaded": True,
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "use_llm_intent": settings.USE_LLM_INTENT,
        "use_rag": settings.USE_RAG,
        "use_vector": settings.USE_VECTOR_SEARCH,
    }


# =====================================================================
# Local run
# =====================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )