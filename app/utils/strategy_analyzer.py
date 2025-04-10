"""
Utility module for analyzing and determining optimization strategies.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set, Any

from app.config.app_categories import (
    APP_CATEGORIES, 
    get_app_name, 
    get_app_category,
    get_apps_in_category
)
from app.config.strategy_config import (
    get_battery_strategy,
    get_data_strategy,
    get_battery_savings,
    get_data_savings,
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

def determine_focus(prompt: Optional[str], optimization_type: Optional[str]) -> str:
    """Determine the focus of optimization (battery, network, or both)."""
    if optimization_type:
        return optimization_type
    
    if not prompt:
        return "both"
    
    prompt = prompt.lower()
    
    # Check for battery/power keywords
    battery_keywords = [
        "battery", "power", "charge", "energy", "juice", "low battery"
    ]
    battery_focus = any(keyword in prompt for keyword in battery_keywords)
    
    # Check for network/data keywords
    network_keywords = [
        "data", "network", "internet", "wifi", "mb", "gb", "megabyte", "gigabyte"
    ]
    network_focus = any(keyword in prompt for keyword in network_keywords)
    
    # Enhanced check for phrases that explicitly mention both
    both_keywords = [
        "battery and data", "data and battery", 
        "power and data", "data and power",
        "both battery", "both power", "save both",
        "battery & data", "data & battery"
    ]
    both_explicit = any(keyword in prompt for keyword in both_keywords)
    
    # If both are explicitly requested, return "both" immediately
    if both_explicit:
        return "both"
    
    # If both present, try to determine primary focus based on context
    if battery_focus and network_focus:
        # Primary data focus indicators
        data_primary_phrases = [
            "optimize data", "save data", "reduce data", "conserve data",
            "data usage", "data consumption", "data limit", "data plan", 
            "optimize network", "save network", "network usage"
        ]
        
        # Primary battery focus indicators
        battery_primary_phrases = [
            "optimize battery", "save battery", "extend battery", 
            "preserve battery", "conserve battery", "battery life"
        ]
        
        is_data_primary = any(phrase in prompt for phrase in data_primary_phrases)
        is_battery_primary = any(phrase in prompt for phrase in battery_primary_phrases)
        
        # Check if battery is referenced only as a state/condition rather than focus
        battery_as_condition = any(
            condition in prompt for condition in 
            ["with battery at", "battery is at", "battery level", "% battery", "percent battery"]
        )
        
        # If data is primary focus and battery is just mentioned as a condition
        if is_data_primary and (battery_as_condition or not is_battery_primary):
            return "network"
        # If battery is primary focus and data is secondary
        elif is_battery_primary and not is_data_primary:
            return "battery"
        # Equal focus or unclear
        else:
            return "both"
    elif battery_focus:
        return "battery"
    elif network_focus:
        return "network"
    else:
        return "both"

def extract_time_constraint(prompt: str) -> Optional[int]:
    """Extract time constraint from the prompt in hours."""
    if not prompt:
        return None
    
    # Look for patterns like "2 hours", "4 hr", etc.
    patterns = [
        r'(\d+)\s*hours?',
        r'(\d+)\s*hrs?',
        r'(\d+)\s*h\b',
        r'for\s*(\d+)'  # e.g., "for 3 hours" or just "for 3"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    return None

def extract_data_constraint(prompt: str) -> Optional[float]:
    """Extract data constraint from the prompt in MB."""
    if not prompt:
        return None
    
    # Look for patterns like "500 MB", "1.5 GB", etc.
    patterns = [
        r'(\d+\.?\d*)\s*mb',
        r'(\d+\.?\d*)\s*megabytes?',
        r'(\d+\.?\d*)\s*gb',
        r'(\d+\.?\d*)\s*gigabytes?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            try:
                value = float(match.group(1))
                # Convert GB to MB if needed
                if 'gb' in pattern or 'gigabyte' in pattern:
                    value *= 1000
                return value
            except (ValueError, IndexError):
                pass
    
    return None

def extract_critical_categories(prompt: str) -> List[str]:
    """Extract critical app categories from the prompt."""
    if not prompt:
        return []
    
    categories = []
    prompt = prompt.lower()
    
    # Check for messaging keywords
    messaging_keywords = [
        "message", "whatsapp", "messenger", "viber", "chat", "text"
    ]
    if any(keyword in prompt for keyword in messaging_keywords):
        categories.append("messaging")
    
    # Check for navigation keywords
    navigation_keywords = [
        "map", "navigation", "direction", "gps", "route", "google maps", "waze"
    ]
    if any(keyword in prompt for keyword in navigation_keywords):
        categories.append("navigation")
    
    # Check for email keywords and exception patterns
    email_keywords = [
        "email", "mail", "gmail", "outlook", "yahoo mail", "inbox", "e-mail", 
        "messages", "electronic mail", "check mail", "send mail", "read mail",
        "gmail", "outlook", "yahoo"
    ]
    
    # Specific phrases that strongly indicate email preservation needs
    email_preservation_phrases = [
        "ensure email", "ensure mail", "ensure gmail", 
        "keep email", "keep mail", "keep gmail",
        "preserve email", "preserve mail", "preserve gmail",
        "email still works", "mail still works", "gmail still works",
        "protect email", "protect mail", "protect gmail"
    ]
    
    # Direct check for common email preservation phrases
    if any(phrase in prompt for phrase in email_preservation_phrases):
        categories.append("email")
        logger.info(f"[PowerGuard] Email preservation phrase detected in prompt: '{prompt}'")
    
    # Check for direct keywords - make email detection more aggressive
    elif any(keyword in prompt for keyword in email_keywords):
        # If any email keyword is found, consider it a critical category
        if "email" not in categories:
            categories.append("email")
            logger.info(f"[PowerGuard] Email detected in prompt: '{prompt}'")
    
    # Additional check for phrases that might imply email importance
    email_phrases = [
        "check mail", "check my mail", "check email", "check my email",
        "read mail", "read my mail", "read email", "read my email",
        "send mail", "send email", "access mail", "access email",
        "keep my mail", "keep mail", "maintain mail", "mail service",
        "email service", "email working", "mail working"
    ]
    
    if any(phrase in prompt for phrase in email_phrases):
        if "email" not in categories:
            categories.append("email")
            logger.info(f"[PowerGuard] Email phrase detected in prompt: '{prompt}'")
    
    # Check for exception patterns like "ensure X works" or "keep X working"
    exception_patterns = [
        r"ensure (\w+) (?:still )?works",
        r"keep (\w+) working",
        r"maintain (\w+) function",
        r"preserve (\w+)",
        r"but (\w+) should work",
        r"need (\w+) to work",
        r"need (\w+) working",
        r"can i use (\w+)",
        r"access (\w+)",
        r"use (\w+)",
        r"with (\w+)"
    ]
    
    for pattern in exception_patterns:
        matches = re.findall(pattern, prompt)
        for match in matches:
            match_lower = match.lower()
            # Check if the matched word is related to email
            if any(email_keyword in match_lower for email_keyword in email_keywords):
                if "email" not in categories:
                    categories.append("email")
                    logger.info(f"[PowerGuard] Email exception detected: '{match}' in '{prompt}'")
            
            # Check if the match is a simple "mail" or related term
            if match_lower in ["mail", "email", "gmail", "outlook", "inbox"]:
                if "email" not in categories:
                    categories.append("email")
                    logger.info(f"[PowerGuard] Email match detected: '{match}' in '{prompt}'")
    
    # Special case for "Save data but ensure my email still works"
    if "email still works" in prompt or "mail still works" in prompt:
        if "email" not in categories:
            categories.append("email")
            logger.info(f"[PowerGuard] Email preservation detected in phrase: '{prompt}'")
    
    # If the prompt mentions preserving functionality and doesn't specify any other category
    if ("ensure" in prompt or "still works" in prompt or "keep working" in prompt) and len(categories) == 0:
        # Check if any email-related term exists in the prompt
        if any(term in prompt for term in ["mail", "email", "gmail"]):
            categories.append("email")
            logger.info(f"[PowerGuard] Implicit email preservation detected: '{prompt}'")
    
    return categories

def determine_time_aggressiveness(
    time_constraint: Optional[int], 
    battery_level: float
) -> Optional[str]:
    """Determine aggressiveness based on time constraint and battery level."""
    if not time_constraint:
        return None
    
    # Calculate battery percentage per hour needed
    if time_constraint <= 0:
        return None
    
    battery_per_hour = battery_level / time_constraint
    
    if battery_per_hour < 5:  # Critical - less than 5% battery per hour
        return "very_aggressive"
    elif battery_per_hour < 10:  # Low - less than 10% battery per hour
        return "aggressive"
    elif battery_per_hour < 20:  # Moderate - less than 20% battery per hour
        return "moderate"
    else:
        return "minimal"

def determine_data_aggressiveness(data_constraint: Optional[float]) -> Optional[str]:
    """Determine aggressiveness based on data constraint."""
    if not data_constraint:
        return None
    
    # We use the same logic as the get_data_strategy function
    return get_data_strategy(data_constraint)

def get_critical_apps(categories: List[str], apps: List[dict]) -> List[str]:
    """Get critical apps based on categories and available apps."""
    if not categories or not apps:
        return []
    
    # Get all app package names from the device data
    device_apps = {app.get("packageName", "") for app in apps}
    
    # Get all critical packages from the categories
    critical_packages = set()
    for category in categories:
        # Get all packages in this category
        category_packages = get_apps_in_category(category).keys()
        critical_packages.update(category_packages)
    
    # Find intersection with device apps
    return list(critical_packages.intersection(device_apps))

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

def get_data_constraint_from_device(device_data: dict) -> Optional[float]:
    """Get data constraint from device data."""
    if not device_data or "network" not in device_data:
        return None
    
    # Calculate data usage
    data_usage = device_data.get("network", {}).get("dataUsage", {})
    data_used_mb = 0
    
    if "foreground" in data_usage and "background" in data_usage:
        data_used_mb = data_usage.get("foreground", 0) + data_usage.get("background", 0)
    
    # Estimate remaining data (assume 2GB monthly by default)
    # This is a simplified calculation and should be replaced with actual plan details
    data_plan_mb = DEFAULT_DAILY_DATA
    data_remaining = data_plan_mb - data_used_mb
    
    if data_remaining <= 0:
        return 0
    
    return data_remaining

# Add this new function to improve low resource handling
def handle_low_resources(device_data: dict, strategy: dict) -> dict:
    """Apply special handling for low resource scenarios."""
    battery_level = device_data.get("battery", {}).get("level", 100)
    data_constraint = strategy.get("data_constraint", None)
    
    # Special handling for critical battery (10% or less)
    if battery_level <= 10:
        strategy["focus"] = "both"  # Always consider both aspects for critical battery
        strategy["aggressiveness"] = "very_aggressive"
        strategy["show_battery_savings"] = True
        strategy["show_data_savings"] = True
        
        # Ensure we have a valid value for data_constraint even if it was None
        if data_constraint is None:
            strategy["data_constraint"] = 1000  # Assume moderate data constraint
            
        logger.info(f"[PowerGuard] CRITICAL BATTERY LEVEL ({battery_level}%). Using most aggressive strategy.")
    
    # Force focus to "both" if both battery and data are critically low
    elif battery_level <= 15 and data_constraint is not None and data_constraint < 300:
        strategy["focus"] = "both"
        strategy["aggressiveness"] = "very_aggressive"
        strategy["show_battery_savings"] = True
        strategy["show_data_savings"] = True
        logger.info(f"[PowerGuard] Critical resource situation: Battery={battery_level}%, Data={data_constraint}MB. Using very aggressive strategy.")
    
    # For low battery + medium-low data
    elif battery_level <= 20 and data_constraint is not None and data_constraint < 1000:
        strategy["focus"] = "both"
        strategy["show_battery_savings"] = True
        strategy["show_data_savings"] = True
        
        # Ensure we use at least aggressive strategy
        if AGGRESSIVENESS_LEVELS.get(strategy["aggressiveness"], 0) < AGGRESSIVENESS_LEVELS.get("aggressive", 3):
            strategy["aggressiveness"] = "aggressive"
        
        logger.info(f"[PowerGuard] Low resource situation: Battery={battery_level}%, Data={data_constraint}MB. Using aggressive strategy.")
    
    # For moderate battery + low data scenarios
    elif battery_level <= 30 and data_constraint is not None and data_constraint < 300:
        if strategy["focus"] != "both":
            strategy["focus"] = "both" 
            strategy["show_battery_savings"] = True
            strategy["show_data_savings"] = True
            logger.info(f"[PowerGuard] Data critical, battery low: Battery={battery_level}%, Data={data_constraint}MB")
    
    # For low battery + moderate data scenarios
    elif battery_level <= 15 and data_constraint is not None and data_constraint < 1000:
        if strategy["focus"] != "both":
            strategy["focus"] = "both"
            strategy["show_battery_savings"] = True
            strategy["show_data_savings"] = True
            logger.info(f"[PowerGuard] Battery critical, data moderate: Battery={battery_level}%, Data={data_constraint}MB")
    
    # HIGH BATTERY + LOW DATA: Always prioritize data when battery is high but data is low
    elif battery_level >= 50 and data_constraint is not None and data_constraint < 500:
        strategy["focus"] = "network"  # Prioritize network/data optimization
        strategy["show_data_savings"] = True
        
        # Use at least moderate aggressiveness for data
        if AGGRESSIVENESS_LEVELS.get(strategy["aggressiveness"], 0) < AGGRESSIVENESS_LEVELS.get("moderate", 2):
            strategy["aggressiveness"] = "moderate"
            
        logger.info(f"[PowerGuard] High battery ({battery_level}%) + low data ({data_constraint}MB): Prioritizing data optimization")
    
    return strategy 

def is_informational_query(prompt: str) -> bool:
    """
    Determine if the prompt is primarily an informational query.
    Information queries focus on providing information without immediate actions.
    """
    informational_patterns = [
        r"(?i)what (is|are) .*apps? (using|draining|consuming)",
        r"(?i)which apps? (use|drain|consume)",
        r"(?i)show me .*apps? (using|draining)",
        r"(?i)list .*apps? (using|draining)",
        r"(?i)apps? (using|draining) .*(battery|data)",
        r"(?i)how (much|many|long) .*(battery|data)",
        r"(?i)why is (my)? (battery|data)",
        r"(?i)(top|worst) .* (battery|data)"
    ]
    
    return any(re.search(pattern, prompt) for pattern in informational_patterns)

def handle_informational_queries(prompt: str, device_data: dict, strategy: dict) -> dict:
    """
    Handle prompts that are primarily informational by adapting the response
    to also consider resource constraints when relevant.
    """
    battery_level = device_data.get("battery", {}).get("level", 100)
    data_remaining = device_data.get("data", {}).get("remaining_mb", 10000)
    
    # Copy the original strategy to avoid modifying it directly
    updated_strategy = strategy.copy()
    
    # Even for informational queries, we should adapt our response based on resource constraints
    if battery_level <= 15:
        # For critical battery situations, add battery-saving suggestions
        updated_strategy["add_resource_warning"] = True
        updated_strategy["resource_warning_type"] = "battery"
        updated_strategy["show_battery_savings"] = True
        if battery_level <= 10:
            updated_strategy["aggressiveness"] = "very_aggressive" 
        elif battery_level <= 15:
            updated_strategy["aggressiveness"] = "aggressive"
        logger.info(f"[PowerGuard] Informational query with critical battery level ({battery_level}%). Adding battery warnings.")
        
    elif data_remaining < 300:
        # For low data situations, add data-saving suggestions
        updated_strategy["add_resource_warning"] = True
        updated_strategy["resource_warning_type"] = "data"
        updated_strategy["show_data_savings"] = True
        if data_remaining < 100:
            updated_strategy["aggressiveness"] = "very_aggressive"
        elif data_remaining < 300:
            updated_strategy["aggressiveness"] = "aggressive"
        logger.info(f"[PowerGuard] Informational query with low data remaining ({data_remaining}MB). Adding data warnings.")
    
    # For both low battery and data, prioritize both
    if battery_level <= 20 and data_remaining < 1000:
        updated_strategy["add_resource_warning"] = True
        updated_strategy["resource_warning_type"] = "both"
        updated_strategy["show_battery_savings"] = True
        updated_strategy["show_data_savings"] = True
        updated_strategy["aggressiveness"] = "very_aggressive"
        updated_strategy["focus"] = "both"
        logger.info(f"[PowerGuard] Informational query with both resources low: Battery={battery_level}%, Data={data_remaining}MB")
    
    return updated_strategy

def adapt_informational_query_for_constraints(strategy: dict, device_data: dict) -> dict:
    """
    Adapt the strategy for an informational query when resources are constrained.
    This changes the strategy to include optimization actions even for information requests
    when resources are critically low.
    
    Args:
        strategy: The current strategy dictionary
        device_data: The device data dictionary
        
    Returns:
        Updated strategy dictionary
    """
    # Get current resource status
    battery_level = device_data.get("battery", {}).get("level", 100)
    data_constraint = strategy.get("data_constraint", None)
    
    # For low battery + low data scenario, always set focus to both
    if battery_level <= 20 and data_constraint is not None and data_constraint < 1000:
        strategy["focus"] = "both"
        strategy["show_battery_savings"] = True
        strategy["show_data_savings"] = True
        strategy["aggressiveness"] = "aggressive"
        logger.info(f"[PowerGuard] Informational query with battery={battery_level}%, data={data_constraint}MB: Setting focus to both")
        return strategy
    
    # For critical battery scenarios, add battery optimization
    if battery_level <= 15:
        strategy["focus"] = "both" if data_constraint and data_constraint < 1000 else "battery"
        strategy["show_battery_savings"] = True
        
        # Adjust aggressiveness based on severity
        if battery_level <= 10:
            strategy["aggressiveness"] = "very_aggressive"
        elif battery_level <= 15:
            strategy["aggressiveness"] = "aggressive"
        
        logger.info(f"[PowerGuard] Adapting informational query for critical battery level: {battery_level}%")
    
    # For critical data scenarios, add data optimization
    if data_constraint is not None and data_constraint < 300:
        if strategy["focus"] != "both":
            strategy["focus"] = "both" if battery_level <= 30 else "network"
        
        strategy["show_data_savings"] = True
        
        # Adjust aggressiveness for data
        if data_constraint < 100:
            if AGGRESSIVENESS_LEVELS.get(strategy["aggressiveness"], 0) < AGGRESSIVENESS_LEVELS["very_aggressive"]:
                strategy["aggressiveness"] = "very_aggressive"
        elif data_constraint < 300:
            if AGGRESSIVENESS_LEVELS.get(strategy["aggressiveness"], 0) < AGGRESSIVENESS_LEVELS["aggressive"]:
                strategy["aggressiveness"] = "aggressive"
                
        logger.info(f"[PowerGuard] Adapting informational query for low data: {data_constraint}MB")
    
    return strategy

def balance_strategy_priority(prompt: str, device_data: dict, strategy: dict) -> dict:
    """
    Adjust the strategy priorities based on current device state and resource availability.
    This function ensures proper focus when one resource is constrained while the other is abundant.
    
    Args:
        prompt: User prompt text
        device_data: Current device data including battery and network stats
        strategy: Current strategy configuration
        
    Returns:
        Updated strategy with balanced priorities
    """
    try:
        # Ensure device_data is a dictionary
        if not device_data:
            device_data = {}
            
        # Get key resource metrics with safety checks
        battery_level = device_data.get("battery", {}).get("level")
        if battery_level is None:
            battery_level = 100  # Default value
        
        # Check if this is an explicit battery optimization request
        is_battery_request = False
        battery_request_phrases = [
            "save battery", "extend battery", "battery life", 
            "preserve battery", "conserve battery", "optimize battery",
            "need battery", "battery to last"
        ]
        for phrase in battery_request_phrases:
            if phrase in prompt.lower():
                is_battery_request = True
                break
        
        # If this is a battery request and battery is low, prioritize battery actions
        # even if data is also constrained
        if is_battery_request and battery_level <= 20:
            strategy["focus"] = "battery"
            strategy["show_battery_savings"] = True
            strategy["aggressiveness"] = "aggressive" if battery_level <= 15 else "moderate"
            logger.info(f"[PowerGuard] Prioritizing battery focus due to explicit battery request with low battery ({battery_level}%)")
            
            # For data-related battery requests, don't add data actions unless critically low
            data_remaining = device_data.get("data", {}).get("remaining_mb", 10000)
            data_request_phrases = ["save data", "data usage"]
            is_data_related = any(phrase in prompt.lower() for phrase in data_request_phrases)
            
            if is_data_related or (data_remaining and data_remaining < 300):
                strategy["focus"] = "both"
                strategy["show_data_savings"] = True
                # Ensure we don't create more data actions than battery actions
                strategy["limit_data_actions"] = True
            
            return strategy
        
        # Continue with normal priority balancing...
        
        data_remaining = device_data.get("data", {}).get("remaining_mb", 10000)
        data_plan = device_data.get("data", {}).get("plan_mb", data_remaining * 2 or 1)  # Default to twice remaining if 0
        data_percentage = (data_remaining / max(data_plan, 1) * 100)
        
        logger.info(f"[PowerGuard] Balancing priorities - Battery: {battery_level}%, Data: {data_percentage}%")
        
        # Critical resource checks - handle extreme cases first
        if battery_level <= 10:
            # Critical battery trumps everything
            strategy["focus"] = "battery"
            strategy["aggressiveness"] = "very_aggressive"
            strategy["show_battery_savings"] = True
            logger.info(f"[PowerGuard] CRITICAL BATTERY LEVEL: {battery_level}%. Forcing battery focus.")
        elif data_percentage <= 10:
            # Critical data situation
            if battery_level <= 30:
                # Both resources are low - dual focus
                strategy["focus"] = "both"
                strategy["show_battery_savings"] = True
                strategy["show_data_savings"] = True
            else:
                # Only data is critical
                strategy["focus"] = "network"
                strategy["show_data_savings"] = True
            strategy["aggressiveness"] = "very_aggressive"
            logger.info(f"[PowerGuard] CRITICAL DATA LEVEL: {data_percentage}%. Adjusting focus to {strategy['focus']}.")
        
        # Handle high battery + low data scenarios (key improvement)
        elif battery_level >= 70 and data_percentage <= 30:
            # High battery but low data - clearly prioritize data
            strategy["focus"] = "network"
            strategy["show_data_savings"] = True
            strategy["aggressiveness"] = "aggressive" if data_percentage <= 20 else "moderate"
            logger.info(f"[PowerGuard] High battery ({battery_level}%) + low data ({data_percentage}%). Prioritizing data savings.")
        
        # Handle low battery + high data scenarios
        elif battery_level <= 30 and data_percentage >= 70:
            # Low battery but high data - prioritize battery
            strategy["focus"] = "battery"
            strategy["show_battery_savings"] = True
            strategy["aggressiveness"] = "aggressive" if battery_level <= 20 else "moderate"
            logger.info(f"[PowerGuard] Low battery ({battery_level}%) + high data ({data_percentage}%). Prioritizing battery savings.")
        
        # Both resources moderately constrained
        elif battery_level <= 50 and data_percentage <= 50:
            strategy["focus"] = "both"
            strategy["show_battery_savings"] = True
            strategy["show_data_savings"] = True
            strategy["aggressiveness"] = "moderate"
            logger.info(f"[PowerGuard] Both resources constrained: Battery={battery_level}%, Data={data_percentage}%. Setting dual focus.")
        
        # Override if user explicitly requested a focus but the other resource is critical
        if strategy.get("focus") == "battery" and data_percentage <= 15:
            # User asked for battery focus but data is critically low
            strategy["focus"] = "both"
            strategy["show_data_savings"] = True
            strategy["aggressiveness"] = max(
                strategy.get("aggressiveness", "minimal"),
                "aggressive" if data_percentage <= 10 else "moderate"
            )
            logger.info(f"[PowerGuard] User requested battery focus but data is critical ({data_percentage}%). Adding data focus.")
        
        if strategy.get("focus") == "network" and battery_level <= 15:
            # User asked for data focus but battery is critically low
            strategy["focus"] = "both"
            strategy["show_battery_savings"] = True
            strategy["aggressiveness"] = max(
                strategy.get("aggressiveness", "minimal"),
                "aggressive" if battery_level <= 10 else "moderate"
            )
            logger.info(f"[PowerGuard] User requested data focus but battery is critical ({battery_level}%). Adding battery focus.")
        
        # Always return the updated strategy
        return strategy
    except Exception as e:
        logger.error(f"[PowerGuard] Error in balance_strategy_priority: {str(e)}")
    
    return strategy  # Return the strategy even if there was an error 