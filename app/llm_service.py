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
        UsagePattern.device_id == device_id
    ).order_by(UsagePattern.timestamp.desc()).all()
    
    # Group patterns by package name, taking the most recent pattern for each package
    result = {}
    for pattern in patterns:
        if pattern.package_name not in result:
            result[pattern.package_name] = pattern.pattern
    
    logger.debug(f"[PowerGuard] Found {len(result)} historical patterns for device {device_id}")
    return result

def analyze_device_data(device_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Process device data through Groq LLM and get optimization recommendations"""
    logger.info(f"[PowerGuard] Starting analysis for device: {device_data['device_id']}")
    logger.debug(f"[PowerGuard] Received device data: {json.dumps(device_data, indent=2)}")
    
    # Get historical patterns for this device
    historical_patterns = get_historical_patterns(db, device_data['device_id'])
    
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
    App Usage:
    {format_app_usage(device_data['app_usage'])}
    
    Battery Stats:
    - Level: {device_data['battery_stats']['level']}%
    - Temperature: {device_data['battery_stats']['temperature']}°C
    - Charging: {device_data['battery_stats']['is_charging']}
    
    Wake Locks:
    {format_wake_locks(device_data['wake_locks'])}
    
    Network Usage:
    {format_network_usage(device_data['network_usage'])}
    
    Based on both the historical patterns and current data, generate:
    
    1. actionables: A list of specific actions to take (JSON format)
       Example format:
       [
         {{"type": "app_mode_change", "app": "package_name", "new_mode": "strict"}},
         {{"type": "disable_wakelock", "app": "package_name"}},
         {{"type": "restrict_background_data", "app": "package_name", "enabled": true}},
         {{"type": "cut_charging", "reason": "reason"}}
       ]
    
    2. summary: A human-readable explanation of what changes were made
    
    3. usage_patterns: Key behavioral trends as {{"package_name": "pattern description"}}
    
    Return ONLY valid JSON with those 3 keys plus a timestamp. Do not include any other text or explanation.
    """
    
    logger.debug(f"[PowerGuard] Generated prompt for LLM: {prompt}")
    
    # Call Groq API
    try:
        logger.info("[PowerGuard] Calling Groq API for analysis")
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # or other Groq model
            messages=[
                {"role": "system", "content": "You are an AI battery optimization expert that analyzes device data and provides actionable recommendations, taking into account historical usage patterns. Always respond with valid JSON only, no additional text."},
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
                # Ensure timestamp is an integer
                if 'timestamp' in response_data:
                    if isinstance(response_data['timestamp'], str):
                        try:
                            dt = datetime.fromisoformat(response_data['timestamp'].replace('Z', '+00:00'))
                            response_data['timestamp'] = int(dt.timestamp())
                        except ValueError:
                            response_data['timestamp'] = device_data['timestamp']
                    elif not isinstance(response_data['timestamp'], int):
                        response_data['timestamp'] = device_data['timestamp']
                else:
                    response_data['timestamp'] = device_data['timestamp']
                
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
                "actionables": [],
                "summary": "Failed to generate optimization suggestions.",
                "usage_patterns": {},
                "timestamp": device_data['timestamp']
            }
    except Exception as e:
        logger.error(f"[PowerGuard] Error calling Groq API: {e}", exc_info=True)
        # Return fallback response
        return {
            "actionables": [],
            "summary": f"Error analyzing device data: {str(e)}",
            "usage_patterns": {},
            "timestamp": device_data['timestamp']
        }

def format_app_usage(app_usage):
    """Format app usage data for the prompt"""
    logger.debug(f"[PowerGuard] Formatting app usage data for {len(app_usage)} apps")
    result = ""
    for app in app_usage[:5]:  # Limit to top 5 apps to keep prompt size reasonable
        result += f"- {app['app_name']} ({app['package_name']}): {app['foreground_time_ms']/3600000:.1f}h foreground, {app['background_time_ms']/3600000:.1f}h background\n"
    return result

def format_wake_locks(wake_locks):
    """Format wake lock data for the prompt"""
    logger.debug(f"[PowerGuard] Formatting wake lock data for {len(wake_locks)} locks")
    result = ""
    for lock in wake_locks:
        result += f"- {lock['package_name']}: {lock['wake_lock_name']} held for {lock['time_held_ms']/3600000:.1f}h\n"
    return result

def format_network_usage(network_usage):
    """Format network usage data for the prompt"""
    logger.debug(f"[PowerGuard] Formatting network usage data for {len(network_usage['app_network_usage'])} apps")
    result = ""
    for app in network_usage['app_network_usage'][:5]:  # Limit to top 5 apps
        result += f"- {app['package_name']}: {app['data_usage_bytes']/1000000:.1f}MB data, {app['wifi_usage_bytes']/1000000:.1f}MB wifi\n"
    return result 