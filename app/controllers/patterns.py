"""Usage patterns API controller."""

import logging
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.pattern_service import PatternService
from app.schemas.response import UsagePatternsResponseSchema, DatabaseEntrySchema
from app.core.exceptions import DatabaseException

logger = logging.getLogger('powerguard_patterns_controller')

patterns_router = APIRouter(prefix="/api", tags=["Patterns"])


@patterns_router.get("/patterns/{device_id}", response_model=UsagePatternsResponseSchema)
async def get_patterns(device_id: str, db: Session = Depends(get_db)):
    """
    Get stored usage patterns for a specific device.
    
    Parameters:
    * device_id: Unique identifier of the device
    
    Returns:
    * Dictionary of package names and their corresponding usage patterns
    
    Response Example:
    ```json
    {
        "patterns": {
            "com.example.app1": "High battery usage during background operation",
            "com.example.app2": "Excessive network data usage during foreground"
        }
    }
    ```
    """
    try:
        logger.info(f"[PatternsController] Fetching patterns for device: {device_id}")
        
        pattern_service = PatternService(db)
        patterns = pattern_service.get_patterns_for_device(device_id)
        
        logger.debug(f"[PatternsController] Found {len(patterns)} patterns")
        return UsagePatternsResponseSchema(patterns=patterns)
        
    except DatabaseException as e:
        logger.error(f"[PatternsController] Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"[PatternsController] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred")


@patterns_router.get("/all-entries", response_model=List[DatabaseEntrySchema])
async def get_all_entries(db: Session = Depends(get_db)):
    """
    Fetch all entries from the database.
    
    Returns a list of all usage patterns with their details including:
    * Device ID
    * Package name
    * Usage pattern
    * Timestamp (in human-readable format)
    
    Response Example:
    ```json
    [
        {
            "id": 1,
            "device_id": "example-device-001",
            "package_name": "com.example.app",
            "pattern": "High battery usage during background operation",
            "timestamp": "2023-06-08 12:34:56",
            "raw_timestamp": 1686123456
        }
    ]
    ```
    """
    try:
        logger.info("[PatternsController] Fetching all database entries")
        
        pattern_service = PatternService(db)
        entries = pattern_service.get_all_entries()
        
        logger.debug(f"[PatternsController] Found {len(entries)} entries")
        return entries
        
    except DatabaseException as e:
        logger.error(f"[PatternsController] Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"[PatternsController] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred")