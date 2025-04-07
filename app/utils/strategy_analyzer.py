"""
Utility module for analyzing and determining optimization strategies.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set

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

def determine_strategy(
    device_data: dict,
    prompt: Optional[str] = None,
    optimization_type: Optional[str] = None
) -> dict:
    """
    Determine the optimization strategy based on device data and user prompt.
    
    Args:
        device_data: The device data dictionary
        prompt: Optional user prompt for directed optimization
        optimization_type: Explicit optimization type from UI ("battery" or "network")
        
    Returns:
        Dictionary containing the strategy details
    """
    strategy = {
        "focus": None,              # "battery", "network", or "both"
        "aggressiveness": None,     # "very_aggressive", "aggressive", "moderate", "minimal"
        "critical_apps": [],        # List of critical app package names
        "critical_categories": [],  # List of critical app categories
        "show_battery_savings": False,
        "show_data_savings": False,
        "time_constraint": None,    # Hours
        "data_constraint": None     # MB
    }
    
    # Get battery level
    battery_level = device_data.get("battery", {}).get("level", 100)
    
    # Extract constraints from the prompt
    if prompt:
        time_constraint = extract_time_constraint(prompt)
        data_constraint = extract_data_constraint(prompt)
        critical_categories = extract_critical_categories(prompt)
        
        strategy["time_constraint"] = time_constraint
        strategy["data_constraint"] = data_constraint
        strategy["critical_categories"] = critical_categories
        
        # Log the identified critical categories
        if critical_categories:
            logger.info(f"[PowerGuard] Identified critical categories in prompt: {critical_categories}")
    
    # If no explicit data constraint in prompt, check device data for low data
    if not strategy["data_constraint"] and "network" in device_data:
        device_data_constraint = get_data_constraint_from_device(device_data)
        if device_data_constraint is not None and device_data_constraint < 500:  # Less than 500MB left
            strategy["data_constraint"] = device_data_constraint
            logger.info(f"[PowerGuard] Detected low data from device: {device_data_constraint}MB remaining")
    
    # Determine focus based on optimization_type or prompt
    strategy["focus"] = determine_focus(prompt, optimization_type)
    
    # Determine level of aggressiveness for battery
    battery_level_aggressiveness = get_battery_strategy(battery_level)
    
    # Determine aggressiveness based on time constraint
    time_aggressiveness = determine_time_aggressiveness(strategy["time_constraint"], battery_level)
    
    # Determine aggressiveness based on data constraint
    data_aggressiveness = determine_data_aggressiveness(strategy["data_constraint"])
    
    # Get the overall aggressiveness (most aggressive of all)
    aggressiveness_values = [
        AGGRESSIVENESS_LEVELS[battery_level_aggressiveness]
    ]
    
    if time_aggressiveness:
        aggressiveness_values.append(AGGRESSIVENESS_LEVELS[time_aggressiveness])
    
    if data_aggressiveness:
        aggressiveness_values.append(AGGRESSIVENESS_LEVELS[data_aggressiveness])
    
    max_aggressiveness = max(aggressiveness_values)
    
    # Convert back to string
    for name, level in AGGRESSIVENESS_LEVELS.items():
        if level == max_aggressiveness:
            strategy["aggressiveness"] = name
            break
    
    # Determine which savings to show
    if strategy["focus"] in ["battery", "both"] or battery_level <= 30:
        strategy["show_battery_savings"] = True
    
    if strategy["focus"] in ["network", "both"] or strategy["data_constraint"]:
        strategy["show_data_savings"] = True
    
    # Extract critical apps based on categories
    strategy["critical_apps"] = get_critical_apps(
        strategy["critical_categories"],
        device_data.get("apps", [])
    )
    
    # Check for explicit app mentions in the prompt if no critical apps found yet
    if prompt and not strategy["critical_apps"]:
        # Get all apps from device
        all_device_apps = device_data.get("apps", [])
        available_app_names = {
            get_app_name(app.get("packageName", "")).lower(): app.get("packageName", "")
            for app in all_device_apps
        }
        
        # Look for app names in the prompt
        for app_name, package_name in available_app_names.items():
            if app_name in prompt.lower() and app_name != prompt.lower() and package_name not in strategy["critical_apps"]:
                strategy["critical_apps"].append(package_name)
                logger.info(f"[PowerGuard] Found explicit app mention in prompt: {app_name} ({package_name})")
    
    logger.info(f"[PowerGuard] Final strategy: focus={strategy['focus']}, " +
                f"aggressiveness={strategy['aggressiveness']}, " +
                f"critical_apps={strategy['critical_apps']}")
    
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
    
    if battery_focus and network_focus:
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

def calculate_savings(
    strategy: dict,
    critical_apps: List[str]
) -> dict:
    """
    Calculate estimated savings based on strategy and critical apps.
    
    Args:
        strategy: The optimization strategy
        critical_apps: List of critical app package names
        
    Returns:
        Dictionary with batteryMinutes and dataMB values
    """
    savings = {
        "batteryMinutes": 0,
        "dataMB": 0
    }
    
    num_critical_apps = len(critical_apps)
    
    # Battery savings based on aggressiveness
    if strategy["show_battery_savings"]:
        savings["batteryMinutes"] = get_battery_savings(
            strategy["aggressiveness"],
            num_critical_apps
        )
    
    # Data savings based on aggressiveness
    if strategy["show_data_savings"]:
        savings["dataMB"] = get_data_savings(
            strategy["aggressiveness"],
            num_critical_apps
        )
    
    return savings

# Find where the bug is in data constraint handling
def get_data_constraint_from_device(device_data: dict) -> Optional[float]:
    """Extract data constraint from device data."""
    try:
        # Safe access to network data usage
        network = device_data.get("network", {})
        data_usage = network.get("dataUsage", {})
        
        # Safely get numerical values, with defaults
        total_used = 0
        if isinstance(data_usage, dict):  # Ensure it's a dictionary before accessing
            foreground = data_usage.get("foreground", 0)
            background = data_usage.get("background", 0)
            if isinstance(foreground, (int, float)) and isinstance(background, (int, float)):
                total_used = foreground + background
        
        # Get data limit if it exists
        data_used = network.get("dataUsed", 0)
        if isinstance(data_used, (int, float)) and data_used > 0:
            # Assume 2GB monthly limit if not specified
            monthly_limit = 2000  # 2GB in MB
            data_left = max(0, monthly_limit - data_used)
            return data_left
    except Exception as e:
        logger.error(f"Error extracting data constraint: {str(e)}")
    
    return None 