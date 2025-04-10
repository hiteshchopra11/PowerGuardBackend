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
        
        # Get device info for enhanced analysis if available
        device_info = device_data.get("deviceInfo", {})
        settings = device_data.get("settings", {})
        
        # Log additional device information if available
        if device_info:
            logger.debug(f"[PowerGuard] Analyzing data for {device_info.get('manufacturer', 'Unknown')} {device_info.get('model', 'Unknown')}, OS: {device_info.get('osVersion', 'Unknown')}")
        
        # Include device settings in strategy determination
        is_battery_optimization_enabled = settings.get("batteryOptimization", False) if settings else False
        is_data_saver_enabled = settings.get("dataSaver", False) if settings else False
        is_power_save_mode_enabled = settings.get("powerSaveMode", False) if settings else False
        
        # Log device settings
        if settings:
            logger.debug(f"[PowerGuard] Device settings - Battery Optimization: {is_battery_optimization_enabled}, Data Saver: {is_data_saver_enabled}, Power Save: {is_power_save_mode_enabled}")
        
        # Always determine the optimization strategy based on device data and prompt
        # even for information requests (we'll use it for insights)
        try:
            strategy = determine_strategy(device_data, prompt)
            logger.debug(f"[PowerGuard] Strategy determined successfully")
        except Exception as strategy_error:
            if "429" in str(strategy_error) or "rate limit" in str(strategy_error).lower():
                logger.error(f"[PowerGuard] Rate limit error in strategy determination: {str(strategy_error)}")
                raise Exception("429: Rate limit exceeded in strategy determination")
            logger.error(f"[PowerGuard] Error determining strategy: {str(strategy_error)}", exc_info=True)
            raise Exception(f"Error determining strategy: {str(strategy_error)}")
        
        # Enhance strategy with additional device settings
        strategy.update({
            "batteryOptimizationEnabled": is_battery_optimization_enabled,
            "dataSaverEnabled": is_data_saver_enabled,
            "powerSaveModeEnabled": is_power_save_mode_enabled,
            "deviceManufacturer": device_info.get("manufacturer", "") if device_info else "",
            "deviceModel": device_info.get("model", "") if device_info else "",
            "osVersion": device_info.get("osVersion", "") if device_info else ""
        })
        
        logger.debug(f"[PowerGuard] Determined strategy: {strategy}")
        
        # Generate insights first to check if it's a yes/no question
        try:
            insights = generate_insights(strategy, device_data, info_request, prompt)
            logger.debug(f"[PowerGuard] Generated {len(insights)} insights")
        except Exception as insights_error:
            if "429" in str(insights_error) or "rate limit" in str(insights_error).lower():
                logger.error(f"[PowerGuard] Rate limit error in insights generation: {str(insights_error)}")
                raise Exception("429: Rate limit exceeded in insights generation")
            logger.error(f"[PowerGuard] Error generating insights: {str(insights_error)}", exc_info=True)
            raise Exception(f"Error generating insights: {str(insights_error)}")
        
        # Check if this is a yes/no question by looking at the first insight type
        is_yes_no = insights and insights[0].get("type") == "YesNo"
        
        # Handle yes/no questions and information requests specifically
        actionables = []
        if is_yes_no or info_request:
            # Yes/no questions and information requests should never generate actionables
            actionables = []
            
            # For information requests, set insights to match the query focus
            strategy["show_battery_savings"] = False  # Don't show savings for info requests
            strategy["show_data_savings"] = False
        else:
            # Generate actionables for optimization requests
            try:
                actionables = generate_actionables(strategy, device_data)
                logger.debug(f"[PowerGuard] Generated {len(actionables)} actionables")
            except Exception as actionables_error:
                if "429" in str(actionables_error) or "rate limit" in str(actionables_error).lower():
                    logger.error(f"[PowerGuard] Rate limit error in actionables generation: {str(actionables_error)}")
                    raise Exception("429: Rate limit exceeded in actionables generation")
                logger.error(f"[PowerGuard] Error generating actionables: {str(actionables_error)}", exc_info=True)
                raise Exception(f"Error generating actionables: {str(actionables_error)}")
        
        # Calculate estimated savings once - for consistency between insights and response
        savings = {
            "batteryMinutes": 0,
            "dataMB": 0
        }
        
        # Only calculate savings for optimization requests that are not yes/no questions
        if not (info_request or is_yes_no) and (strategy["show_battery_savings"] or strategy["show_data_savings"]):
            try:
                from app.utils.strategy_analyzer import calculate_savings
                savings = calculate_savings(strategy, strategy["critical_apps"])
                logger.debug(f"[PowerGuard] Calculated savings: battery={savings['batteryMinutes']}min, data={savings['dataMB']}MB")
                
                # Store the savings directly in the strategy for insights to use
                strategy["calculated_savings"] = savings
            except Exception as savings_error:
                logger.error(f"[PowerGuard] Error calculating savings: {str(savings_error)}", exc_info=True)
                # Don't fail the whole request, just log and continue with zero savings
        
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
        
        # If no actionables were generated for an optimization request (and not a yes/no question)
        if not (info_request or is_yes_no) and not actionables:
            actionables = [{
                "id": f"default-{int(time.time())}",
                "type": "OPTIMIZE_BATTERY",
                "packageName": "system",
                "description": "Apply default battery optimization",
                "reason": "General optimization",
                "newMode": "optimized",
                "parameters": {}
            }]
        
        try:
            battery_score = calculate_battery_score(device_data)
            data_score = calculate_data_score(device_data)
            performance_score = calculate_performance_score(device_data)
        except Exception as score_error:
            logger.error(f"[PowerGuard] Error calculating scores: {str(score_error)}", exc_info=True)
            battery_score = 50.0  # Default scores if calculation fails
            data_score = 50.0
            performance_score = 50.0
        
        # Construct the response - using the previously calculated savings
        response = {
            "id": f"gen_{int(datetime.now().timestamp())}",
            "success": True,
            "timestamp": int(datetime.now().timestamp()),
            "message": "Analysis completed successfully",
            "responseType": "information" if (info_request or is_yes_no) else "optimization",
            "actionable": actionables,
            "insights": insights,
            "batteryScore": battery_score,
            "dataScore": data_score,
            "performanceScore": performance_score,
            "estimatedSavings": savings
        }
        
        # Store device usage patterns in database
        if not (info_request or is_yes_no):
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
            friendly_message = "Analysis took too long to complete. Please try again with simplified data."
            error_type = "Timeout"
        else:
            friendly_message = f"An error occurred while analyzing your device data: {error_message}"
            error_type = "General"
        
        # Return error response with a general insight
        return {
            "id": f"error_{int(datetime.now().timestamp())}",
            "success": False,
            "timestamp": int(datetime.now().timestamp()),
            "message": "Analysis failed",
            "responseType": "error",
            "actionable": [],
            "insights": [{
                "type": error_type,
                "title": "Error Analyzing Device Data",
                "description": friendly_message,
                "severity": "high"
            }],
            "batteryScore": 50.0,  # Default scores for error cases
            "dataScore": 50.0,
            "performanceScore": 50.0,
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
            
            # Handle dataUsage as a dictionary object
            data_usage_obj = app.get("dataUsage", {})
            # Calculate total data usage by adding foreground and background
            total_data_usage = 0
            if isinstance(data_usage_obj, dict):
                foreground_data = data_usage_obj.get("foreground", 0)
                background_data = data_usage_obj.get("background", 0)
                total_data_usage = foreground_data + background_data
            
            foreground_time = app.get("foregroundTime", 0)
            
            if not package_name:
                continue
            
            # Generate a pattern description based on usage
            pattern = generate_usage_pattern(
                package_name,
                battery_usage,
                total_data_usage,
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
    
    # Battery usage patterns - handle None values for battery_usage
    if battery_usage is not None:
        if battery_usage > 20:
            patterns.append("Very high battery usage")
        elif battery_usage > 10:
            patterns.append("High battery usage")
        elif battery_usage > 5:
            patterns.append("Moderate battery usage")
    
    # Data usage patterns - handle None values for data_usage
    if data_usage is not None:
        if data_usage > 500:
            patterns.append("Very high data usage")
        elif data_usage > 200:
            patterns.append("High data usage")
        elif data_usage > 50:
            patterns.append("Moderate data usage")
    
    # Foreground time patterns - handle None values for foreground_time
    if foreground_time is not None:
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
    """Calculate a battery health score from device data"""
    try:
        battery = device_data.get("battery", {})
        battery_level = battery.get("level", 50)  # Default 50%
        battery_health = battery.get("health", 2)  # Default is 2 (GOOD)
        is_charging = battery.get("isCharging", False)
        temperature = battery.get("temperature", 30)  # Default 30°C
        
        # Settings from device if available
        settings = device_data.get("settings", {})
        power_save_mode = settings.get("powerSaveMode", False) if settings else False
        battery_optimization = settings.get("batteryOptimization", False) if settings else False
        
        # Calculate base score based on battery level and health
        base_score = min(100, battery_level + 40)  # Level-based baseline
        
        # Adjust based on health (health is often an enum: 2=GOOD, lower=worse, higher=better)
        health_adj = 0
        if battery_health < 2:  # POOR, DEAD, etc.
            health_adj = -20
        elif battery_health > 2:  # EXCELLENT, etc.
            health_adj = 10
            
        # Temperature adjustment (penalize for high temperature)
        temp_adj = 0
        if temperature > 40:
            temp_adj = -15
        elif temperature > 35:
            temp_adj = -5
            
        # Settings adjustment
        settings_adj = 0
        if power_save_mode:
            settings_adj += 10
        if battery_optimization:
            settings_adj += 5
            
        # Charging bonus
        charging_adj = 5 if is_charging else 0
        
        # Calculate final score
        score = base_score + health_adj + temp_adj + settings_adj + charging_adj
        
        # Ensure score is between 0-100
        return max(0, min(100, score))
    except Exception as e:
        logger.error(f"Error calculating battery score: {str(e)}")
        return 50  # Default fallback score

def calculate_data_score(device_data: Dict[str, Any]) -> int:
    """Calculate a data usage efficiency score from device data"""
    try:
        network = device_data.get("network", {})
        data_usage = network.get("dataUsage", {})
        background_usage = data_usage.get("background", 0)
        foreground_usage = data_usage.get("foreground", 0)
        network_type = network.get("type", "").lower()
        is_roaming = network.get("isRoaming", False)
        
        # Settings from device if available
        settings = device_data.get("settings", {})
        data_saver = settings.get("dataSaver", False) if settings else False
        auto_sync = settings.get("autoSync", True) if settings else True
        
        # Calculate total data usage and ratio
        total_usage = background_usage + foreground_usage
        
        # Base score starting point
        base_score = 80
        
        # If no data usage, give high score 
        if total_usage == 0:
            return 90
        
        # Adjust for background ratio
        bg_ratio = background_usage / total_usage if total_usage > 0 else 0
        bg_adj = 0
        if bg_ratio > 0.7:
            bg_adj = -20  # High background usage is inefficient
        elif bg_ratio > 0.5:
            bg_adj = -10
        elif bg_ratio < 0.3:
            bg_adj = +10  # Low background usage is efficient
            
        # Network type adjustment
        network_adj = 0
        if network_type == "wifi":
            network_adj = 15  # WiFi is more efficient for data
        elif network_type == "cellular" and is_roaming:
            network_adj = -20  # Roaming is expensive
            
        # Settings adjustment
        settings_adj = 0
        if data_saver:
            settings_adj += 15
        if not auto_sync:
            settings_adj += 5
            
        # Calculate final score
        score = base_score + bg_adj + network_adj + settings_adj
        
        # Ensure score is between 0-100
        return max(0, min(100, score))
    except Exception as e:
        logger.error(f"Error calculating data score: {str(e)}")
        return 50  # Default fallback score

def calculate_performance_score(device_data: Dict[str, Any]) -> int:
    """Calculate a general performance score from device data"""
    try:
        memory = device_data.get("memory", {})
        total_ram = memory.get("totalRam", 0)
        available_ram = memory.get("availableRam", 0)
        low_memory = memory.get("lowMemory", False)
        
        # Get CPU info if available
        cpu = device_data.get("cpu", {})
        cpu_usage = cpu.get("usage")  # This might be None due to -1 values in Android
        
        # Apps info
        apps = device_data.get("apps", [])
        app_count = len(apps)
        crash_count = sum(app.get("crashes", 0) for app in apps)
        
        # Base score
        base_score = 70
        
        # Memory adjustment
        memory_adj = 0
        if total_ram > 0:
            # Calculate free memory percentage
            free_memory_percent = (available_ram / total_ram) * 100 if total_ram > 0 else 0
            
            if free_memory_percent < 15:
                memory_adj = -25
            elif free_memory_percent < 30:
                memory_adj = -15
            elif free_memory_percent > 60:
                memory_adj = +15
                
        # Low memory flag is critical
        if low_memory:
            memory_adj -= 20
            
        # CPU usage adjustment
        cpu_adj = 0
        if cpu_usage is not None:  # Only if we have valid CPU data
            if cpu_usage > 70:
                cpu_adj = -15
            elif cpu_usage < 30:
                cpu_adj = +10
                
        # Crashes adjustment
        crash_adj = 0
        if crash_count > 3:
            crash_adj = -20
        elif crash_count > 0:
            crash_adj = -10
            
        # Calculate final score
        score = base_score + memory_adj + cpu_adj + crash_adj
        
        # Ensure score is between 0-100
        return max(0, min(100, score))
    except Exception as e:
        logger.error(f"Error calculating performance score: {str(e)}")
        return 50  # Default fallback score

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
        sorted_apps = sorted(apps, key=lambda x: float(x.get('batteryUsage', 0) or 0), reverse=True)[:5]
        
        for app in sorted_apps:
            try:
                # Get app name and package name safely
                app_name = app.get('appName', 'Unknown App')
                package_name = app.get('packageName', 'unknown.package')
                
                # Get time values safely and convert to minutes
                foreground_time = float(app.get('foregroundTime', 0)) / 60
                background_time = float(app.get('backgroundTime', 0)) / 60
                
                # Get battery usage safely
                battery_usage = float(app.get('batteryUsage', 0) or 0)
                
                # Get data usage safely
                data_usage = app.get('dataUsage', {})
                if not isinstance(data_usage, dict):
                    data_usage = {}
                foreground_data = float(data_usage.get('foreground', 0) or 0)
                background_data = float(data_usage.get('background', 0) or 0)
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