import os
from groq import Groq
from dotenv import load_dotenv
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import UsagePattern
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_llm')

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_historical_patterns(db: Session, device_id: str) -> Dict[str, str]:
    """Fetch historical usage patterns for a device from the database"""
    logger.debug(f"[PowerGuard] Fetching historical patterns for device: {device_id}")
    
    # Query patterns for this specific device only
    patterns = db.query(UsagePattern).filter(
        UsagePattern.deviceId == device_id
    ).order_by(UsagePattern.timestamp.desc()).all()
    
    # Group patterns by package name, taking the most recent pattern for each package
    result = {}
    for pattern in patterns:
        if pattern.packageName not in result:
            result[pattern.packageName] = pattern.pattern
    
    logger.debug(f"[PowerGuard] Found {len(result)} historical patterns for device {device_id}")
    return result

def analyze_device_data(device_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Process device data through Groq LLM and get optimization recommendations"""
    logger.info(f"[PowerGuard] Starting analysis for device: {device_data['deviceId']}")
    logger.debug(f"[PowerGuard] Received device data: {json.dumps(device_data, indent=2)}")
    
    # Get historical patterns for this device
    historical_patterns = get_historical_patterns(db, device_data['deviceId'])
    
    # Format historical patterns for the prompt
    historical_patterns_text = "Historical Usage Patterns:\n"
    if historical_patterns:
        for package_name, pattern in historical_patterns.items():
            historical_patterns_text += f"- {package_name}: {pattern}\n"
    else:
        historical_patterns_text += "No historical patterns found.\n"
    
    logger.debug(f"[PowerGuard] Formatted historical patterns: {historical_patterns_text}")
    
    # Convert device data to a more readable format for the prompt
    prompt = f"""
    As an AI battery optimization expert, analyze this Android device data:
    
    {historical_patterns_text}
    
    Current Device Data:
    Battery:
    - Level: {device_data['battery']['level']}%
    - Temperature: {device_data['battery']['temperature']}°C
    - Charging: {device_data['battery']['isCharging']}
    - Voltage: {device_data['battery']['voltage']}
    - Health: {device_data['battery']['health']}
    
    Memory:
    - Total RAM: {device_data['memory']['totalRam']} MB
    - Available RAM: {device_data['memory']['availableRam']} MB
    - Low Memory: {device_data['memory']['lowMemory']}
    
    CPU:
    - Usage: {device_data['cpu']['usage']}%
    - Temperature: {device_data['cpu']['temperature']}°C
    
    Network:
    - Type: {device_data['network']['type']}
    - Strength: {device_data['network']['strength']}
    - Roaming: {device_data['network']['isRoaming']}
    - Data Usage: {device_data['network']['dataUsage']['foreground'] + device_data['network']['dataUsage']['background']} MB
    - Cellular Generation: {device_data['network']['cellularGeneration']}
    
    App Data:
    {format_apps(device_data['apps'])}
    
    Based on this data, generate a comprehensive analysis with:
    
    1. actionable: A list of specific actions to take, including:
       - id: unique identifier for the action
       - type: the type of action (e.g., "KillBackground")
       - packageName: affected app's package name
       - description: what the action will do
       - reason: why this action is recommended
       - newMode: target state (e.g., "restricted")
       - parameters: additional context as key-value pairs
    
    2. insights: List of insights discovered about the device's behavior:
       - type: insight category (e.g., "BatteryDrain")
       - title: summary title
       - description: detailed explanation
       - severity: e.g., "low", "medium", "high"
    
    3. scores and estimates:
       - batteryScore: from 0-100 evaluating battery health
       - dataScore: from 0-100 evaluating data usage efficiency
       - performanceScore: from 0-100 evaluating overall performance
       - estimatedSavings: with batteryMinutes and dataMB values
    
    Return ONLY valid JSON with an id, success flag (true), timestamp, message, and the above fields.
    """
    
    logger.debug(f"[PowerGuard] Generated prompt for LLM: {prompt}")
    
    # Call Groq API
    try:
        logger.info("[PowerGuard] Calling Groq API for analysis")
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # or other Groq model
            messages=[
                {"role": "system", "content": "You are an AI battery and resource optimization expert that analyzes device data and provides actionable recommendations. Always respond with valid JSON only, no additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        logger.debug(f"[PowerGuard] Received response from Groq API: {completion.choices[0].message.content}")
        
        # Extract JSON from response
        response_text = completion.choices[0].message.content.strip()
        
        # Try to find JSON content between triple backticks if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            if json_end > json_start:
                response_text = response_text[json_start:json_end].strip()
        
        # Try to find JSON content between curly braces
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                response_data = json.loads(json_str)
                
                # Ensure timestamp is a number
                if 'timestamp' in response_data:
                    if isinstance(response_data['timestamp'], str):
                        try:
                            dt = datetime.fromisoformat(response_data['timestamp'].replace('Z', '+00:00'))
                            response_data['timestamp'] = int(dt.timestamp())
                        except ValueError:
                            response_data['timestamp'] = int(device_data['timestamp'])
                    elif not isinstance(response_data['timestamp'], (int, float)):
                        response_data['timestamp'] = int(device_data['timestamp'])
                else:
                    response_data['timestamp'] = int(device_data['timestamp'])
                
                # Ensure required fields are present
                if 'id' not in response_data:
                    response_data['id'] = f"analysis-{device_data['deviceId']}-{int(device_data['timestamp'])}"
                if 'success' not in response_data:
                    response_data['success'] = True
                if 'message' not in response_data:
                    response_data['message'] = "Analysis completed successfully."
                if 'actionable' not in response_data:
                    response_data['actionable'] = []
                if 'insights' not in response_data:
                    response_data['insights'] = []
                if 'batteryScore' not in response_data:
                    response_data['batteryScore'] = 50
                if 'dataScore' not in response_data:
                    response_data['dataScore'] = 50
                if 'performanceScore' not in response_data:
                    response_data['performanceScore'] = 50
                if 'estimatedSavings' not in response_data:
                    response_data['estimatedSavings'] = {"batteryMinutes": 0, "dataMB": 0}
                
                logger.info("[PowerGuard] Successfully processed LLM response")
                return response_data
            except json.JSONDecodeError as e:
                logger.error(f"[PowerGuard] JSON parsing error: {e}")
                logger.error(f"[PowerGuard] Problematic JSON string: {json_str}")
                raise
        else:
            logger.error("[PowerGuard] Failed to extract JSON from LLM response")
            logger.error(f"[PowerGuard] Full response: {response_text}")
            # Fallback with empty response structure
            return {
                "id": f"analysis-{device_data['deviceId']}-{int(device_data['timestamp'])}",
                "success": False,
                "timestamp": int(device_data['timestamp']),
                "message": "Failed to generate optimization suggestions.",
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
    except Exception as e:
        logger.error(f"[PowerGuard] Error calling Groq API: {e}", exc_info=True)
        # Return fallback response
        return {
            "id": f"analysis-{device_data['deviceId']}-{int(device_data['timestamp'])}",
            "success": False,
            "timestamp": int(device_data['timestamp']),
            "message": f"Error analyzing device data: {str(e)}",
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

def format_apps(apps):
    """Format apps data for the prompt"""
    logger.debug(f"[PowerGuard] Formatting data for {len(apps)} apps")
    result = ""
    for app in apps[:5]:  # Limit to top 5 apps to keep prompt size reasonable
        result += f"- {app['appName']} ({app['packageName']}): {app['foregroundTime']/60:.1f}min foreground, {app['backgroundTime']/60:.1f}min background\n"
        result += f"  Battery: {app['batteryUsage']}%, Data: {app['dataUsage']['foreground'] + app['dataUsage']['background']:.1f}MB\n"
    return result 