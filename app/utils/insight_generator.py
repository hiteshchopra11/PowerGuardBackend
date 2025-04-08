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
    Generate insights based on optimization strategy and device data.
    
    Args:
        strategy: The optimization strategy
        device_data: The device data dictionary
        is_information_request: Whether this is an information request
        prompt: The original user prompt for question detection
        
    Returns:
        List of insight dictionaries
    """
    # Check for yes/no questions first
    if prompt:
        yes_no_response = analyze_yes_no_question(prompt, strategy, device_data)
        if yes_no_response:
            # For yes/no questions, return only the yes/no response insights
            return yes_no_response["insights"]
    
    insights = []
    
    # Generate regular insights based on request type
    if is_information_request:
        insights.extend(generate_information_insights(strategy, device_data))
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
        savings = calculate_savings(strategy, strategy["critical_apps"])
    
    # Main strategy insight
    main_insight = {
        "type": "Strategy",
        "title": f"Designed a custom {'battery' if strategy['focus'] == 'battery' else 'network' if strategy['focus'] == 'network' else 'resource'} strategy for you",
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
    if strategy["data_constraint"]:
        insights.append({
            "type": "DataWarning",
            "title": "Limited Data Remaining",
            "description": f"You have {strategy['data_constraint']}MB of data remaining. Restricting background data usage to conserve data.",
            "severity": "medium"
        })
    
    # Time constraint insight
    if strategy["time_constraint"]:
        insights.append({
            "type": "TimeConstraint",
            "title": f"Optimized for {strategy['time_constraint']} Hour{'s' if strategy['time_constraint'] > 1 else ''} Usage",
            "description": f"Adjusting power management to ensure device lasts for {strategy['time_constraint']} hour{'s' if strategy['time_constraint'] > 1 else ''}.",
            "severity": "info"
        })
    
    # Critical apps insight
    if strategy["critical_apps"]:
        app_names = [get_app_name(app) for app in strategy["critical_apps"]]
        insights.append({
            "type": "CriticalApps",
            "title": "Protected Critical Apps",
            "description": f"Maintaining full functionality for: {', '.join(app_names)}",
            "severity": "info"
        })
    
    # Add savings insights using the same consistent values
    if strategy["show_battery_savings"] and savings["batteryMinutes"] > 0:
        insights.append({
            "type": "BatterySavings",
            "title": "Extended Battery Life",
            "description": f"Estimated battery extension: {savings['batteryMinutes']} minutes",
            "severity": "info"
        })
    
    if strategy["show_data_savings"] and savings["dataMB"] > 0:
        insights.append({
            "type": "DataSavings",
            "title": "Reduced Data Usage",
            "description": f"Estimated data savings: {savings['dataMB']} MB",
            "severity": "info"
        })
    
    return insights

def generate_information_insights(strategy: dict, device_data: dict) -> List[Dict]:
    """Generate insights for information requests."""
    insights = []
    
    # Device-level insights
    battery_level = device_data.get("battery", {}).get("level", 0)
    
    # Add battery status insight
    if "battery" in strategy["focus"] or strategy["focus"] == "both":
        charging = device_data.get("battery", {}).get("isCharging", False)
        status = "charging" if charging else "discharging"
        severity = "low"
        
        if not charging and battery_level <= 15:
            severity = "high"
        elif not charging and battery_level <= 30:
            severity = "medium"
            
        insights.append({
            "type": "BatteryStatus",
            "title": "Battery Status",
            "description": f"Current battery level is {battery_level}% and {status}.",
            "severity": severity
        })
    
    # Add network status insight
    if "network" in strategy["focus"] or strategy["focus"] == "both":
        network_type = device_data.get("network", {}).get("type", "unknown")
        network_strength = device_data.get("network", {}).get("strength", 0)
        data_used = device_data.get("network", {}).get("dataUsed", 0)
        
        data_status = "good"
        severity = "low"
        
        if data_used > 1800:  # Over 90% of 2GB
            data_status = "nearly depleted"
            severity = "high"
        elif data_used > 1500:  # Over 75% of 2GB
            data_status = "running low"
            severity = "medium"
            
        insights.append({
            "type": "NetworkStatus",
            "title": "Network Status",
            "description": f"Connected to {network_type} with {network_strength}% signal strength. Your data usage is {data_status} with {2000-data_used}MB remaining.",
            "severity": severity
        })
    
    # Get top battery consuming apps
    if "battery" in strategy["focus"] or strategy["focus"] == "both":
        battery_apps = get_top_consuming_apps(device_data, "battery", 5)
        if battery_apps:
            apps_str = "\n".join([f"- {app['name']}: {app['usage']}%" for app in battery_apps])
            battery_insight = {
                "type": "BatteryUsage",
                "title": "Top Battery Consuming Apps",
                "description": f"The following apps are consuming the most battery:\n{apps_str}",
                "severity": "info"
            }
            
            # Add recommendations for high-consuming apps
            if battery_apps and battery_apps[0]["usage"] > 20:
                high_usage_apps = [app["name"] for app in battery_apps if app["usage"] > 20]
                if high_usage_apps:
                    battery_insight["description"] += f"\n\nConsider restricting background activity for {', '.join(high_usage_apps)} to save battery."
            
            insights.append(battery_insight)
    
    # Get top data consuming apps
    if "network" in strategy["focus"] or strategy["focus"] == "both":
        data_apps = get_top_consuming_apps(device_data, "data", 5)
        if data_apps:
            apps_str = "\n".join([f"- {app['name']}: {app['usage']} MB" for app in data_apps])
            data_insight = {
                "type": "DataUsage",
                "title": "Top Data Consuming Apps",
                "description": f"The following apps are consuming the most data:\n{apps_str}",
                "severity": "info"
            }
            
            # Add recommendations for high-consuming apps
            if data_apps and data_apps[0]["usage"] > 100:
                high_usage_apps = [app["name"] for app in data_apps if app["usage"] > 100]
                if high_usage_apps:
                    data_insight["description"] += f"\n\nConsider restricting background data for {', '.join(high_usage_apps)} to save mobile data."
            
            insights.append(data_insight)
    
    return insights

def generate_strategy_description(strategy: dict, battery_level: float, savings: dict = None) -> str:
    """Generate a human-readable description of the strategy."""
    lines = []
    
    # Battery level context
    if battery_level <= 10:
        lines.append(f"As battery is critically low ({battery_level}%), taking aggressive measures")
    elif battery_level <= 30:
        lines.append(f"As battery is low ({battery_level}%), optimizing usage")
    elif battery_level > 80:
        lines.append(f"As battery is sufficient ({battery_level}%), taking minimal measures")
    
    # Critical apps
    if strategy["critical_apps"]:
        app_names = [get_app_name(app) for app in strategy["critical_apps"]]
        lines.append(f"Protected critical apps: {', '.join(app_names)}")
    
    # Add actionable descriptions based on strategy
    if strategy["aggressiveness"] in ["very_aggressive", "aggressive"]:
        lines.append("Restricted background activity for non-critical apps")
        
        if strategy["focus"] in ["network", "both"]:
            lines.append("Limited background data usage")
        
        if strategy["focus"] in ["battery", "both"]:
            lines.append("Applied aggressive battery optimization")
    else:
        lines.append("Applied moderate optimization for non-critical apps")
    
    # Time constraint
    if strategy["time_constraint"]:
        lines.append(f"Optimized for {strategy['time_constraint']} hour{'s' if strategy['time_constraint'] > 1 else ''} of usage")
    
    # If savings not provided, check for pre-calculated savings in strategy
    if savings is None:
        if "calculated_savings" in strategy:
            savings = strategy["calculated_savings"]
        else:
            # Last resort: calculate if nothing else is available
            savings = calculate_savings(strategy, strategy["critical_apps"])
    
    # Savings information
    if strategy["show_battery_savings"] and savings["batteryMinutes"] > 0:
        lines.append(f"Estimated battery extension: {savings['batteryMinutes']} minutes")
    
    if strategy["show_data_savings"] and savings["dataMB"] > 0:
        lines.append(f"Estimated data savings: {savings['dataMB']} MB")
    
    return "\n".join(lines)

def get_top_consuming_apps(device_data: dict, resource_type: str, limit: int = 5) -> List[Dict]:
    """
    Get the top consuming apps for a specific resource.
    
    Args:
        device_data: The device data dictionary
        resource_type: "battery" or "data"
        limit: Maximum number of apps to return
        
    Returns:
        List of dictionaries with app name and usage
    """
    apps = device_data.get("apps", [])
    if not apps:
        return []
    
    usage_field = "batteryUsage" if resource_type == "battery" else "dataUsage"
    
    # Filter and extract valid apps with usage data
    valid_apps = []
    for app in apps:
        if usage_field not in app:
            continue
            
        app_name = get_app_name(app.get("packageName", ""))
        if resource_type == "battery":
            # Battery usage is a simple value
            usage = app.get(usage_field, 0)
            if usage is not None and usage > 0:
                valid_apps.append({
                    "name": app_name,
                    "usage": usage
                })
        else:
            # Data usage could be a dict or value
            data_usage = app.get(usage_field, 0)
            total_usage = 0
            
            if data_usage is None:
                continue
            elif isinstance(data_usage, dict):
                # Extract foreground and background usage
                foreground = data_usage.get("foreground", 0)
                background = data_usage.get("background", 0)
                if isinstance(foreground, (int, float)) and isinstance(background, (int, float)):
                    total_usage = foreground + background
            elif isinstance(data_usage, (int, float)):
                total_usage = data_usage
                
            if total_usage > 0:
                valid_apps.append({
                    "name": app_name,
                    "usage": total_usage
                })
    
    # Sort by usage (descending)
    sorted_apps = sorted(valid_apps, key=lambda app: app.get("usage", 0), reverse=True)
    
    # Return top N apps
    return sorted_apps[:limit]

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
        
        # Generate insights based on the analysis
        insights = []
        
        # Main yes/no insight
        if remaining_battery > 20:
            # Can do it comfortably
            insights.append({
                "type": "YesNo",
                "title": "Yes, you can!",
                "description": f"Yes, you can {activity_description} for {time_constraint} hour{'s' if time_constraint > 1 else ''} with {battery_level}% battery. You'll have about {int(remaining_battery)}% battery remaining.",
                "severity": "low"
            })
        elif remaining_battery > 5:
            # Can do it but battery will be low
            insights.append({
                "type": "YesNo",
                "title": "Yes, but battery will be low",
                "description": f"Yes, you can {activity_description} for {time_constraint} hour{'s' if time_constraint > 1 else ''}, but your battery will be low (around {int(remaining_battery)}%) afterward.",
                "severity": "medium"
            })
        else:
            # Not enough battery
            hours_possible = battery_level / drain_rate
            insights.append({
                "type": "YesNo",
                "title": "No, insufficient battery",
                "description": f"No, {battery_level}% battery is not enough to {activity_description} for {time_constraint} hour{'s' if time_constraint > 1 else ''}. You can only {activity_description} for about {hours_possible:.1f} hour{'s' if hours_possible != 1 else ''}.",
                "severity": "high"
            })
        
        # Add battery usage insight
        insights.append({
            "type": "BatteryUsage",
            "title": f"Battery Usage for {activity_description.capitalize()}",
            "description": f"This activity typically uses about {drain_rate}% battery per hour.",
            "severity": "info"
        })
        
    else:  # Handle constraint-based battery questions
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
            "instagram": "Instagram"
        }
        
        for app_key, app_name in common_apps.items():
            if app_key in prompt_lower:
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
        
        insights = []
        
        # Main battery strategy insight
        strategy_desc = []
        if battery_level <= 15:
            strategy_desc.append(f"With critically low battery ({battery_level}%), I'll help you maximize battery life while keeping {', '.join(critical_apps)} running.")
            severity = "high"
        elif battery_level <= 30:
            strategy_desc.append(f"With low battery ({battery_level}%), I'll optimize battery usage while maintaining {', '.join(critical_apps)} functionality.")
            severity = "medium"
        else:
            strategy_desc.append(f"With {battery_level}% battery, I'll help you extend battery life while keeping {', '.join(critical_apps)} running normally.")
            severity = "low"
        
        # Add app-specific information
        for app_name, usage in critical_app_usage.items():
            if usage > 0:
                strategy_desc.append(f"{app_name} is currently using {usage}% of your battery.")
        
        # Add recommendations
        strategy_desc.append("\nRecommendations:")
        strategy_desc.append("• Keep these apps running normally")
        strategy_desc.append("• Restrict background activity for other apps")
        strategy_desc.append("• Reduce screen brightness")
        if battery_level <= 30:
            strategy_desc.append("• Enable battery saver mode")
        
        insights.append({
            "type": "BatteryStrategy",
            "title": f"Battery Strategy with {', '.join(critical_apps)}",
            "description": "\n".join(strategy_desc),
            "severity": severity
        })
        
        # Add battery status insight
        insights.append({
            "type": "BatteryStatus",
            "title": "Current Battery Status",
            "description": f"Battery level is at {battery_level}%. {'Critical - immediate action needed.' if battery_level <= 15 else 'Low - optimization recommended.' if battery_level <= 30 else 'Sufficient for normal operation.'}",
            "severity": severity
        })
    
    return {
        "insights": insights,
        "actionable": [],  # No actionables for yes/no questions
        "estimatedSavings": {
            "batteryMinutes": 0,  # No savings for information requests
            "dataMB": 0
        }
    } 