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
import time
import random

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_llm')

# Retry configuration
MAX_RETRIES = 5  # Increased from 3 to 5
INITIAL_RETRY_DELAY = 2  # Increased from 1 to 2 seconds
MAX_RETRY_DELAY = 120  # Increased from 60 to 120 seconds

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
    logger = logging.getLogger("powerguard_api")
    
    # Extract and clean prompt if present
    prompt = device_data.get("prompt", "").strip() if device_data.get("prompt") is not None else ""
    
    # Determine optimization focus based on prompt or default to combined
    optimization_type = "combined"
    if prompt:
        prompt_lower = prompt.lower()
        if any(term in prompt_lower for term in ["battery", "power", "energy"]) and not any(term in prompt_lower for term in ["data", "network", "internet"]):
            optimization_type = "battery"
        elif any(term in prompt_lower for term in ["data", "network", "internet"]) and not any(term in prompt_lower for term in ["battery", "power", "energy"]):
            optimization_type = "data"
        elif "not" in prompt_lower:
            # Handle negation cases
            if "not data" in prompt_lower or "not network" in prompt_lower:
                optimization_type = "battery"
            elif "not battery" in prompt_lower or "not power" in prompt_lower:
                optimization_type = "data"
    
    # Generate system content based on optimization type
    system_content = """You are PowerGuard, an AI system that analyzes device usage data and provides actionable recommendations for optimizing battery life and data usage. 
Your responses must be in valid JSON format with the following required fields:
{
  "id": "string",
  "success": boolean,
  "timestamp": number,
  "message": "string",
  "actionable": [
    {
      "id": "string",
      "type": "OPTIMIZE_BATTERY" | "RESTRICT_BACKGROUND" | "ENABLE_DATA_SAVER" | "DISABLE_FEATURES",
      "packageName": "string",
      "description": "string",
      "reason": "string",
      "newMode": "string",
      "parameters": object
    }
  ],
  "insights": [
    {
      "type": "string",
      "title": "string",
      "description": "string",
      "severity": "low" | "medium" | "high"
    }
  ],
  "batteryScore": number (0-100),
  "dataScore": number (0-100),
  "performanceScore": number (0-100),
  "estimatedSavings": {
    "batteryMinutes": number,
    "dataMB": number
  }
}

You MUST provide at least one actionable item and one insight.
"""

    # Add optimization-specific instructions
    if optimization_type == "battery":
        system_content += "\nFocus on battery optimization actions (OPTIMIZE_BATTERY, RESTRICT_BACKGROUND)."
    elif optimization_type == "data":
        system_content += "\nFocus on data optimization actions (ENABLE_DATA_SAVER, DISABLE_FEATURES)."
    else:
        system_content += "\nProvide a balanced mix of battery and data optimization actions."

    # Generate user content with device data analysis request
    apps_data = device_data.get("apps", [])
    battery_heavy_apps = [app for app in apps_data if app.get("batteryUsage", 0) > 10]
    data_heavy_apps = [app for app in apps_data if app.get("dataUsage", {}).get("background", 0) > 10]

    user_content = f"""Analyze the following device data and provide optimization recommendations:

Battery Status:
- Level: {device_data.get("batteryLevel", 0)}%
- Temperature: {device_data.get("batteryTemperature", 0)}°C
- Charging: {device_data.get("isCharging", False)}

Memory Usage:
- Available: {device_data.get("availableMemory", 0)} MB
- Total: {device_data.get("totalMemory", 0)} MB

CPU Usage: {device_data.get("cpuUsage", 0)}%

Network Data:
- Rx Bytes: {device_data.get("networkData", {}).get("rxBytes", 0)}
- Tx Bytes: {device_data.get("networkData", {}).get("txBytes", 0)}

Heavy Battery Usage Apps: {", ".join(app.get("appName", "") for app in battery_heavy_apps)}
Heavy Data Usage Apps: {", ".join(app.get("appName", "") for app in data_heavy_apps)}

User Prompt: {prompt if prompt else "Provide general optimization recommendations"}

Provide specific, actionable recommendations to optimize the device based on this data."""

    # Call Groq API with retry logic
    for attempt in range(MAX_RETRIES):
        try:
            # Add jitter to retry delay
            current_delay = min(INITIAL_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_RETRY_DELAY)
            
            logger.info(f"[PowerGuard] Calling Groq API (attempt {attempt + 1}/{MAX_RETRIES})")
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"[PowerGuard] Raw LLM response: {response_text}")
            
            try:
                # Remove code block markers if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                response_data = json.loads(response_text)
                
                # Validate required fields
                required_fields = ["id", "success", "timestamp", "message", "actionable", "insights", 
                                 "batteryScore", "dataScore", "performanceScore", "estimatedSavings"]
                missing_fields = [field for field in required_fields if field not in response_data]
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
                # Validate actionable items
                if not response_data["actionable"]:
                    raise ValueError("At least one actionable item is required")
                
                for action in response_data["actionable"]:
                    required_action_fields = ["id", "type", "packageName", "description", "reason", "newMode"]
                    missing_action_fields = [field for field in required_action_fields if field not in action]
                    if missing_action_fields:
                        raise ValueError(f"Missing required action fields: {', '.join(missing_action_fields)}")
                    
                    if action["type"] not in ALLOWED_ACTIONABLE_TYPES:
                        raise ValueError(f"Invalid action type: {action['type']}")
                
                # Validate insights
                if not response_data["insights"]:
                    raise ValueError("At least one insight is required")
                
                for insight in response_data["insights"]:
                    required_insight_fields = ["type", "title", "description", "severity"]
                    missing_insight_fields = [field for field in required_insight_fields if field not in insight]
                    if missing_insight_fields:
                        raise ValueError(f"Missing required insight fields: {', '.join(missing_insight_fields)}")
                    
                    if insight["severity"] not in ["low", "medium", "high"]:
                        raise ValueError(f"Invalid severity level: {insight['severity']}")
                
                # Validate scores
                for score_field in ["batteryScore", "dataScore", "performanceScore"]:
                    score = response_data.get(score_field)
                    if not isinstance(score, (int, float)) or score < 0 or score > 100:
                        raise ValueError(f"Invalid {score_field}: {score}")
                
                # Validate estimated savings
                savings = response_data.get("estimatedSavings")
                if not isinstance(savings, dict):
                    raise ValueError("estimatedSavings must be an object")
                
                for field in ["batteryMinutes", "dataMB"]:
                    value = savings.get(field)
                    if not isinstance(value, (int, float)) or value < 0:
                        raise ValueError(f"Invalid {field}: {value}")
                
                logger.info("[PowerGuard] Successfully validated LLM response")
                return response_data
                
            except json.JSONDecodeError as e:
                logger.error(f"[PowerGuard] Failed to parse LLM response as JSON: {str(e)}")
                raise ValueError("Invalid JSON response from LLM")
            except ValueError as e:
                logger.error(f"[PowerGuard] Validation error: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"[PowerGuard] Error calling Groq API: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"[PowerGuard] Retrying in {current_delay:.2f} seconds...")
                time.sleep(current_delay)
            else:
                logger.error("[PowerGuard] Max retries reached, failing")
                raise

def format_apps(apps):
    """Format apps data for the prompt"""
    logger.debug(f"[PowerGuard] Formatting data for {len(apps)} apps")
    result = ""
    try:
        # Ensure apps is a list
        if not isinstance(apps, list):
            logger.warning("[PowerGuard] Apps data is not a list")
            return "No valid app data available.\n"
        
        # Sort apps by battery usage (descending) and take top 5
        sorted_apps = sorted(apps, key=lambda x: float(x.get('batteryUsage', 0)), reverse=True)[:5]
        
        for app in sorted_apps:
            try:
                # Get app name and package name safely
                app_name = app.get('appName', 'Unknown App')
                package_name = app.get('packageName', 'unknown.package')
                
                # Get time values safely and convert to minutes
                foreground_time = float(app.get('foregroundTime', 0)) / 60
                background_time = float(app.get('backgroundTime', 0)) / 60
                
                # Get battery usage safely
                battery_usage = float(app.get('batteryUsage', 0))
                
                # Get data usage safely
                data_usage = app.get('dataUsage', {})
                if not isinstance(data_usage, dict):
                    data_usage = {}
                foreground_data = float(data_usage.get('foreground', 0))
                background_data = float(data_usage.get('background', 0))
                total_data = foreground_data + background_data
                
                # Format the app entry
                result += f"- {app_name} ({package_name}): {foreground_time:.1f}min foreground, {background_time:.1f}min background\n"
                result += f"  Battery: {battery_usage:.1f}%, Data: {total_data:.1f}MB\n"
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"[PowerGuard] Error formatting app data: {str(e)}")
                continue
        
        # If no apps were successfully formatted
        if not result:
            result = "No valid app data available.\n"
        
        return result
    except Exception as e:
        logger.error(f"[PowerGuard] Error in format_apps: {str(e)}")
        return "Error formatting app data.\n" 