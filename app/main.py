from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import os
from app.database import Base, engine
from datetime import datetime
from app.rate_limit import setup_rate_limiting

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
    description="""
    PowerGuard AI Backend is a battery optimization service that uses AI to analyze device usage patterns
    and provide actionable recommendations for better battery life.
    
    ## Features
    * Device usage analysis
    * Battery optimization recommendations
    * Usage pattern tracking
    * Historical data analysis
    
    ## API Endpoints
    * `/api/analyze` - Analyze device data and get optimization recommendations
    * `/api/patterns/{device_id}` - Get usage patterns for a specific device
    * `/api/reset-db` - Reset the database (use with caution)
    * `/api/all-entries` - Get all database entries
    
    ## Rate Limits
    * Default: 100 requests per minute
    * Analyze endpoint: 30 requests per minute
    * Patterns endpoint: 60 requests per minute
    * Reset DB endpoint: 5 requests per hour
    """,
    version="1.0.0"
)

# Setup rate limiting
setup_rate_limiting(app)

@app.post("/api/reset-db")
async def reset_database():
    """
    Reset the database by removing the existing file and recreating tables.
    
    ⚠️ WARNING: This endpoint will delete all existing data in the database.
    Use with caution in production environments.
    
    Returns:
    * Success message if database is reset successfully
    * Error message with details if reset fails
    """
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
    """
    Analyze device data and return optimization recommendations.
    
    This endpoint processes device usage data through an AI model to generate:
    * Actionable recommendations for battery and data optimization
    * Insights about device usage patterns
    * Battery, data, and performance scores
    * Estimated resource savings
    
    The response includes:
    * List of specific actions to take
    * Insights discovered during analysis
    * Scores measuring efficiency and health
    * Estimated savings in battery life and data usage
    """
    try:
        logger.info(f"[PowerGuard] Received request for device: {data.deviceId}")
        logger.debug(f"[PowerGuard] Request data: {data.model_dump_json(indent=2)}")
        
        # Process data through LLM
        response = analyze_device_data(data.model_dump(), db)
        logger.debug(f"[PowerGuard] LLM response: {response}")
        
        # Store usage patterns in DB if present
        if response and response.get('insights'):
            logger.info(f"[PowerGuard] Storing insights as usage patterns")
            for insight in response['insights']:
                if 'packageName' in insight.get('parameters', {}):
                    package_name = insight['parameters']['packageName']
                    pattern_text = f"{insight['title']}: {insight['description']}"
                    
                    # Check if pattern already exists
                    existing_pattern = db.query(UsagePattern).filter(
                        UsagePattern.deviceId == data.deviceId,
                        UsagePattern.packageName == package_name
                    ).first()
                    
                    if existing_pattern:
                        # Update existing pattern
                        existing_pattern.pattern = pattern_text
                        existing_pattern.timestamp = int(data.timestamp)
                        logger.debug(f"Updated pattern for device {data.deviceId}, package {package_name}")
                    else:
                        # Create new pattern
                        db_pattern = UsagePattern(
                            deviceId=data.deviceId,
                            packageName=package_name,
                            pattern=pattern_text,
                            timestamp=int(data.timestamp)
                        )
                        db.add(db_pattern)
                        logger.debug(f"Created new pattern for device {data.deviceId}, package {package_name}")
            
            db.commit()
            logger.info("[PowerGuard] Successfully stored usage patterns")
            
        return response
    except Exception as e:
        logger.error(f"[PowerGuard] Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing device data: {str(e)}")

@app.get("/api/patterns/{device_id}", response_model=dict)
async def get_patterns(device_id: str, db: Session = Depends(get_db)):
    """
    Get stored usage patterns for a specific device.
    
    Parameters:
    * device_id: Unique identifier of the device
    
    Returns:
    * Dictionary of package names and their corresponding usage patterns
    """
    logger.info(f"[PowerGuard] Fetching patterns for device: {device_id}")
    patterns = db.query(UsagePattern).filter(UsagePattern.deviceId == device_id).all()
    
    result = {}
    for pattern in patterns:
        result[pattern.packageName] = pattern.pattern
        
    logger.debug(f"[PowerGuard] Found {len(result)} patterns")
    return result

@app.get("/api/all-entries", response_model=List[Dict])
async def get_all_entries(db: Session = Depends(get_db)):
    """
    Fetch all entries from the database.
    
    Returns a list of all usage patterns with their details including:
    * Device ID
    * Package name
    * Usage pattern
    * Timestamp (in human-readable format)
    """
    try:
        entries = db.query(UsagePattern).all()
        result = []
        for entry in entries:
            result.append({
                "id": entry.id,
                "device_id": entry.device_id,
                "package_name": entry.package_name,
                "pattern": entry.pattern,
                "timestamp": datetime.fromtimestamp(entry.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                "raw_timestamp": entry.timestamp
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching database entries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch database entries: {str(e)}"
        )

@app.get("/")
async def root():
    """
    Root endpoint to check if the service is running.
    
    Returns:
    * Simple message indicating the service is operational
    """
    return {"message": "PowerGuard AI Backend is running"} 