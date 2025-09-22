from langchain_community.utilities.sql_database import SQLDatabase
from app.core.config import settings
import time
from typing import Optional
import logging
import pymysql

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Singleton database manager with connection pooling"""
    _instance: Optional['DatabaseManager'] = None
    _db: Optional[SQLDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._db is None:
            self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection"""
        connection_start = time.time()
        logger.info("🔄 Initializing database connection...")
        
        # Create connection string
        mysql_uri = f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        
        # Create LangChain SQLDatabase instance (it will handle connection internally)
        self._db = SQLDatabase.from_uri(mysql_uri)
        
        connection_duration = time.time() - connection_start
        logger.info(f"✅ Database connection initialized in {connection_duration*1000:.0f}ms")
    
    def get_database(self) -> SQLDatabase:
        """Get the database instance"""
        if self._db is None:
            self._initialize_connection()
        return self._db
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            # Use LangChain's built-in method to test connection
            result = self._db.run("SELECT 1 as test")
            logger.info(f"✅ Database test query result: {result}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def get_pool_status(self) -> dict:
        """Get connection status"""
        try:
            if self._db:
                return {
                    "status": "connected",
                    "dialect": str(self._db.dialect),
                    "database": settings.DATABASE_NAME
                }
            return {"status": "not_initialized"}
        except Exception as e:
            logger.error(f"❌ Error getting connection status: {e}")
            return {"status": "error", "error": str(e)}
    
    def close_connections(self):
        """Close database connections"""
        if self._db:
            # LangChain SQLDatabase doesn't have explicit close method
            # It will be garbage collected
            self._db = None
            logger.info("🔐 Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()