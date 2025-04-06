import os
from groq import Groq
from dotenv import load_dotenv
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import UsagePattern
import logging
from datetime import datetime
from app.prompt_analyzer import (
    classify_user_prompt, 
    is_prompt_relevant, 
    classify_with_llm, 
    generate_optimization_prompt,
    ALLOWED_ACTIONABLE_TYPES
)

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
    
    # Check if a user prompt is provided
    user_prompt = device_data.get('prompt')
    prompt_classification = None
    
    if user_prompt:
        logger.info(f"[PowerGuard] User provided prompt: '{user_prompt}'")
        
        # Try rule-based classification first
        rule_classification = classify_user_prompt(user_prompt)
        
        # If rule-based classification finds the prompt relevant, use it
        if rule_classification["is_relevant"]:
            logger.info(f"[PowerGuard] Rule-based classification identified relevant prompt")
            prompt_classification = rule_classification
        else:
            # Fall back to LLM-based classification
            logger.info(f"[PowerGuard] Attempting LLM-based classification")
            llm_classification = classify_with_llm(user_prompt, groq_client)
            
            if llm_classification["is_relevant"]:
                logger.info(f"[PowerGuard] LLM-based classification identified relevant prompt")
                prompt_classification = llm_classification
            else:
                logger.info(f"[PowerGuard] Prompt classified as not relevant, using default analysis")
                
        # Add the original prompt to the classification for reference
        if prompt_classification:
            prompt_classification["original_prompt"] = user_prompt
    
    # Generate the appropriate prompt based on classification
    if prompt_classification and prompt_classification["is_relevant"]:
        prompt = generate_optimization_prompt(prompt_classification, device_data, historical_patterns_text)
        logger.debug(f"[PowerGuard] Generated specialized prompt for LLM: {prompt}")
        
        # Adjust system content based on classification
        system_content = "You are an AI resource optimization expert that analyzes device data and provides actionable recommendations. "
        
        if prompt_classification["optimize_battery"] and prompt_classification["optimize_data"]:
            system_content += "Focus on optimizing both battery life and data usage. "
        elif prompt_classification["optimize_battery"]:
            system_content += "Focus on optimizing battery life. "
        elif prompt_classification["optimize_data"]:
            system_content += "Focus on optimizing data usage. "
            
        system_content += "Only use the exact action types provided, and respond with valid JSON only, no additional text."
    else:
        # Use the standard prompt and system content
        prompt = f"""
        As an AI resource optimization expert, analyze this Android device data:
        
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
           - type: the type of action (MUST be one of these EXACT values: KILL_APP, RESTRICT_BACKGROUND, OPTIMIZE_BATTERY, MARK_APP_INACTIVE, SET_STANDBY_BUCKET, ENABLE_BATTERY_SAVER, ENABLE_DATA_SAVER, ADJUST_SYNC_SETTINGS, CATEGORIZE_APP)
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
        
        logger.debug(f"[PowerGuard] Generated standard prompt for LLM: {prompt}")
        system_content = "You are an AI battery and resource optimization expert that analyzes device data and provides actionable recommendations. Always respond with valid JSON only, no additional text."
    
    # Call Groq API
    try:
        logger.info("[PowerGuard] Calling Groq API for analysis")
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # or other Groq model
            messages=[
                {"role": "system", "content": system_content},
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
                
                # Validate actionable types to ensure they match allowed types
                if 'actionable' in response_data and isinstance(response_data['actionable'], list):
                    for i, action in enumerate(response_data['actionable']):
                        # Ensure required fields exist and have valid values
                        if 'type' not in action or action['type'] not in ALLOWED_ACTIONABLE_TYPES:
                            logger.warning(f"[PowerGuard] Invalid action type '{action.get('type')}' found, replacing with OPTIMIZE_BATTERY")
                            response_data['actionable'][i]['type'] = "OPTIMIZE_BATTERY"
                        
                        # Ensure packageName exists and is a string
                        if 'packageName' not in action or not isinstance(action.get('packageName'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid packageName in action, setting default")
                            response_data['actionable'][i]['packageName'] = "com.android.system"
                        
                        # Ensure description exists and is a string
                        if 'description' not in action or not isinstance(action.get('description'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid description in action, setting default")
                            response_data['actionable'][i]['description'] = f"Perform {action.get('type', 'OPTIMIZE_BATTERY')} action"
                        
                        # Ensure reason exists and is a string
                        if 'reason' not in action or not isinstance(action.get('reason'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid reason in action, setting default")
                            response_data['actionable'][i]['reason'] = "Resource optimization needed"
                        
                        # Ensure newMode exists and is a string
                        if 'newMode' not in action or not isinstance(action.get('newMode'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid newMode in action, setting default")
                            response_data['actionable'][i]['newMode'] = "optimized"
                        
                        # Ensure parameters exists and is a dict
                        if 'parameters' not in action or not isinstance(action.get('parameters'), dict):
                            logger.warning(f"[PowerGuard] Missing or invalid parameters in action, setting default")
                            response_data['actionable'][i]['parameters'] = {}
                        
                        # Ensure id exists and is a string
                        if 'id' not in action or not isinstance(action.get('id'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid id in action, setting default")
                            response_data['actionable'][i]['id'] = f"action-{i+1}"
                
                # Validate insights to ensure they have required fields
                if 'insights' in response_data and isinstance(response_data['insights'], list):
                    for i, insight in enumerate(response_data['insights']):
                        # Ensure type exists and is a string
                        if 'type' not in insight or not isinstance(insight.get('type'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid type in insight, setting default")
                            response_data['insights'][i]['type'] = "ResourceUsage"
                        
                        # Ensure title exists and is a string
                        if 'title' not in insight or not isinstance(insight.get('title'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid title in insight, setting default")
                            response_data['insights'][i]['title'] = "Resource optimization insight"
                        
                        # Ensure description exists and is a string
                        if 'description' not in insight or not isinstance(insight.get('description'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid description in insight, setting default")
                            response_data['insights'][i]['description'] = "Resource usage pattern detected"
                        
                        # Ensure severity exists and is a string
                        if 'severity' not in insight or not isinstance(insight.get('severity'), str):
                            logger.warning(f"[PowerGuard] Missing or invalid severity in insight, setting default")
                            response_data['insights'][i]['severity'] = "medium"
                
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