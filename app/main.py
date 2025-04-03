from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import logging
import os
from app.database import Base, engine

from app.models import DeviceData, ActionResponse
from app.llm_service import analyze_device_data
from app.database import get_db, UsagePattern

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_api')

app = FastAPI(
    title="PowerGuard AI Backend",
    description="Backend service for PowerGuard with Groq LLM integration",
    version="1.0.0"
)

@app.post("/api/reset-db")
async def reset_database():
    """Reset the database by removing the existing file and recreating tables"""
    try:
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
        logger.error(f"Error resetting database: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset database: {str(e)}"
        )

@app.post("/api/analyze", response_model=ActionResponse)
async def analyze_data(
    data: DeviceData = Body(..., description="Device usage data to analyze"),
    db: Session = Depends(get_db)
):
    """Analyze device data and return optimization recommendations"""
    try:
        logger.info(f"[PowerGuard] Received request for device: {data.device_id}")
        logger.debug(f"[PowerGuard] Request data: {data.model_dump_json(indent=2)}")
        
        # Process data through LLM
        response = analyze_device_data(data.model_dump(), db)
        logger.debug(f"[PowerGuard] LLM response: {response}")
        
        # Store usage patterns in DB
        if response and 'usage_patterns' in response:
            logger.info(f"[PowerGuard] Storing {len(response['usage_patterns'])} usage patterns")
            for package_name, pattern in response['usage_patterns'].items():
                # Check if pattern already exists
                existing_pattern = db.query(UsagePattern).filter(
                    UsagePattern.device_id == data.device_id,
                    UsagePattern.package_name == package_name
                ).first()
                
                if existing_pattern:
                    # Update existing pattern
                    existing_pattern.pattern = pattern
                    existing_pattern.timestamp = data.timestamp
                    logger.debug(f"Updated pattern for device {data.device_id}, package {package_name}")
                else:
                    # Create new pattern
                    db_pattern = UsagePattern(
                        device_id=data.device_id,
                        package_name=package_name,
                        pattern=pattern,
                        timestamp=data.timestamp
                    )
                    db.add(db_pattern)
                    logger.debug(f"Created new pattern for device {data.device_id}, package {package_name}")
            
            db.commit()
            logger.info("[PowerGuard] Successfully stored usage patterns")
            
        return response
    except Exception as e:
        logger.error(f"[PowerGuard] Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing device data: {str(e)}")

@app.get("/api/patterns/{device_id}", response_model=dict)
async def get_patterns(device_id: str, db: Session = Depends(get_db)):
    """Get stored usage patterns for a device"""
    logger.info(f"[PowerGuard] Fetching patterns for device: {device_id}")
    patterns = db.query(UsagePattern).filter(UsagePattern.device_id == device_id).all()
    
    result = {}
    for pattern in patterns:
        result[pattern.package_name] = pattern.pattern
        
    logger.debug(f"[PowerGuard] Found {len(result)} patterns")
    return result

@app.get("/")
async def root():
    return {"message": "PowerGuard AI Backend is running"} 