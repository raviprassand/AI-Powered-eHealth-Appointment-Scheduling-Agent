
import os
import logging
from dotenv import load_dotenv
base_dir = os.path.dirname(os.path.abspath(__file__))  # /app
project_root = os.path.dirname(base_dir)  # go up one level → project folder
env_path = os.path.join(project_root, ".env")

print("📂 Running file:", __file__)
print("📂 Current working directory:", os.getcwd())
print("📁 Trying to load .env from:", env_path)

loaded = load_dotenv(dotenv_path=env_path, override=True)
print("✅ load_dotenv() returned:", loaded)

if os.path.exists(env_path):
    print("📄 .env file found!")
else:
    print("❌ .env file NOT found!")

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print("🔑 OPENAI_API_KEY (first 25 chars):", api_key[:25])
else:
    print("🚨 OPENAI_API_KEY is missing or not loaded!")


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import db_manager
from app.routers import chat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Application starting up...")
    
    # Initialize and test database connection
    try:
        if db_manager.test_connection():
            logger.info("✅ Database connection pool ready")
            pool_status = db_manager.get_pool_status()
            logger.info(f"📊 Pool status: {pool_status}")
        else:
            logger.error("❌ Database connection failed - check credentials")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
    
    logger.info(f"🌐 Port: {os.environ.get('PORT', '8080')}")
    
    yield
    
    # Shutdown
    logger.info("🔄 Application shutting down...")
    db_manager.close_connections()
    logger.info("✅ Application shutdown complete")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- temporarily allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {
        "message": "Health Informatics API with OpenAI + Connection Pooling", 
        "status": "healthy",
        "database": "pooled"
    }

@app.get("/health")
def health_check():
    """Enhanced health check endpoint"""
    db_healthy = db_manager.test_connection()
    pool_status = db_manager.get_pool_status()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "pool_status": pool_status,
        "ai_provider": "openai",
        "platform": "optimized-local"
    }

@app.get("/debug/pool")
def pool_debug():
    """Debug endpoint to check pool status"""
    return {
        "pool_status": db_manager.get_pool_status(),
        "connection_test": db_manager.test_connection()
    }

# For Cloud Run
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)