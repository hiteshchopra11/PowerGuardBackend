"""Health and admin API controller."""

import os
import logging
from fastapi import APIRouter, HTTPException

from app.core.database import engine, Base

logger = logging.getLogger('powerguard_health_controller')

health_router = APIRouter(prefix="/api", tags=["Database"])


@health_router.post("/reset-db")
async def reset_database():
    """
    Reset the database by removing the existing file and recreating tables.
    
    ⚠️ WARNING: This endpoint will delete all existing data in the database.
    Use with caution in production environments.
    
    Returns:
    * Success message if database is reset successfully
    * Error message with details if reset fails
    
    Response Example:
    ```json
    {
        "status": "success",
        "message": "Database reset successfully completed"
    }
    ```
    """
    try:
        logger.info("[HealthController] Resetting database")
        
        # Get the database path from the engine URL
        db_path = "power_guard.db"
        
        # Close any existing connections
        engine.dispose()
        
        # Remove the existing database file if it exists
        if os.path.exists(db_path):
            logger.info(f"Removing existing database: {db_path}")
            os.remove(db_path)
        
        # Create new database and tables
        logger.info("Creating new database and tables...")
        Base.metadata.create_all(bind=engine)
        
        # Set correct permissions (readable and writable)
        os.chmod(db_path, 0o666)
        
        logger.info("Database reset complete!")
        return {"status": "success", "message": "Database reset successfully completed"}
        
    except Exception as e:
        logger.error(f"[HealthController] Error resetting database: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset database: {str(e)}"
        )