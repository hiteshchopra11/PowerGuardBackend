"""
Utility module for generating actionables based on optimization strategies.
"""

import logging
import uuid
from typing import List, Dict, Optional, Set

from app.config.app_categories import get_app_name

# Configure logging
logger = logging.getLogger('powerguard_actionables')

# Define actionable types - using string values
ACTIONABLE_TYPES = {
    "SET_STANDBY_BUCKET",
    "RESTRICT_BACKGROUND_DATA",
    "KILL_APP", 
    "MANAGE_WAKE_LOCKS",
    "THROTTLE_CPU_USAGE"
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
    
    # Post-process actionables to ensure human-readable app names in descriptions
    actionables = post_process_actionables(actionables)
    
    return actionables

def post_process_actionables(actionables: List[Dict]) -> List[Dict]:
    """
    Post-process actionables to ensure human-readable app names in descriptions.
    
    Args:
        actionables: List of actionable dictionaries
        
    Returns:
        List of actionables with human-readable app names in descriptions
    """
    processed_actionables = []
    
    for actionable in actionables:
        # Skip if no package name
        if not actionable.get("packageName"):
            processed_actionables.append(actionable)
            continue
            
        package_name = actionable.get("packageName")
        description = actionable.get("description", "")
        
        # Skip system-level actionables or ones without descriptions
        if package_name == "system" or not description:
            processed_actionables.append(actionable)
            continue
            
        # Get human-readable app name
        app_name = get_app_name(package_name)
        
        # Skip if app name is same as package name (no mapping found)
        if app_name == package_name:
            processed_actionables.append(actionable)
            continue
            
        # Replace package name with app name in description
        if package_name in description:
            # Make a more direct replacement to ensure we catch all instances
            new_description = description.replace(package_name, app_name)
            logger.debug(f"Replaced '{package_name}' with '{app_name}' in description: '{description}' -> '{new_description}'")
            actionable["description"] = new_description
        
        processed_actionables.append(actionable)
        
    return processed_actionables

def generate_global_actionables(
    strategy: dict,
    battery_level: float
) -> List[Dict]:
    """Generate global actionables based on strategy."""
    actionables = []
    
    # Battery optimization
    if strategy.get("focus", "battery") in ["battery", "both"]:
        if battery_level <= 30:
            # Use MANAGE_WAKE_LOCKS for low battery
            actionables.append({
                "id": f"global-batt-{uuid.uuid4().hex[:8]}",
                "type": "MANAGE_WAKE_LOCKS",
                "packageName": "system",
                "description": "Manage system wake locks",
                "reason": f"Battery level is low ({battery_level}%)",
                "newMode": "enabled",
                "parameters": {}
            })
        
        # Use CPU throttling for aggressive battery saving
        if strategy.get("aggressiveness") in ["very_aggressive", "aggressive"]:
            actionables.append({
                "id": f"global-cpu-{uuid.uuid4().hex[:8]}",
                "type": "THROTTLE_CPU_USAGE",
                "packageName": "system",
                "description": "Throttle CPU usage for background apps",
                "reason": "Optimize battery usage",
                "newMode": "optimized",
                "parameters": {
                    "throttleLevel": "medium"
                }
            })
    
    # Data optimization
    if strategy.get("focus", "battery") in ["network", "both"]:
        actionables.append({
            "id": f"global-data-{uuid.uuid4().hex[:8]}",
            "type": "RESTRICT_BACKGROUND_DATA",
            "packageName": "system",
            "description": "Restrict background data usage",
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
    critical_apps = set(strategy.get("critical_apps", []))
    
    # Get current device conditions
    battery_level = device_data.get("battery", {}).get("level", 100)
    data_usage = device_data.get("network", {}).get("dataUsage", {})
    
    # Check if we should limit data actions to be fewer than battery actions
    limit_data_actions = strategy.get("limit_data_actions", False)
    
    # Calculate total data usage
    foreground_data = data_usage.get("foreground", 0)
    background_data = data_usage.get("background", 0)
    total_data_used = foreground_data + background_data
    
    # Assume 3GB plan for estimation
    total_data_plan = 3000
    data_remaining = max(0, total_data_plan - total_data_used)
    
    # Determine criticality of resources
    battery_critical = battery_level <= 20
    data_critical = data_remaining <= 100
    
    # Create a prioritized list of apps based on resource usage
    if strategy["focus"] == "battery" or (strategy["focus"] == "both" and battery_critical and not data_critical):
        # Prioritize battery optimization
        sorted_apps = sorted(apps, key=lambda x: float(x.get("batteryUsage", 0) or 0), reverse=True)
    elif strategy["focus"] == "network" or (strategy["focus"] == "both" and data_critical and not battery_critical):
        # Prioritize data optimization
        sorted_apps = sorted(apps, key=lambda x: float(
            x.get("dataUsage", {}).get("foreground", 0) + x.get("dataUsage", {}).get("background", 0) 
            if isinstance(x.get("dataUsage", {}), dict) else float(x.get("dataUsage", 0) or 0)
        ), reverse=True)
    else:
        # Balanced approach - consider both
        sorted_apps = sorted(apps, key=lambda x: (
            float(x.get("batteryUsage", 0) or 0) + 
            float(x.get("dataUsage", {}).get("foreground", 0) + x.get("dataUsage", {}).get("background", 0) 
                if isinstance(x.get("dataUsage", {}), dict) else float(x.get("dataUsage", 0) or 0))
        ), reverse=True)
    
    # Track battery and data action counts when limiting
    battery_action_count = 0
    data_action_count = 0
    
    for app in sorted_apps:
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
                "type": "SET_STANDBY_BUCKET",
                "packageName": package_name,
                "description": f"Set {app_name} to normal priority",
                "reason": "Critical app needed for user's current task",
                "newMode": "normal",
                "parameters": {}
            })
            continue
        
        # Add appropriate battery actions based on conditions
        if (strategy["focus"] in ["battery", "both"] and (battery_usage or 0) > 0):
            if battery_critical:
                # If battery is critically low, apply more aggressive actions
                if battery_usage > 10:
                    # Kill high battery consuming apps
                    actionables.append({
                        "id": f"batt-{package_name}-{uuid.uuid4().hex[:8]}",
                        "type": "KILL_APP",
                        "packageName": package_name,
                        "description": f"Force stop {app_name}",
                        "reason": f"Battery critically low ({battery_level}%), app uses {battery_usage}% battery",
                        "newMode": "killed",
                        "parameters": {}
                    })
                else:
                    # Use wake lock management for moderate consumers
                    actionables.append({
                        "id": f"batt-save-{package_name}-{uuid.uuid4().hex[:8]}",
                        "type": "MANAGE_WAKE_LOCKS",
                        "packageName": package_name,
                        "description": f"Manage wake locks for {app_name}",
                        "reason": f"Battery low ({battery_level}%) with moderate usage ({battery_usage}%)",
                        "newMode": "restricted",
                        "parameters": {}
                    })
            elif strategy["aggressiveness"] in ["very_aggressive", "aggressive"]:
                actionables.append({
                    "id": f"batt-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "THROTTLE_CPU_USAGE",
                    "packageName": package_name,
                    "description": f"Throttle CPU usage for {app_name}",
                    "reason": f"Consuming {battery_usage}% battery, aggressive optimization strategy",
                    "newMode": "throttled",
                    "parameters": {
                        "level": "moderate"
                    }
                })
            else:
                actionables.append({
                    "id": f"batt-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "SET_STANDBY_BUCKET",
                    "packageName": package_name,
                    "description": f"Place {app_name} in restricted standby bucket",
                    "reason": f"Consuming {battery_usage}% battery in background",
                    "newMode": "restricted",
                    "parameters": {}
                })
            battery_action_count += 1
        
        # Add appropriate data actions based on conditions
        if (strategy["focus"] in ["network", "both"] and data_usage_total is not None and data_usage_total > 0):
            # Skip if we're limiting data actions and already have at least as many as battery actions
            if limit_data_actions and data_action_count >= battery_action_count:
                continue
            
            if data_critical:
                # If data is critically low, apply more aggressive actions
                if data_usage_total > total_data_used * 0.1:  # Using more than 10% of total data
                    actionables.append({
                        "id": f"data-{package_name}-{uuid.uuid4().hex[:8]}",
                        "type": "KILL_APP",
                        "packageName": package_name,
                        "description": f"Force stop {app_name} to prevent data usage",
                        "reason": f"Data critically low ({data_remaining} MB), app uses significant data ({data_usage_total} MB)",
                        "newMode": "killed",
                        "parameters": {}
                    })
                else:
                    actionables.append({
                        "id": f"data-save-{package_name}-{uuid.uuid4().hex[:8]}",
                        "type": "RESTRICT_BACKGROUND_DATA",
                        "packageName": package_name,
                        "description": f"Restrict background data for {app_name}",
                        "reason": f"Data critically low ({data_remaining} MB), preserve for essential use",
                        "newMode": "restricted",
                        "parameters": {}
                    })
                data_action_count += 1
            elif strategy["aggressiveness"] in ["very_aggressive", "aggressive"]:
                actionables.append({
                    "id": f"data-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "RESTRICT_BACKGROUND_DATA",
                    "packageName": package_name,
                    "description": f"Restrict background data for {app_name}",
                    "reason": f"Consuming {data_usage_background} MB of data in background",
                    "newMode": "restricted",
                    "parameters": {}
                })
            else:
                actionables.append({
                    "id": f"data-{package_name}-{uuid.uuid4().hex[:8]}",
                    "type": "SET_STANDBY_BUCKET",
                    "packageName": package_name,
                    "description": f"Place {app_name} in restricted standby bucket",
                    "reason": f"Optimize data usage by limiting background activity",
                    "newMode": "restricted",
                    "parameters": {}
                })
                data_action_count += 1
    
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
    
    # First check for optimization indicators even if in question format
    optimization_indicators = [
        "optimize", "save", "reduce", "conserve", "limit", "minimize", 
        "decrease", "cut down", "lower", "how can i use less", "how to save", 
        "how to reduce", "how to conserve", "how to limit", "how to minimize",
        "ways to reduce", "ways to save", "tips to save"
    ]
    
    # If the prompt contains clear optimization indicators, it's not an information request
    for indicator in optimization_indicators:
        if indicator in prompt:
            return False
    
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
    # Only consider 'how' as informational if not followed by optimization indicators
    question_starters = ["what", "which", "who", "where", "when", "why"]
    
    # Special handling for "how" - it can be both information and optimization
    if prompt.startswith("how"):
        # If "how" is followed by optimization indicators, it's not an information request
        if any(f"how {word}" in prompt or f"how to {word}" in prompt for word in ["save", "reduce", "optimize", "conserve", "minimize"]):
            return False
        # If "how" is followed by typical info patterns, it's an information request
        if any(f"how {word}" in prompt for word in ["much", "many", "often", "long"]):
            return True
    
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