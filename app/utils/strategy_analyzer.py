"""
Utility module for analyzing and determining optimization strategies.
"""

import re
import logging
from typing import List, Dict, Optional, Any

from app.config.app_categories import (
    APP_CATEGORIES, 
    get_app_name, 
    get_app_category,
    get_apps_in_category
)
from app.config.strategy_config import (
    AGGRESSIVENESS_LEVELS,
    DEFAULT_DAILY_DATA
)

# Configure logging
logger = logging.getLogger('powerguard_strategy')

def determine_strategy(device_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """
    Determine the optimization strategy based on device data and user prompt.
    
    Args:
        device_data: Device usage data
        prompt: User's optimization request
        
    Returns:
        Dictionary containing strategy parameters
    """
    # Default strategy
    strategy = {
        "optimize_battery": False,
        "optimize_data": False,
        "protected_apps": [],
        "time_constraint_minutes": None,
        "aggressiveness": "balanced",
        "critical_apps": [],
        "show_battery_savings": False,
        "show_data_savings": False,
        "focus": "both"  # Default focus is both battery and data
    }
    
    # Get battery level
    battery_level = device_data.get("battery", {}).get("level", 50)
    
    # Determine base aggressiveness based on battery level
    if battery_level <= 10:
        strategy["aggressiveness"] = "very_aggressive"
    elif battery_level <= 30:
        strategy["aggressiveness"] = "aggressive"
    elif battery_level <= 50:
        strategy["aggressiveness"] = "balanced"
    else:
        strategy["aggressiveness"] = "minimal"
    
    # Analyze prompt for protected apps and time constraints
    from app.prompt_analyzer import classify_with_llm
    prompt_analysis = classify_with_llm(prompt)
    
    # Update strategy based on prompt analysis
    strategy["optimize_battery"] = prompt_analysis.get("optimize_battery", False)
    strategy["optimize_data"] = prompt_analysis.get("optimize_data", False)
    strategy["protected_apps"] = prompt_analysis.get("protected_apps", [])
    strategy["time_constraint_minutes"] = prompt_analysis.get("time_constraint_minutes")
    
    # Set which savings to show based on optimization focus
    strategy["show_battery_savings"] = strategy["optimize_battery"]
    strategy["show_data_savings"] = strategy["optimize_data"]
    
    # Set focus based on optimization flags
    if strategy["optimize_battery"] and not strategy["optimize_data"]:
        strategy["focus"] = "battery"
    elif strategy["optimize_data"] and not strategy["optimize_battery"]:
        strategy["focus"] = "data"
    else:
        strategy["focus"] = "both"
    
    # Extract explicitly mentioned apps from prompt
    mentioned_apps = []
    app_patterns = [
        r"(?:keep|need|using|use|watch|stream|open|running)\s+(?:WhatsApp|Gmail|Maps|Netflix|Chrome|Spotify|Facebook|Instagram|YouTube|Messenger|Telegram|Signal|Waze|Outlook|Slack|Teams|Zoom)",
        r"(?:WhatsApp|Gmail|Maps|Netflix|Chrome|Spotify|Facebook|Instagram|YouTube|Messenger|Telegram|Signal|Waze|Outlook|Slack|Teams|Zoom)\s+(?:working|running|active|open)",
        r"I need (?:WhatsApp|Gmail|Maps|Netflix|Chrome|Spotify|Facebook|Instagram|YouTube|Messenger|Telegram|Signal|Waze|Outlook|Slack|Teams|Zoom)",
        r"using (?:WhatsApp|Gmail|Maps|Netflix|Chrome|Spotify|Facebook|Instagram|YouTube|Messenger|Telegram|Signal|Waze|Outlook|Slack|Teams|Zoom)"
    ]
    
    # App name to package name mapping
    app_package_map = {
        "WhatsApp": "com.whatsapp",
        "Gmail": "com.google.android.gm",
        "Maps": "com.google.android.apps.maps",
        "Netflix": "com.netflix.mediaclient",
        "Chrome": "com.android.chrome",
        "Spotify": "com.spotify.music",
        "Facebook": "com.facebook.katana",
        "Instagram": "com.instagram.android",
        "YouTube": "com.google.android.youtube",
        "Messenger": "com.facebook.orca",
        "Telegram": "org.telegram.messenger",
        "Signal": "org.thoughtcrime.securesms",
        "Waze": "com.waze",
        "Outlook": "com.microsoft.office.outlook",
        "Slack": "com.Slack",
        "Teams": "com.microsoft.teams",
        "Zoom": "us.zoom.videomeetings"
    }
    
    for pattern in app_patterns:
        matches = re.finditer(pattern, prompt, re.IGNORECASE)
        for match in matches:
            # Extract the app name from the match
            app_name = None
            if match.groups():
                app_name = match.group(1)
            else:
                # If no groups, split the match and take the last word
                words = match.group(0).split()
                for word in reversed(words):
                    if word in app_package_map:
                        app_name = word
                        break
            
            if app_name:
                package_name = app_package_map.get(app_name)
                if package_name and package_name not in mentioned_apps:
                    mentioned_apps.append(package_name)
                    logger.debug(f"[PowerGuard] Detected app mention: {app_name} -> {package_name}")
    
    # Add mentioned apps to protected and critical apps
    strategy["protected_apps"].extend(mentioned_apps)
    strategy["critical_apps"].extend(mentioned_apps)
    
    # Adjust aggressiveness based on time constraint
    if strategy["time_constraint_minutes"] is not None:
        if strategy["time_constraint_minutes"] <= 60:  # 1 hour or less
            strategy["aggressiveness"] = "very_aggressive"
        elif strategy["time_constraint_minutes"] <= 180:  # 3 hours or less
            strategy["aggressiveness"] = "aggressive"
        elif strategy["time_constraint_minutes"] <= 360:  # 6 hours or less
            strategy["aggressiveness"] = "balanced"
    
    return strategy



def calculate_savings(strategy: Dict[str, Any], critical_apps: List[str]) -> Dict[str, float]:
    """Calculate estimated savings based on strategy"""
    savings = {
        "batteryMinutes": 0.0,
        "dataMB": 0.0
    }
    
    # Calculate battery savings if requested
    if strategy.get("optimize_battery", False):
        savings["batteryMinutes"] = 30.0  # Default value for testing
        
    # Calculate data savings if requested
    if strategy.get("optimize_data", False):
        savings["dataMB"] = 20.0  # Default value for testing
        
    return savings

 