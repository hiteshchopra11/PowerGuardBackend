from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List

from app.models import DeviceData, ActionResponse
from app.llm_service import analyze_device_data
from app.database import get_db, UsagePattern

app = FastAPI(
    title="PowerGuard AI Backend",
    description="Backend service for PowerGuard with Groq LLM integration",
    version="1.0.0"
)

@app.post("/api/analyze", response_model=ActionResponse)
async def analyze_data(
    data: DeviceData = Body(..., description="Device usage data to analyze"),
    db: Session = Depends(get_db)
):
    """Analyze device data and return optimization recommendations"""
    try:
        # Process data through LLM
        response = analyze_device_data(data.model_dump())
        
        # Store usage patterns in DB
        if response and 'usage_patterns' in response:
            for package_name, pattern in response['usage_patterns'].items():
                db_pattern = UsagePattern(
                    device_id=data.device_id,
                    package_name=package_name,
                    pattern=pattern,
                    timestamp=data.timestamp
                )
                db.add(db_pattern)
            db.commit()
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing device data: {str(e)}")

@app.get("/api/patterns/{device_id}", response_model=dict)
async def get_patterns(device_id: str, db: Session = Depends(get_db)):
    """Get stored usage patterns for a device"""
    patterns = db.query(UsagePattern).filter(UsagePattern.device_id == device_id).all()
    
    result = {}
    for pattern in patterns:
        result[pattern.package_name] = pattern.pattern
        
    return result

@app.get("/")
async def root():
    return {"message": "PowerGuard AI Backend is running"} 