from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import os
from app.database import Base, engine
from datetime import datetime

from app.models import DeviceData, ActionResponse
from app.llm_service import analyze_device_data
from app.database import get_db, UsagePattern

# Define allowed actionable types
ALLOWED_ACTIONABLE_TYPES = {
    "SET_STANDBY_BUCKET",
    "RESTRICT_BACKGROUND_DATA",
    "KILL_APP", 
    "MANAGE_WAKE_LOCKS",
    "THROTTLE_CPU_USAGE"
}

# Mapping of actionable types to their descriptions
ACTIONABLE_TYPE_DESCRIPTIONS = {
    1: "SET_STANDBY_BUCKET",
    2: "RESTRICT_BACKGROUND_DATA",
    3: "KILL_APP", 
    4: "MANAGE_WAKE_LOCKS",
    5: "THROTTLE_CPU_USAGE"
}

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_api')

app = FastAPI(
    title="PowerGuard AI Backend",
    description="""
    PowerGuard AI Backend is an advanced battery and data optimization service that uses AI to analyze device usage patterns
    and provide actionable recommendations for better resource management.
    
    ## Features
    * Advanced AI-powered query processing with 6 category types
    * Battery and data optimization recommendations
    * Smart resource type detection (BATTERY/DATA/OTHER)
    * Information, predictive, optimization, monitoring, and pattern analysis queries
    * Usage pattern tracking and historical analysis
    * Exclusion handling for critical apps
    * User-directed optimizations via natural language prompts
    * Android app-compatible prompt system
    * Hybrid rule-based and LLM prompt classification
    
    ## API Endpoints
    * `/api/analyze` - Analyze device data and get optimization recommendations
    * `/api/patterns/{device_id}` - Get usage patterns for a specific device
    * `/api/reset-db` - Reset the database (use with caution)
    * `/api/all-entries` - Get all database entries
    * `/api/test/with-prompt/{prompt}` - Test endpoint with prompt
    * `/api/test/no-prompt` - Test endpoint without prompt
    
    ## Error Handling
    The API uses standard HTTP status codes:
    * 200: Success
    * 400: Bad Request
    * 500: Internal Server Error
    
    ## Authentication
    Currently, the API does not require authentication.
    
    ## Response Format
    All responses are in JSON format and include:
    * Success/failure status
    * Timestamp
    * Message
    * Data (if applicable)
    """,
    version="1.0.0",
    contact={
        "name": "PowerGuard Team",
        "url": "https://powerguardbackend.onrender.com",
        "email": "support@powerguard.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Analysis",
            "description": "Endpoints for device data analysis and optimization"
        },
        {
            "name": "Patterns",
            "description": "Endpoints for retrieving usage patterns"
        },
        {
            "name": "Database",
            "description": "Endpoints for database management"
        }
    ]
)

@app.post("/api/reset-db", tags=["Database"])
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

@app.post("/api/analyze", response_model=ActionResponse, tags=["Analysis"])
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
            "temperature": 35.0
        },
        "memory": {
            "total": 8000000000,
            "used": 4000000000,
            "free": 4000000000
        },
        "cpu": {
            "usage": 45.0,
            "temperature": 45.0
        },
        "network": {
            "dataUsed": 100.5,
            "wifiEnabled": True,
            "mobileDataEnabled": False
        },
        "apps": [
            {
                "packageName": "com.example.app",
                "batteryUsage": 15.0,
                "dataUsage": 5.0,
                "foregroundTime": 3600
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
    
    ## New AI Prompt System Features:
    This endpoint now uses a sophisticated 2-step analysis process similar to the Android app:
    
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
    
    Response Example:
    ```json
    {
        "id": "gen_1686123456",
        "success": true,
        "timestamp": 1686123456.789,
        "message": "Analysis completed successfully",
        "actionable": [
            {
                "id": "bat-1",
                "type": "OPTIMIZE_BATTERY",
                "packageName": "com.example.heavybattery",
                "description": "Optimize battery usage for Heavy Battery App",
                "reason": "App is consuming excessive battery",
                "newMode": "optimized",
                "parameters": {}
            }
        ],
        "insights": [
            {
                "type": "BatteryDrain",
                "title": "Battery Drain Detected",
                "description": "Heavy Battery App is using significant battery resources",
                "severity": "high"
            }
        ],
        "batteryScore": 75.0,
        "dataScore": 85.0,
        "performanceScore": 80.0,
        "estimatedSavings": {
            "batteryMinutes": 120.0,
            "dataMB": 50.0
        }
    }
    ```
    """
    try:
        logger.info(f"[PowerGuard] Received request for device: {data.deviceId}")
        logger.debug(f"[PowerGuard] Request data: {data.model_dump_json(indent=2)}")
        
        # Process data through LLM
        try:
            response = analyze_device_data(data.model_dump(), db)
            logger.debug(f"[PowerGuard] LLM response: {response}")
            
            # Validate response structure
            if not isinstance(response, dict):
                logger.error("[PowerGuard] LLM response is not a dictionary")
                raise ValueError("LLM response is not a dictionary")
            
            # Ensure all required fields are present with default values
            required_fields = {
                "actionable": [],
                "insights": [],
                "batteryScore": 50,
                "dataScore": 50,
                "performanceScore": 50,
                "estimatedSavings": {"batteryMinutes": 0, "dataMB": 0},
                "id": f"gen_{int(datetime.now().timestamp())}",
                "success": True,
                "timestamp": int(datetime.now().timestamp()),
                "message": "Analysis completed successfully",
                "responseType": "BATTERY_OPTIMIZATION"
            }
            
            # Set default values for missing fields
            for field, default_value in required_fields.items():
                if field not in response:
                    logger.warning(f"[PowerGuard] Missing required field '{field}', setting to default value")
                    response[field] = default_value
            
            # Validate actionable items
            if not isinstance(response["actionable"], list):
                logger.warning("[PowerGuard] Actionable items is not a list, setting to empty list")
                response["actionable"] = []
            else:
                valid_actionable = []
                for item in response["actionable"]:
                    if not isinstance(item, dict):
                        logger.warning(f"[PowerGuard] Skipping invalid actionable item (not a dictionary): {item}")
                        continue
                    if "type" not in item:
                        logger.warning(f"[PowerGuard] Skipping actionable item without type: {item}")
                        continue
                    
                    # Convert type to string if it's an integer
                    if isinstance(item["type"], int):
                        type_mapping = {
                            1: "SET_STANDBY_BUCKET",
                            2: "RESTRICT_BACKGROUND_DATA",
                            3: "KILL_APP",
                            4: "MANAGE_WAKE_LOCKS",
                            5: "THROTTLE_CPU_USAGE"
                        }
                        if item["type"] in type_mapping:
                            item["type"] = type_mapping[item["type"]]
                        else:
                            item["type"] = "SET_STANDBY_BUCKET"  # Default
                        
                    # Check if type is in allowed types
                    if item["type"] not in ALLOWED_ACTIONABLE_TYPES:
                        logger.warning(f"[PowerGuard] Converting unknown actionable type {item['type']} to SET_STANDBY_BUCKET")
                        item["type"] = "SET_STANDBY_BUCKET"
                    
                    # Ensure required fields exist with sensible defaults
                    if "parameters" not in item or not isinstance(item.get("parameters"), dict):
                        item["parameters"] = {}
                    if "description" not in item:
                        item["description"] = ""
                    if "reason" not in item:
                        item["reason"] = ""
                    
                    # Handle field name changes from packageName to package_name
                    if "packageName" in item:
                        item["package_name"] = item.pop("packageName")
                    
                    # Set default values for new required fields
                    if "estimated_battery_savings" not in item:
                        item["estimated_battery_savings"] = 10.0  # Default battery savings
                    if "estimated_data_savings" not in item:
                        item["estimated_data_savings"] = 5.0   # Default data savings
                    if "severity" not in item:
                        item["severity"] = 2  # Default severity (1-5 scale)
                    if "enabled" not in item:
                        item["enabled"] = True
                    if "throttle_level" not in item:
                        item["throttle_level"] = None
                    
                    # Default new_mode based on actionable type if missing
                    if "new_mode" not in item and "newMode" not in item:
                        default_modes_by_type = {
                            "RESTRICT_BACKGROUND_DATA": "restricted",
                            "SET_STANDBY_BUCKET": "restricted",
                            "KILL_APP": "terminated",
                            "MANAGE_WAKE_LOCKS": "restricted",
                            "THROTTLE_CPU_USAGE": "throttled",
                        }
                        item["new_mode"] = default_modes_by_type.get(item["type"], "restricted")
                    elif "newMode" in item:
                        # Convert newMode to new_mode for consistency
                        item["new_mode"] = item.pop("newMode")
                    
                    valid_actionable.append(item)
                response["actionable"] = valid_actionable
            
            # Validate insights
            if not isinstance(response["insights"], list):
                logger.warning("[PowerGuard] Insights is not a list, setting to empty list")
                response["insights"] = []
            else:
                valid_insights = []
                for item in response["insights"]:
                    if not isinstance(item, dict):
                        logger.warning(f"[PowerGuard] Skipping invalid insight (not a dictionary): {item}")
                        continue
                    if not all(k in item for k in ["type", "title", "description", "severity"]):
                        logger.warning(f"[PowerGuard] Skipping insight with missing fields: {item}")
                        continue
                    valid_insights.append(item)
                response["insights"] = valid_insights
            
            # Validate scores
            for score_field in ["batteryScore", "dataScore", "performanceScore"]:
                try:
                    score = float(response[score_field])
                    if score < 0 or score > 100:
                        logger.warning(f"[PowerGuard] Invalid {score_field} value {score}, clamping to range [0, 100]")
                        response[score_field] = max(0, min(100, score))
                except (ValueError, TypeError):
                    logger.warning(f"[PowerGuard] Invalid {score_field} value {response[score_field]}, setting to default value 50")
                    response[score_field] = 50
            
            # Validate estimated savings
            if not isinstance(response["estimatedSavings"], dict):
                logger.warning("[PowerGuard] estimatedSavings is not a dictionary, setting to default values")
                response["estimatedSavings"] = {"batteryMinutes": 0, "dataMB": 0}
            else:
                savings = response["estimatedSavings"]
                for field in ["batteryMinutes", "dataMB"]:
                    try:
                        savings[field] = float(savings.get(field, 0))
                        if savings[field] < 0:
                            logger.warning(f"[PowerGuard] Negative {field} value {savings[field]}, setting to 0")
                            savings[field] = 0
                    except (ValueError, TypeError):
                        logger.warning(f"[PowerGuard] Invalid {field} value {savings.get(field)}, setting to 0")
                        savings[field] = 0
            
            logger.info("[PowerGuard] Successfully validated and processed LLM response")
            
        except Exception as e:
            logger.error(f"[PowerGuard] Error processing LLM response: {str(e)}", exc_info=True)
            # Check for rate limit error
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
            # Return a valid response with default values
            response = {
                "id": "error_" + str(int(datetime.now().timestamp())),
                "success": False,
                "timestamp": int(datetime.now().timestamp()),
                "message": f"Error processing LLM response: {str(e)}",
                "actionable": [],
                "insights": [],
                "batteryScore": 50,
                "dataScore": 50,
                "performanceScore": 50,
                "estimatedSavings": {
                    "batteryMinutes": 0,
                    "dataMB": 0
                }
            }
        
        # Store usage patterns in DB if present
        if response and response.get('insights'):
            logger.info(f"[PowerGuard] Storing insights as usage patterns")
            try:
                for insight in response['insights']:
                    # Check both packageName and package_name for compatibility
                    package_name = None
                    if 'packageName' in insight.get('parameters', {}):
                        package_name = insight['parameters']['packageName']
                    elif 'package_name' in insight.get('parameters', {}):
                        package_name = insight['parameters']['package_name']
                    
                    if package_name:
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
            except Exception as e:
                logger.error(f"[PowerGuard] Error storing usage patterns: {str(e)}", exc_info=True)
                # Continue with the response even if storing patterns fails
        
        return response
        
    except Exception as e:
        logger.error(f"[PowerGuard] Error processing request: {str(e)}", exc_info=True)
        # Return a valid response with default values
        return {
            "id": "error_" + str(int(datetime.now().timestamp())),
            "success": False,
            "timestamp": int(datetime.now().timestamp()),
            "message": f"Error processing device data: {str(e)}",
            "responseType": "ERROR",
            "actionable": [],
            "insights": [],
            "batteryScore": 50,
            "dataScore": 50,
            "performanceScore": 50,
            "estimatedSavings": {
                "batteryMinutes": 0,
                "dataMB": 0
            }
        }

@app.get("/api/patterns/{device_id}", response_model=dict, tags=["Patterns"])
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
        "com.example.app1": "High battery usage during background operation",
        "com.example.app2": "Excessive network data usage during foreground"
    }
    ```
    """
    logger.info(f"[PowerGuard] Fetching patterns for device: {device_id}")
    patterns = db.query(UsagePattern).filter(UsagePattern.deviceId == device_id).all()
    
    result = {}
    for pattern in patterns:
        result[pattern.packageName] = pattern.pattern
        
    logger.debug(f"[PowerGuard] Found {len(result)} patterns")
    return result

@app.get("/api/all-entries", response_model=List[Dict], tags=["Database"])
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
        entries = db.query(UsagePattern).all()
        result = []
        for entry in entries:
            result.append({
                "id": entry.id,
                "device_id": entry.deviceId,
                "package_name": entry.packageName,
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

# Testing-only routes have been removed for production readiness.