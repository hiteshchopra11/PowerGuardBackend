"""Analysis API controller."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analysis_service import AnalysisService
from app.schemas.device_data import DeviceData
from app.schemas.response import ActionResponseSchema
from app.core.exceptions import AnalysisException, RateLimitException, ValidationException

logger = logging.getLogger('powerguard_analysis_controller')

analysis_router = APIRouter(prefix="/api", tags=["Analysis"])


@analysis_router.post("/analyze", response_model=ActionResponseSchema)
async def analyze_data(
    data: DeviceData = Body(..., description="""
    Device usage data to analyze, with an optional 'prompt' field for user-directed optimizations.
    
    Example:
    ```json
    {
        "deviceId": "example-device-001",
        "timestamp": 1686123456,
        "battery": {
            "level": 45.0,
            "health": 95.0,
            "temperature": 35.0,
            "isCharging": false,
            "chargingType": "none",
            "voltage": 3.7,
            "capacity": 3000.0,
            "currentNow": 500.0
        },
        "memory": {
            "totalRam": 8000000000,
            "availableRam": 4000000000,
            "lowMemory": false,
            "threshold": 1000000000
        },
        "cpu": {
            "usage": 45.0,
            "temperature": 45.0,
            "frequencies": [1800, 2400]
        },
        "network": {
            "type": "wifi",
            "strength": 85.0,
            "isRoaming": false,
            "dataUsage": {
                "foreground": 100.0,
                "background": 50.0,
                "rxBytes": 1000000,
                "txBytes": 500000
            },
            "activeConnectionInfo": "WiFi connected",
            "linkSpeed": 866.0,
            "cellularGeneration": "4G"
        },
        "apps": [
            {
                "packageName": "com.example.app",
                "processName": "com.example.app",
                "appName": "Example App",
                "isSystemApp": false,
                "lastUsed": 1686123456,
                "foregroundTime": 3600,
                "backgroundTime": 1800,
                "batteryUsage": 15.0,
                "dataUsage": {
                    "foreground": 10.0,
                    "background": 5.0,
                    "rxBytes": 100000,
                    "txBytes": 50000
                },
                "memoryUsage": 128.0,
                "cpuUsage": 5.0,
                "notifications": 3,
                "crashes": 0,
                "versionName": "1.0.0",
                "versionCode": 1,
                "targetSdkVersion": 30,
                "installTime": 1686000000,
                "updatedTime": 1686100000,
                "alarmWakeups": 2,
                "currentPriority": "NORMAL",
                "bucket": "ACTIVE"
            }
        ],
        "prompt": "Optimize my battery life"
    }
    ```
    """),
    db: Session = Depends(get_db)
):
    """
    Analyze device data using advanced AI prompt system and return optimization recommendations.
    
    ## AI Prompt System Features:
    This endpoint uses a sophisticated 2-step analysis process:
    
    **Step 1: Resource Type Detection**
    - Automatically detects if your query is about BATTERY, DATA, or OTHER resources
    
    **Step 2: Query Categorization**
    - Category 1: Information Queries ("Which apps use most battery?")
    - Category 2: Predictive Queries ("Can I watch Netflix with current battery?")
    - Category 3: Optimization Requests ("Save my battery for 3 hours")
    - Category 4: Monitoring Triggers ("Notify when battery drops below 15%")
    - Category 5: Pattern Analysis ("Optimize based on my usage patterns")
    - Category 6: Invalid/Unrelated Queries
    
    ## Smart Features:
    * **App Exclusion Handling**: "Optimize data but keep WhatsApp running"
    * **Time Constraints**: "Save battery for the next 3 hours"
    * **Number Specifications**: "Show me top 5 battery-consuming apps"
    * **Critical App Protection**: Automatically protects messaging, navigation, email apps
    
    ## Response Types:
    * **Information Responses**: Insights only, no actionables
    * **Optimization Responses**: Both actionables and insights
    * **Predictive Responses**: Yes/no answers with explanations
    
    ## Prompt Examples:
    - "Which apps use the most battery?" (Information)
    - "Can I stream video for 2 hours?" (Predictive) 
    - "Optimize my data usage but keep Gmail working" (Optimization with exclusion)
    - "Notify me when battery hits 20%" (Monitoring)
    - "Optimize based on my typical evening usage" (Pattern Analysis)
    """
    try:
        logger.info(f"[AnalysisController] Received request for device: {data.deviceId}")
        
        # Create analysis service and process request
        analysis_service = AnalysisService(db)
        result = analysis_service.analyze_device_data(data.model_dump())
        
        logger.info(f"[AnalysisController] Analysis completed successfully for device: {data.deviceId}")
        return result
        
    except RateLimitException as e:
        logger.error(f"[AnalysisController] Rate limit exceeded: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    
    except ValidationException as e:
        logger.error(f"[AnalysisController] Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except AnalysisException as e:
        logger.error(f"[AnalysisController] Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"[AnalysisController] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred")