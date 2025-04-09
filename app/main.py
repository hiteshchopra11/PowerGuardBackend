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

# Define allowed actionable types
ALLOWED_ACTIONABLE_TYPES = {
    "OPTIMIZE_BATTERY",
    "ENABLE_DATA_SAVER",
    "RESTRICT_BACKGROUND",
    "ADJUST_SCREEN",
    "MANAGE_LOCATION",
    "UPDATE_APP",
    "UNINSTALL_APP",
    "CLEAR_CACHE",
    "ENABLE_BATTERY_SAVER",
    "ENABLE_AIRPLANE_MODE",
    "DISABLE_FEATURES",
    "SCHEDULE_TASKS"
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
    PowerGuard AI Backend is a battery optimization service that uses AI to analyze device usage patterns
    and provide actionable recommendations for better battery life.
    
    ## Features
    * Device usage analysis
    * Battery optimization recommendations
    * Usage pattern tracking
    * Historical data analysis
    * AI-powered insights
    * Rate limiting and DDoS protection
    * User-directed optimizations via prompts
    * Hybrid rule-based and LLM prompt classification
    
    ## API Endpoints
    * `/api/analyze` - Analyze device data and get optimization recommendations
    * `/api/patterns/{device_id}` - Get usage patterns for a specific device
    * `/api/reset-db` - Reset the database (use with caution)
    * `/api/all-entries` - Get all database entries
    * `/api/test/with-prompt/{prompt}` - Test endpoint with prompt
    * `/api/test/no-prompt` - Test endpoint without prompt
    
    ## Rate Limits
    * Default endpoints: 1000 requests per minute
    * Analyze endpoint: 500 requests per minute
    * Patterns endpoint: 1000 requests per minute
    * Reset DB endpoint: 100 requests per hour
    
    ## Error Handling
    The API uses standard HTTP status codes:
    * 200: Success
    * 400: Bad Request
    * 429: Too Many Requests
    * 500: Internal Server Error
    
    ## Authentication
    Currently, the API does not require authentication. Rate limiting is implemented
    based on IP address to prevent abuse.
    
    ## Response Format
    All responses are in JSON format and include:
    * Success/failure status
    * Timestamp
    * Message
    * Data (if applicable)
    
    ## Example Usage
    ```python
    import requests
    
    # Analyze device data
    response = requests.post(
        "https://powerguardbackend.onrender.com/api/analyze",
        json={
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
    )
    ```
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
        },
        {
            "name": "Testing",
            "description": "Test endpoints for development and testing"
        }
    ]
)

# Setup rate limiting
setup_rate_limiting(app)

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
    
    Optional 'prompt' field:
    * Allows users to specify optimization goals (e.g., "save battery life", "reduce data usage")
    * Customizes the analysis to focus on the user's specific needs
    * Examples: "Optimize battery life", "Reduce network data usage", "I'm low on battery"
    
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
                "message": "Analysis completed successfully"
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
                    if item["type"] not in ALLOWED_ACTIONABLE_TYPES:
                        logger.warning(f"[PowerGuard] Converting unknown actionable type to OPTIMIZE_BATTERY: {item['type']}")
                        item["type"] = "OPTIMIZE_BATTERY"
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

@app.get("/", tags=["Testing"])
async def root():
    """
    Root endpoint to check if the service is running.
    
    Returns:
    * Simple message indicating the service is operational
    
    Response Example:
    ```json
    {
        "message": "PowerGuard AI Backend is running"
    }
    ```
    """
    return {"message": "PowerGuard AI Backend is running"}

@app.get("/api/test/with-prompt/{prompt}", tags=["Testing"])
async def test_with_prompt(prompt: str):
    """
    Test endpoint that returns a sample response based on the provided prompt.
    This endpoint does not call the LLM, it just returns a sample response.
    
    Parameters:
    * prompt: The user prompt to simulate
    
    Returns:
    * A sample ActionResponse based on the prompt
    
    Response Example:
    ```json
    {
        "id": "test_1686123456",
        "success": true,
        "timestamp": 1686123456.789,
        "message": "Test response generated successfully",
        "actionable": [
            {
                "id": "test-1",
                "type": "OPTIMIZE_BATTERY",
                "packageName": "com.example.app",
                "description": "Test battery optimization",
                "reason": "Test reason",
                "newMode": "optimized",
                "parameters": {}
            }
        ],
        "insights": [
            {
                "type": "TestInsight",
                "title": "Test Insight",
                "description": "This is a test insight",
                "severity": "medium"
            }
        ],
        "batteryScore": 80.0,
        "dataScore": 70.0,
        "performanceScore": 75.0,
        "estimatedSavings": {
            "batteryMinutes": 60.0,
            "dataMB": 30.0
        }
    }
    ```
    """
    logger.info(f"[PowerGuard] Test endpoint called with prompt: '{prompt}'")
    
    # Generate a sample response based on the prompt
    response = ActionResponse.example_response(prompt)
    
    logger.info(f"[PowerGuard] Generated sample response with {len(response.actionable)} actionable items and {len(response.insights)} insights")
    return response

@app.get("/api/test/no-prompt", tags=["Testing"])
async def test_no_prompt():
    """
    Test endpoint that returns a sample response without a prompt.
    This endpoint does not call the LLM, it just returns a sample response.
    
    Returns:
    * A sample ActionResponse without considering a prompt
    
    Response Example:
    ```json
    {
        "id": "test_1686123456",
        "success": true,
        "timestamp": 1686123456.789,
        "message": "Test response generated successfully",
        "actionable": [
            {
                "id": "test-1",
                "type": "OPTIMIZE_BATTERY",
                "packageName": "com.example.app",
                "description": "Test battery optimization",
                "reason": "Test reason",
                "newMode": "optimized",
                "parameters": {}
            }
        ],
        "insights": [
            {
                "type": "TestInsight",
                "title": "Test Insight",
                "description": "This is a test insight",
                "severity": "medium"
            }
        ],
        "batteryScore": 80.0,
        "dataScore": 70.0,
        "performanceScore": 75.0,
        "estimatedSavings": {
            "batteryMinutes": 60.0,
            "dataMB": 30.0
        }
    }
    ```
    """
    logger.info("[PowerGuard] Test endpoint called without prompt")
    
    # Generate a sample response without a prompt
    response = ActionResponse.example_response()
    
    logger.info(f"[PowerGuard] Generated sample response with {len(response.actionable)} actionable items and {len(response.insights)} insights")
    return response

@app.post("/api/debug/app-values", tags=["Testing"])
async def debug_app_values(data: DeviceData = Body(...)):
    """
    Debug endpoint to examine the battery usage values for all apps in the request.
    
    Returns:
        Dictionary with app names and their battery usage values
    """
    result = {
        "battery_values": []
    }
    
    try:
        # Process each app
        for app in data.apps:
            app_info = {
                "app_name": app.appName,
                "package_name": app.packageName,
                "battery_usage": app.batteryUsage,
                "battery_usage_type": str(type(app.batteryUsage))
            }
            result["battery_values"].append(app_info)
            
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing app values: {str(e)}"
        ) 