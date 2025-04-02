import os
from groq import Groq
from dotenv import load_dotenv
import json
from typing import Dict, Any

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_device_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process device data through Groq LLM and get optimization recommendations"""
    
    # Convert device data to a more readable format for the prompt
    prompt = f"""
    As an AI battery optimization expert, analyze this Android device data:
    
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
    
    Based on this data, generate:
    
    1. actionables: A list of specific actions to take (JSON format)
       [
         {"type": "app_mode_change", "app": "package_name", "new_mode": "strict"},
         {"type": "disable_wakelock", "app": "package_name"},
         {"type": "restrict_background_data", "app": "package_name", "enabled": true},
         {"type": "cut_charging", "reason": "reason"}
       ]
    
    2. summary: A human-readable explanation of what changes were made
    
    3. usage_patterns: Key behavioral trends as {"package_name": "pattern description"}
    
    Return ONLY valid JSON with those 3 keys plus a timestamp.
    """
    
    # Call Groq API
    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # or other Groq model
            messages=[
                {"role": "system", "content": "You are an AI battery optimization expert that analyzes device data and provides actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        # Extract JSON from response
        response_text = completion.choices[0].message.content
        # Find JSON part in the response (in case LLM adds explanatory text)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            response_data = json.loads(json_str)
            # Add timestamp if not present
            if 'timestamp' not in response_data:
                response_data['timestamp'] = device_data['timestamp']
            return response_data
        else:
            # Fallback with empty response structure
            return {
                "actionables": [],
                "summary": "Failed to generate optimization suggestions.",
                "usage_patterns": {},
                "timestamp": device_data['timestamp']
            }
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        # Return fallback response
        return {
            "actionables": [],
            "summary": f"Error analyzing device data: {str(e)}",
            "usage_patterns": {},
            "timestamp": device_data['timestamp']
        }

def format_app_usage(app_usage):
    """Format app usage data for the prompt"""
    result = ""
    for app in app_usage[:5]:  # Limit to top 5 apps to keep prompt size reasonable
        result += f"- {app['app_name']} ({app['package_name']}): {app['foreground_time_ms']/3600000:.1f}h foreground, {app['background_time_ms']/3600000:.1f}h background\n"
    return result

def format_wake_locks(wake_locks):
    """Format wake lock data for the prompt"""
    result = ""
    for lock in wake_locks:
        result += f"- {lock['package_name']}: {lock['wake_lock_name']} held for {lock['time_held_ms']/3600000:.1f}h\n"
    return result

def format_network_usage(network_usage):
    """Format network usage data for the prompt"""
    result = ""
    for app in network_usage['app_network_usage'][:5]:  # Limit to top 5 apps
        result += f"- {app['package_name']}: {app['data_usage_bytes']/1000000:.1f}MB data, {app['wifi_usage_bytes']/1000000:.1f}MB wifi\n"
    return result 