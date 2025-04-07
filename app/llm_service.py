import os
from groq import Groq
from dotenv import load_dotenv
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database import UsagePattern
import logging
from datetime import datetime
import time
import random

# Import our new utility modules
from app.utils.strategy_analyzer import determine_strategy
from app.utils.insight_generator import generate_insights
from app.utils.actionable_generator import generate_actionables, is_information_request, ACTIONABLE_TYPES

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_llm')

# Retry configuration
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 2
MAX_RETRY_DELAY = 120

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
    logger.info(f"[PowerGuard] Analyzing device data for device: {device_data.get('deviceId', 'unknown')}")
    
    # Extract prompt if present
    prompt = device_data.get("prompt", "").strip() if device_data.get("prompt") is not None else ""
    
    try:
        # Check if this is an information request
        info_request = False
        if prompt:
            info_request = is_information_request(prompt)
            logger.info(f"[PowerGuard] Prompt classified as {'information request' if info_request else 'optimization request'}")
        
        # Always determine the optimization strategy based on device data and prompt
        # even for information requests (we'll use it for insights)
        strategy = determine_strategy(device_data, prompt)
        logger.debug(f"[PowerGuard] Determined strategy: {strategy}")
        
        # Handle information requests specifically
        actionables = []
        if info_request:
            # Information requests should never generate actionables
            actionables = []
            
            # For information requests, set insights to match the query focus
            strategy["show_battery_savings"] = False  # Don't show savings for info requests
            strategy["show_data_savings"] = False
            
            # Determine query focus based on keywords
            if "battery" in prompt.lower():
                strategy["focus"] = "battery"
                logger.info("[PowerGuard] Information request focused on battery")
            elif "data" in prompt.lower() or "network" in prompt.lower():
                strategy["focus"] = "network"
                logger.info("[PowerGuard] Information request focused on data/network")
            else:
                strategy["focus"] = "both"  # If unclear, show both types of information
                logger.info("[PowerGuard] Information request with general focus")
        else:
            # Generate actionables for optimization requests
            actionables = generate_actionables(strategy, device_data)
            logger.debug(f"[PowerGuard] Generated {len(actionables)} actionables")
        
        # Calculate estimated savings once - for consistency between insights and response
        savings = {
            "batteryMinutes": 0,
            "dataMB": 0
        }
        
        # Only calculate savings for optimization requests
        if not info_request and (strategy["show_battery_savings"] or strategy["show_data_savings"]):
            from app.utils.strategy_analyzer import calculate_savings
            savings = calculate_savings(strategy, strategy["critical_apps"])
            logger.debug(f"[PowerGuard] Calculated savings: battery={savings['batteryMinutes']}min, data={savings['dataMB']}MB")
            
            # Store the savings directly in the strategy for insights to use
            strategy["calculated_savings"] = savings
        
        # Generate insights based on strategy, passing the original prompt for question detection
        insights = generate_insights(strategy, device_data, info_request, prompt)
        logger.debug(f"[PowerGuard] Generated {len(insights)} insights")
        
        # If no insights were generated (unlikely), add a fallback message
        if not insights:
            if info_request:
                # Fallback for information requests
                insights = [{
                    "type": "Information",
                    "title": "App Usage Information",
                    "description": "I don't have enough data to provide detailed usage information. Please check your device settings for more accurate usage statistics.",
                    "severity": "info"
                }]
            else:
                # Fallback for optimization requests
                insights = [{
                    "type": "Default",
                    "title": "Default Insight",
                    "description": "No specific insights available for optimization.",
                    "severity": "low"
                }]
        
        # If no actionables were generated for an optimization request, add a default one
        if not info_request and not actionables:
            actionables = [{
                "id": f"default-{int(time.time())}",
                "type": "OPTIMIZE_BATTERY",
                "packageName": "system",
                "description": "Apply default battery optimization",
                "reason": "General optimization",
                "newMode": "optimized",
                "parameters": {}
            }]
        
        # Construct the response - using the previously calculated savings
        response = {
            "id": f"gen_{int(datetime.now().timestamp())}",
            "success": True,
            "timestamp": int(datetime.now().timestamp()),
            "message": "Analysis completed successfully",
            "responseType": "information" if info_request else "optimization",
            "actionable": actionables,
            "insights": insights,
            "batteryScore": calculate_battery_score(device_data),
            "dataScore": calculate_data_score(device_data),
            "performanceScore": calculate_performance_score(device_data),
            "estimatedSavings": savings
        }
        
        # Store device usage patterns in database
        if not info_request:
            try:
                store_usage_patterns(device_data, db, strategy)
            except Exception as db_error:
                logger.error(f"[PowerGuard] Database error storing usage patterns: {str(db_error)}")
                # Don't fail the whole request due to DB error
        
        return response
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"[PowerGuard] Error analyzing device data: {error_message}", exc_info=True)
        
        # Customize error message based on type
        if "rate limit" in error_message.lower() or "429" in error_message:
            friendly_message = "Service is currently experiencing high demand. Please try again in a few moments."
            error_type = "RateLimit"
        elif "timeout" in error_message.lower():
            friendly_message = "Request timed out. Please try again."
            error_type = "Timeout"
        elif "dict" in error_message and "int" in error_message:
            friendly_message = "Error processing device data format. Please ensure your device data is correctly formatted."
            error_type = "DataFormat"
        else:
            friendly_message = f"An error occurred while analyzing your device data: {error_message}"
            error_type = "General"
        
        # Return a valid response with default values in case of error
        return {
            "id": f"error_{int(datetime.now().timestamp())}",
            "success": False,
            "timestamp": int(datetime.now().timestamp()),
            "message": f"Error processing device data: {error_message}",
            "actionable": [],
            "insights": [{
                "type": error_type,
                "title": "Error Analyzing Device Data",
                "description": friendly_message,
                "severity": "high"
            }],
            "batteryScore": 50,
            "dataScore": 50,
            "performanceScore": 50,
            "estimatedSavings": {
                "batteryMinutes": 0,
                "dataMB": 0
            }
        }

def store_usage_patterns(device_data: Dict[str, Any], db: Session, strategy: Dict[str, Any]) -> None:
    """Store device usage patterns in the database"""
    try:
        device_id = device_data.get("deviceId")
        if not device_id:
            logger.warning("[PowerGuard] Cannot store patterns: Missing device ID")
            return
        
        # Get app data from device_data
        apps = device_data.get("apps", [])
        timestamp = int(datetime.now().timestamp())
        
        for app in apps:
            package_name = app.get("packageName")
            battery_usage = app.get("batteryUsage", 0)
            data_usage = app.get("dataUsage", 0)
            foreground_time = app.get("foregroundTime", 0)
            
            if not package_name:
                continue
            
            # Generate a pattern description based on usage
            pattern = generate_usage_pattern(
                package_name,
                battery_usage,
                data_usage,
                foreground_time,
                strategy
            )
            
            # Check if this pattern exists in the database
            existing = db.query(UsagePattern).filter(
                UsagePattern.deviceId == device_id,
                UsagePattern.packageName == package_name
            ).first()
            
            if existing:
                # Update existing pattern
                existing.pattern = pattern
                existing.timestamp = timestamp
            else:
                # Create new pattern
                new_pattern = UsagePattern(
                    deviceId=device_id,
                    packageName=package_name,
                    pattern=pattern,
                    timestamp=timestamp
                )
                db.add(new_pattern)
            
        # Commit changes
        db.commit()
        logger.info(f"[PowerGuard] Stored usage patterns for {len(apps)} apps")
    
    except Exception as e:
        logger.error(f"[PowerGuard] Error storing usage patterns: {str(e)}", exc_info=True)
        db.rollback()

def generate_usage_pattern(
    package_name: str,
    battery_usage: float,
    data_usage: float,
    foreground_time: int,
    strategy: Dict[str, Any]
) -> str:
    """Generate a usage pattern description based on app usage"""
    patterns = []
    
    # Battery usage patterns
    if battery_usage > 20:
        patterns.append("Very high battery usage")
    elif battery_usage > 10:
        patterns.append("High battery usage")
    elif battery_usage > 5:
        patterns.append("Moderate battery usage")
    
    # Data usage patterns
    if data_usage > 500:
        patterns.append("Very high data usage")
    elif data_usage > 200:
        patterns.append("High data usage")
    elif data_usage > 50:
        patterns.append("Moderate data usage")
    
    # Foreground time patterns
    if foreground_time > 3600:  # More than 1 hour
        patterns.append("Frequently used in foreground")
    elif foreground_time > 1800:  # More than 30 minutes
        patterns.append("Moderately used in foreground")
    elif foreground_time < 300:  # Less than 5 minutes
        patterns.append("Rarely used in foreground")
    
    # Check if it's a critical app
    if package_name in strategy.get("critical_apps", []):
        patterns.append("Critical app for user")
    
    if not patterns:
        return "Normal usage pattern"
    
    return "; ".join(patterns)

def calculate_battery_score(device_data: Dict[str, Any]) -> int:
    """Calculate a battery health score (0-100)"""
    battery_level = device_data.get("battery", {}).get("level", 100)
    battery_health = device_data.get("battery", {}).get("health", 100)
    
    # Start with the battery health value
    score = battery_health
    
    # Adjust based on battery level - lower level means more pressing optimization need
    if battery_level < 20:
        score -= 20
    elif battery_level < 50:
        score -= 10
    
    # Ensure score is within 0-100 range
    return max(0, min(100, int(score)))

def calculate_data_score(device_data: Dict[str, Any]) -> int:
    """Calculate a data usage health score (0-100)"""
    # Extract network data if available
    network = device_data.get("network", {})
    data_used = network.get("dataUsed", 0)
    
    # Default score - higher is better
    score = 80
    
    # Adjust score based on data used
    if data_used > 1000:  # More than 1GB
        score -= 30
    elif data_used > 500:  # More than 500MB
        score -= 20
    elif data_used > 200:  # More than 200MB
        score -= 10
    
    # Ensure score is within 0-100 range
    return max(0, min(100, int(score)))

def calculate_performance_score(device_data: Dict[str, Any]) -> int:
    """Calculate a performance health score (0-100)"""
    memory = device_data.get("memory", {})
    cpu = device_data.get("cpu", {})
    
    # Extract values with defaults
    total_memory = memory.get("total", 0)
    used_memory = memory.get("used", 0)
    cpu_usage = cpu.get("usage", 0)
    
    # Calculate memory usage percentage
    memory_usage_pct = (used_memory / total_memory * 100) if total_memory > 0 else 0
    
    # Start with a base score
    score = 100
    
    # Adjust based on memory usage
    if memory_usage_pct > 90:
        score -= 30
    elif memory_usage_pct > 80:
        score -= 20
    elif memory_usage_pct > 70:
        score -= 10
    
    # Adjust based on CPU usage
    if cpu_usage > 80:
        score -= 30
    elif cpu_usage > 60:
        score -= 20
    elif cpu_usage > 40:
        score -= 10
    
    # Ensure score is within 0-100 range
    return max(0, min(100, int(score)))

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