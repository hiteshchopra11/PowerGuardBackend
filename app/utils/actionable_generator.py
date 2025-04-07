"""
Utility module for generating actionables based on optimization strategies.
"""

import logging
import uuid
from typing import List, Dict, Optional, Set

from app.config.app_categories import get_app_name, get_app_category

# Configure logging
logger = logging.getLogger('powerguard_actionables')

# Define actionable types
ACTIONABLE_TYPES = {
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

def generate_actionables(
    strategy: dict,
    device_data: dict
) -> List[Dict]:
    """
    Generate actionables based on optimization strategy and device data.
    
    Args:
        strategy: The optimization strategy
        device_data: The device data dictionary
        
    Returns:
        List of actionable dictionaries
    """
    apps = device_data.get("apps", [])
    battery_level = device_data.get("battery", {}).get("level", 100)
    actionables = []
    
    # Global optimization actionables based on strategy
    global_actionables = generate_global_actionables(strategy, battery_level)
    actionables.extend(global_actionables)
    
    # App-specific actionables
    app_actionables = generate_app_actionables(
        strategy, 
        apps, 
        device_data
    )
    actionables.extend(app_actionables)
    
    return actionables

def generate_global_actionables(
    strategy: dict,
    battery_level: float
) -> List[Dict]:
    """Generate global actionables based on strategy."""
    actionables = []
    
    # Battery optimization
    if strategy.get("focus") in ["battery", "both"]:
        if battery_level <= 30:
            # Enable battery saver mode for low battery
            actionables.append({
                "id": f"global-batt-{uuid.uuid4().hex[:8]}",
                "type": "ENABLE_BATTERY_SAVER",
                "packageName": "system",
                "description": "Enable battery saver mode",
                "reason": f"Battery level is low ({battery_level}%)",
                "newMode": "enabled",
                "parameters": {}
            })
        
        # Adjust screen settings for battery optimization
        if strategy.get("aggressiveness") in ["very_aggressive", "aggressive"]:
            actionables.append({
                "id": f"global-screen-{uuid.uuid4().hex[:8]}",
                "type": "ADJUST_SCREEN",
                "packageName": "system",
                "description": "Reduce screen brightness and timeout",
                "reason": "Optimize battery usage",
                "newMode": "optimized",
                "parameters": {
                    "brightness": "auto",
                    "timeout": "30"
                }
            })
    
    # Data optimization
    if strategy.get("focus") in ["network", "both"]:
        actionables.append({
            "id": f"global-data-{uuid.uuid4().hex[:8]}",
            "type": "ENABLE_DATA_SAVER",
            "packageName": "system",
            "description": "Enable data saver mode",
            "reason": "Optimize network data usage",
            "newMode": "enabled",
            "parameters": {}
        })
    
    return actionables

def generate_app_actionables(
    strategy: dict,
    apps: List[Dict],
    device_data: dict
) -> List[Dict]:
    """Generate app-specific actionables based on strategy."""
    actionables = []
    critical_apps = set(strategy["critical_apps"])
    
    for app in apps:
        package_name = app.get("packageName", "")
        app_name = get_app_name(package_name)
        battery_usage = app.get("batteryUsage", 0)
        
        # Safely extract data usage values
        data_usage_total = 0
        data_usage_background = 0
        
        data_usage = app.get("dataUsage", {})
        if isinstance(data_usage, dict):
            foreground = data_usage.get("foreground", 0)
            background = data_usage.get("background", 0)
            if isinstance(foreground, (int, float)) and isinstance(background, (int, float)):
                data_usage_total = foreground + background
                data_usage_background = background
        elif isinstance(data_usage, (int, float)):
            data_usage_total = data_usage
        
        # Skip critical apps
        if package_name in critical_apps:
            # For critical apps, ensure they're in normal mode
            actionables.append({
                "id": f"critical-{package_name}-{uuid.uuid4().hex[:8]}",
                "type": "OPTIMIZE_BATTERY", 
                "packageName": package_name,
                "description": f"Set {app_name} to normal priority",
                "reason": "Critical app needed for user's current task",
                "newMode": "normal",
                "parameters": {}
            })
            continue
        
        # For non-critical apps, apply optimizations
        
        # Battery optimizations
        if strategy["focus"] in ["battery", "both"] and battery_usage > 0:
            if strategy["aggressiveness"] in ["very_aggressive", "aggressive"]:
                actionables.append({
                    "id": f"batt-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "RESTRICT_BACKGROUND",
                    "packageName": package_name,
                    "description": f"Restrict background activity for {app_name}",
                    "reason": f"Consuming {battery_usage}% battery in background",
                    "newMode": "restricted",
                    "parameters": {}
                })
            else:
                actionables.append({
                    "id": f"batt-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "OPTIMIZE_BATTERY",
                    "packageName": package_name,
                    "description": f"Optimize battery usage for {app_name}",
                    "reason": f"Consuming {battery_usage}% battery",
                    "newMode": "optimized",
                    "parameters": {}
                })
        
        # Data optimizations
        if strategy["focus"] in ["network", "both"] and data_usage_total > 0:
            if strategy["aggressiveness"] in ["very_aggressive", "aggressive"]:
                actionables.append({
                    "id": f"data-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "RESTRICT_BACKGROUND",
                    "packageName": package_name,
                    "description": f"Restrict background data for {app_name}",
                    "reason": f"Consuming {data_usage_background} MB of data in background",
                    "newMode": "restricted",
                    "parameters": {
                        "restrictData": True
                    }
                })
            else:
                actionables.append({
                    "id": f"data-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "ENABLE_DATA_SAVER",
                    "packageName": package_name,
                    "description": f"Enable data saver for {app_name}",
                    "reason": f"Consuming {data_usage_total} MB of data",
                    "newMode": "enabled",
                    "parameters": {}
                })
    
    return actionables

def is_information_request(prompt: str) -> bool:
    """
    Determine if a prompt is an information request rather than an optimization request.
    
    Args:
        prompt: The user prompt
        
    Returns:
        True if the prompt is an information request, False otherwise
    """
    if not prompt:
        return False
    
    prompt = prompt.lower()
    
    # Direct markers for information requests - these should always return True
    direct_info_markers = [
        "show me", "tell me", "what is", "what are", "which is", "which are",
        "how much", "how many", "list", "display", "report"
    ]
    
    # If prompt directly starts with a known information marker, it's definitely an information request
    for marker in direct_info_markers:
        if prompt.startswith(marker):
            return True
    
    # Check for complete phrases that strongly indicate information requests
    strong_info_phrases = [
        "show me my", "tell me my", "what's using", "what is using",
        "which apps are", "show battery usage", "show data usage", 
        "battery usage for", "data usage for", "usage statistics",
        "show statistics", "display usage", "report on"
    ]
    
    for phrase in strong_info_phrases:
        if phrase in prompt:
            return True
            
    # Check for information request keywords
    info_keywords = [
        "what", "which", "tell me", "show me", "list", "top", "consuming", 
        "draining", "using", "usage", "most", "highest", "how much", "how many",
        "statistics", "stats", "analyze", "information", "info", "details",
        "report", "overview", "summary"
    ]
    
    info_phrases = [
        "what apps are",
        "which apps are",
        "show me apps",
        "tell me which",
        "list apps",
        "top apps",
        "apps using",
        "using the most",
        "what's using",
        "what is using",
        "what are",
        "how much",
        "how many",
        "statistics for",
        "stats for",
        "details on",
        "information about",
        "give me info",
        "find out",
        "analyze my",
        "show stats",
        "report on"
    ]
    
    # Checking for informational question word at the beginning of the prompt
    question_starters = ["what", "which", "how", "who", "where", "when", "why"]
    starts_with_question = any(prompt.startswith(q) for q in question_starters)
    
    # Check for exact phrases
    for phrase in info_phrases:
        if phrase in prompt:
            return True
    
    # Count info keywords
    keyword_count = sum(1 for keyword in info_keywords if keyword in prompt.split())
    
    # Check specifically for "show" + resource patterns 
    show_patterns = [
        r'show\s+(?:my|the)?\s*(?:battery|power|energy|data|network|usage)',
        r'display\s+(?:my|the)?\s*(?:battery|power|energy|data|network|usage)'
    ]
    
    import re
    for pattern in show_patterns:
        if re.search(pattern, prompt):
            return True
    
    # If multiple info keywords are present or it starts with a question word, it's likely an information request
    return keyword_count >= 2 or starts_with_question 