"""
Utility module for generating insights based on optimization strategies.
"""

import logging
from typing import List, Dict, Optional
import re

from app.config.app_categories import get_app_name
from app.utils.strategy_analyzer import calculate_savings

# Configure logging
logger = logging.getLogger('powerguard_insights')

def generate_insights(
    strategy: dict,
    device_data: dict,
    is_information_request: bool = False,
    prompt: Optional[str] = None
) -> List[Dict]:
    """
    Generate insights based on device data and strategy.
    
    Args:
        strategy: The determined strategy
        device_data: The device data dictionary
        is_information_request: Whether this is an informational request
        prompt: Original user prompt
        
    Returns:
        List of insights
    """
    insights = []
    
    # Special case: handle direct questions (yes/no, etc.)
    if prompt:
        direct_answer = analyze_yes_no_question(prompt, strategy, device_data)
        if direct_answer:
            return [direct_answer]
    
    # Generate regular insights based on request type
    if is_information_request:
        insights.extend(generate_information_insights(prompt, device_data))
    else:
        insights.extend(generate_optimization_insights(strategy, device_data))
        
    return insights

def generate_optimization_insights(strategy: dict, device_data: dict) -> List[Dict]:
    """Generate insights for optimization requests."""
    insights = []
    battery_level = device_data.get("battery", {}).get("level", 100)
    
    # Use pre-calculated savings if available, otherwise calculate them now
    if "calculated_savings" in strategy:
        savings = strategy["calculated_savings"]
    else:
        # Fallback if not pre-calculated (shouldn't happen with new code)
        savings = calculate_savings(strategy, strategy.get("critical_apps", []))
    
    # Main strategy insight
    description_focus = "battery" if strategy.get('optimize_battery', False) else "data" if strategy.get('optimize_data', False) else "resource"
    main_insight = {
        "type": "Strategy",
        "title": f"Designed a custom {description_focus} strategy for you",
        "description": generate_strategy_description(strategy, battery_level, savings),
        "severity": "info"
    }
    insights.append(main_insight)
    
    # Battery level insight if critically low
    if battery_level <= 10:
        insights.append({
            "type": "BatteryWarning",
            "title": "Critical Battery Level",
            "description": f"Battery level is critically low at {battery_level}%. Taking aggressive measures to extend battery life.",
            "severity": "high"
        })
    elif battery_level <= 30:
        insights.append({
            "type": "BatteryWarning",
            "title": "Low Battery Level",
            "description": f"Battery level is low at {battery_level}%. Optimizing usage to extend battery life.",
            "severity": "medium"
        })
    
    # Data constraint insight
    data_constraint = strategy.get("data_constraint")
    if data_constraint:
        insights.append({
            "type": "DataWarning",
            "title": "Limited Data Remaining",
            "description": f"You have {data_constraint}MB of data remaining. Restricting background data usage to conserve data.",
            "severity": "medium"
        })
    
    # Time constraint insight
    time_constraint = strategy.get("time_constraint")
    if time_constraint:
        insights.append({
            "type": "TimeConstraint",
            "title": f"Optimized for {time_constraint} Hour{'s' if time_constraint > 1 else ''} Usage",
            "description": f"Adjusting power management to ensure device lasts for {time_constraint} hour{'s' if time_constraint > 1 else ''}.",
            "severity": "info"
        })
    
    # Critical apps insight
    critical_apps = strategy.get("critical_apps", [])
    if critical_apps:
        app_names = [get_app_name(app) for app in critical_apps]
        insights.append({
            "type": "CriticalApps",
            "title": "Protected Critical Apps",
            "description": f"Maintaining full functionality for: {', '.join(app_names)}",
            "severity": "info"
        })
    
    # Get app names for managed apps
    all_apps = device_data.get("apps", [])
    app_name_map = {app.get("packageName", ""): app.get("appName", "Unknown App") for app in all_apps}
    
    # Add savings insights using the same consistent values
    if strategy.get("show_battery_savings", False) and savings["batteryMinutes"] > 0:
        # Get names of apps being optimized for battery
        battery_optimized_apps = []
        for app in all_apps:
            battery_usage = app.get("batteryUsage")
            if battery_usage is not None:
                try:
                    battery_usage_float = float(battery_usage)
                    if battery_usage_float > 10 and app.get("packageName") not in strategy["critical_apps"]:
                        battery_optimized_apps.append(app.get("appName", "Unknown App"))
                except (ValueError, TypeError):
                    logger.debug(f"[PowerGuard] Invalid battery usage value for app {app.get('appName', 'Unknown App')}: {battery_usage}")
                    continue
        
        battery_insight = {
            "type": "BatterySavings",
            "title": "Extended Battery Life",
            "description": f"Estimated battery extension: {savings['batteryMinutes']} minutes",
            "severity": "info"
        }
        
        # Add optimized apps if available
        if battery_optimized_apps:
            top_apps = battery_optimized_apps[:3]  # Limit to top 3 for readability
            if len(battery_optimized_apps) > 3:
                battery_insight["description"] += f"\nOptimizing battery usage for: {', '.join(top_apps)}, and {len(battery_optimized_apps) - 3} more apps."
            else:
                battery_insight["description"] += f"\nOptimizing battery usage for: {', '.join(top_apps)}."
        
        insights.append(battery_insight)
    
    if strategy.get("show_data_savings", False) and savings["dataMB"] > 0:
        # Get names of apps being optimized for data
        data_optimized_apps = []
        for app in all_apps:
            try:
                data_usage = app.get("dataUsage", {})
                total_data = 0
                
                if isinstance(data_usage, dict):
                    foreground = float(data_usage.get("foreground", 0) or 0)
                    background = float(data_usage.get("background", 0) or 0)
                    total_data = foreground + background
                elif isinstance(data_usage, (int, float)):
                    total_data = float(data_usage)
                
                if total_data > 50 and app.get("packageName") not in strategy["critical_apps"]:
                    data_optimized_apps.append(app.get("appName", "Unknown App"))
            except (ValueError, TypeError):
                logger.debug(f"[PowerGuard] Invalid data usage value for app {app.get('appName', 'Unknown App')}: {data_usage}")
                continue
        
        data_insight = {
            "type": "DataSavings",
            "title": "Reduced Data Usage",
            "description": f"Estimated data savings: {savings['dataMB']} MB",
            "severity": "info"
        }
        
        # Add optimized apps if available
        if data_optimized_apps:
            top_apps = data_optimized_apps[:3]  # Limit to top 3 for readability
            if len(data_optimized_apps) > 3:
                data_insight["description"] += f"\nOptimizing data usage for: {', '.join(top_apps)}, and {len(data_optimized_apps) - 3} more apps."
            else:
                data_insight["description"] += f"\nOptimizing data usage for: {', '.join(top_apps)}."
        
        insights.append(data_insight)
    
    return insights

def generate_information_insights(prompt: str, device_data: dict) -> List[Dict]:
    """Generate insights for information queries."""
    insights = []
    
    # Extract app count from prompt if specified
    app_count = 3  # default
    if "top" in prompt.lower() and any(str(i) in prompt for i in range(1, 10)):
        for i in range(1, 10):
            if str(i) in prompt:
                app_count = i
                break
    
    # Check if query is about battery or data
    is_battery_query = any(word in prompt.lower() for word in ["battery", "power", "charge"])
    is_data_query = any(word in prompt.lower() for word in ["data", "internet", "network"])
    
    if is_battery_query:
        top_apps = get_top_consuming_apps(device_data, "battery", app_count)
        if all(app.get("is_default", False) for app in top_apps):
            insights.append({
                "type": "BatteryUsage",
                "title": "Battery Usage Information",
                "description": "No significant battery usage detected for any apps. All apps are currently using 0% battery.",
                "severity": "info"
            })
        else:
            app_list = "\n".join([f"- {app['name']}: {app['usage']}%" for app in top_apps])
            insights.append({
                "type": "BatteryUsage",
                "title": f"Top {app_count} Battery Consuming Apps",
                "description": f"The following apps are consuming the most battery:\n{app_list}",
                "severity": "info"
            })
    
    if is_data_query:
        top_apps = get_top_consuming_apps(device_data, "data", app_count)
        if all(app.get("is_default", False) for app in top_apps):
            insights.append({
                "type": "DataUsage",
                "title": "Data Usage Information",
                "description": "No significant data usage detected for any apps. All apps are currently using 0 MB of data.",
                "severity": "info"
            })
        else:
            app_list = "\n".join([f"- {app['name']}: {app['usage'] / (1024 * 1024):.1f} MB" for app in top_apps])
            insights.append({
                "type": "DataUsage",
                "title": f"Top {app_count} Data Consuming Apps",
                "description": f"The following apps are consuming the most data:\n{app_list}",
                "severity": "info"
            })
    
    return insights

def generate_strategy_description(strategy: dict, battery_level: float, savings: dict = None) -> str:
    """Generate a human-readable description of the strategy."""
    lines = []
    
    # Determine primary focus
    is_data_focused = strategy.get("optimize_data", False)
    
    # Context based on focus
    if is_data_focused:
        # For data-focused strategies, prioritize data information
        data_constraint = strategy.get("data_constraint")
        if data_constraint:
            lines.append(f"Optimizing data usage with {data_constraint}MB remaining")
        else:
            lines.append("Optimizing data consumption for your device")
    else:
        # For battery-focused strategies, show battery context
        if battery_level <= 10:
            lines.append(f"As battery is critically low ({battery_level}%), taking aggressive measures")
        elif battery_level <= 30:
            lines.append(f"As battery is low ({battery_level}%), optimizing usage")
        elif battery_level > 80:
            lines.append(f"As battery is sufficient ({battery_level}%), taking minimal measures")
    
    # Add actionable descriptions based on strategy - avoid duplicating information from other insights
    if strategy.get("aggressiveness", "") in ["very_aggressive", "aggressive"]:
        lines.append("Restricted background activity for non-critical apps")
        
        if strategy.get("optimize_data", False) and not strategy.get("data_constraint"):
            lines.append("Limited background data usage")
        
        if strategy.get("optimize_battery", False) and battery_level > 30 and not is_data_focused:
            lines.append("Applied aggressive battery optimization")
    else:
        lines.append("Applied moderate optimization for non-critical apps")
    
    # If savings not provided, check for pre-calculated savings in strategy
    if savings is None:
        if "calculated_savings" in strategy:
            savings = strategy.get("calculated_savings", {})
        else:
            # Last resort: calculate if nothing else is available
            savings = calculate_savings(strategy, strategy.get("critical_apps", []))
    
    return "\n".join(lines)

def get_top_consuming_apps(device_data: dict, resource_type: str = "battery", count: int = 3) -> List[dict]:
    """Get top consuming apps for either battery or data resources."""
    apps = device_data.get("apps", [])
    valid_apps = []
    
    for app in apps:
        if resource_type == "battery":
            usage = app.get("batteryUsage")
            if usage is not None and usage > 0.0:
                valid_apps.append({
                    "name": app.get("appName", "Unknown"),
                    "usage": usage,
                    "is_default": False
                })
        else:  # data usage
            data_usage = app.get("dataUsage", {})
            total_bytes = data_usage.get("rxBytes", 0.0) + data_usage.get("txBytes", 0.0)
            if total_bytes > 0.0:
                valid_apps.append({
                    "name": app.get("appName", "Unknown"),
                    "usage": total_bytes,
                    "is_default": False
                })
    
    # Sort by usage in descending order
    valid_apps.sort(key=lambda x: x["usage"], reverse=True)
    
    # If no valid apps found, return default apps with 0% usage
    if not valid_apps:
        default_apps = []
        for app in apps[:count]:
            default_apps.append({
                "name": app.get("appName", "Unknown"),
                "usage": 0.0,
                "is_default": True
            })
        return default_apps
    
    # Return top N apps
    return valid_apps[:count]

def analyze_yes_no_question(prompt: str, strategy: dict, device_data: dict) -> Optional[Dict]:
    """
    Analyze a yes/no question or constraint-based battery question and provide a direct answer.
    
    Args:
        prompt: The user prompt
        strategy: The determined strategy
        device_data: The device data dictionary
        
    Returns:
        An insight dictionary with the answer, or None if not a relevant question
    """
    if not prompt:
        return None
    
    prompt_lower = prompt.lower()
    
    # Check if it's a question about using an app for a specific duration
    duration_question = (("can i" in prompt_lower or "will i" in prompt_lower) and 
                       ("use" in prompt_lower or "watch" in prompt_lower or "stream" in prompt_lower))
    
    # Check if it's a constraint-based battery question
    battery_constraint = ("save battery" in prompt_lower or "preserve battery" in prompt_lower or 
                         "extend battery" in prompt_lower) and ("but" in prompt_lower or "while" in prompt_lower)
    
    if not (duration_question or battery_constraint):
        return None
    
    # Extract information from the prompt
    battery_level = device_data.get("battery", {}).get("level", 0)
    
    if duration_question:
        # Handle duration-based questions (existing logic)
        time_constraint = None
        import re
        time_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*hrs?',
            r'for\s*(\d+)\s*h',
            r'for\s*(\d+)'
        ]
        for pattern in time_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                try:
                    time_constraint = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    pass
        
        # Default to 1 hour if no time constraint found
        if not time_constraint:
            time_constraint = 1
        
        # Calculate battery drain rates for different activities
        activity_drain_rates = {
            "youtube": 25,      # YouTube streaming
            "netflix": 20,      # Netflix streaming
            "video": 20,        # Generic video streaming
            "game": 25,         # Gaming
            "navigation": 18,   # Maps/navigation
            "call": 15,        # Phone calls
            "message": 10,      # Messaging
            "browse": 12,       # Web browsing
            "general": 10       # Default usage
        }
        
        # Identify the activity type and description
        activity_type = "general"
        activity_description = "use your device"
        
        if "youtube" in prompt_lower:
            activity_type = "youtube"
            activity_description = "use YouTube"
        elif "netflix" in prompt_lower:
            activity_type = "netflix"
            activity_description = "use Netflix"
        elif "video" in prompt_lower or "stream" in prompt_lower or "watch" in prompt_lower:
            activity_type = "video"
            activity_description = "stream video"
        elif "game" in prompt_lower or "play" in prompt_lower:
            activity_type = "game"
            activity_description = "play games"
        elif "navigate" in prompt_lower or "maps" in prompt_lower:
            activity_type = "navigation"
            activity_description = "use navigation"
        elif "call" in prompt_lower:
            activity_type = "call"
            activity_description = "make calls"
        elif "message" in prompt_lower or "text" in prompt_lower:
            activity_type = "message"
            activity_description = "use messaging"
        elif "browse" in prompt_lower or "web" in prompt_lower:
            activity_type = "browse"
            activity_description = "browse the web"
        
        # Get the drain rate for the activity
        drain_rate = activity_drain_rates.get(activity_type, activity_drain_rates["general"])
        
        # Calculate battery needed and determine if possible
        battery_needed = drain_rate * time_constraint
        remaining_battery = battery_level - battery_needed
        
        # Generate insight based on analysis
        if remaining_battery > 20:
            # Can do it comfortably
            return {
                "type": "YesNo",
                "title": "Yes, you can!",
                "description": f"Yes, you can {activity_description} for {time_constraint} hour{'s' if time_constraint > 1 else ''} with {battery_level}% battery. You'll have about {int(remaining_battery)}% battery remaining.",
                "severity": "low"
            }
        elif remaining_battery > 5:
            # Can do it but battery will be low
            return {
                "type": "YesNo",
                "title": "Yes, but battery will be low",
                "description": f"Yes, you can {activity_description} for {time_constraint} hour{'s' if time_constraint > 1 else ''}, but your battery will be low (around {int(remaining_battery)}%) afterward.",
                "severity": "medium"
            }
        else:
            # Not enough battery
            hours_possible = battery_level / drain_rate
            return {
                "type": "YesNo",
                "title": "No, insufficient battery",
                "description": f"No, {battery_level}% battery is not enough to {activity_description} for {time_constraint} hour{'s' if time_constraint > 1 else ''}. You can only {activity_description} for about {hours_possible:.1f} hour{'s' if hours_possible != 1 else ''}.",
                "severity": "high"
            }
    elif battery_constraint:
        # Handle constraint-based battery questions
        # Extract critical apps from the prompt
        critical_apps = []
        common_apps = {
            "gmail": "Gmail",
            "whatsapp": "WhatsApp",
            "maps": "Google Maps",
            "chrome": "Chrome",
            "youtube": "YouTube",
            "netflix": "Netflix",
            "spotify": "Spotify",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "message": "Messages",
            "email": "Email",
            "mail": "Email",
            "messaging": "Messages"
        }
        
        # Check for specific keywords in the prompt
        if any(word in prompt_lower for word in ["message", "messages", "text", "whatsapp", "messaging"]):
            critical_apps.append("WhatsApp")
            critical_apps.append("Messages")
        if any(word in prompt_lower for word in ["email", "mail", "gmail"]):
            critical_apps.append("Gmail")
        
        # Also check for app names directly
        for app_key, app_name in common_apps.items():
            if app_key in prompt_lower and app_name not in critical_apps:
                critical_apps.append(app_name)
        
        if not critical_apps:
            return None
        
        # Get battery usage for critical apps
        apps = device_data.get("apps", [])
        critical_app_usage = {}
        for app in apps:
            app_name = app.get("appName", "")
            if app_name in critical_apps:
                critical_app_usage[app_name] = app.get("batteryUsage", 0)
        
        # Create description based on battery level
        if battery_level <= 15:
            description = f"With critically low battery ({battery_level}%), I'll help you maximize battery life while keeping {', '.join(critical_apps)} running."
            severity = "high"
        elif battery_level <= 30:
            description = f"With low battery ({battery_level}%), I'll optimize battery usage while maintaining {', '.join(critical_apps)} functionality."
            severity = "medium"
        else:
            description = f"With {battery_level}% battery, I'll help you extend battery life while keeping {', '.join(critical_apps)} running normally."
            severity = "low"
        
        # Add app-specific information
        for app_name, usage in critical_app_usage.items():
            if usage > 0:
                description += f" {app_name} is currently using {usage}% of your battery."
        
        return {
            "type": "ConstraintResponse",
            "title": "Battery Optimization with Constraints",
            "description": description,
            "severity": severity
        }
    
    return None

def extract_app_count_from_prompt(prompt: str, default_count: int = 3) -> int:
    """
    Extract the number of apps requested in prompts like "top 3 apps".
    
    Args:
        prompt: The user prompt
        default_count: Default number to return if no number is found
        
    Returns:
        The number of apps requested, or default_count if not specified
    """
    if not prompt:
        return default_count
    
    # Special case for singulars - "the top app", "the top battery app", etc.
    if any(phrase in prompt.lower() for phrase in [
        "the top app", 
        "the top battery app", 
        "the top data app", 
        "the top data-consuming app",
        "the top battery-consuming app",
        "the top data consuming app",
        "the top battery consuming app",
        "the most data",
        "the most battery",
        "which app",
        "what app"
    ]):
        logger.debug(f"[PowerGuard] Singular app phrase detected in prompt: {prompt}")
        return 1
        
    # Use regex to find patterns like "top 3 apps", "3 apps", etc.
    app_count_patterns = [
        r'\btop\s+(\d+)\s+apps?\b',
        r'\b(\d+)\s+top\s+apps?\b',
        r'\b(\d+)\s+apps?\s+(?:using|draining|consuming)\b',
        r'\bshow\s+(?:me\s+)?(?:the\s+)?(\d+)\s+apps?\b',
        r'\btell\s+(?:me\s+)?(?:the\s+)?(\d+)\s+apps?\b',
        r'\blist\s+(?:the\s+)?(\d+)\s+apps?\b',
        # Combined pattern for "tell me/show me/list/give me" with optional parts
        r'\b(?:tell|show|list|give)\s+(?:me\s+)?(?:the\s+)?top\s+(\d+)\s+(?:battery|data)?\s*(?:consuming\s+)?apps?\b',
        # Fallback pattern for any "top N apps" format
        r'\b(?:the\s+)?top\s+(\d+)\s+(?:battery|data)?\s*(?:consuming\s+)?apps?\b'
    ]
    
    for pattern in app_count_patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            try:
                app_count = int(match.group(1))
                app_count = max(1, min(app_count, 10))  # Limit between 1 and 10
                logger.debug(f"[PowerGuard] Extracted app count from prompt: {app_count} (pattern: {pattern})")
                return app_count
            except (ValueError, IndexError):
                pass
                
    logger.debug(f"[PowerGuard] No app count found in prompt, using default: {default_count}")
    return default_count 