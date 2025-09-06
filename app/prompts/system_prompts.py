"""
System prompts for PowerGuard AI analysis - replicating Android app prompt structure.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger('powerguard_prompts')

# Core system prompts
MAIN_SYSTEM_PROMPT = """You are an AI assistant specialized in Android device optimization.
Analyze the provided device data and suggest actionable optimizations.
Focus on battery usage, network data consumption, and performance.
Provide specific recommendations based on the data patterns you observe."""

# Main analysis prompt template
MAIN_ANALYSIS_TEMPLATE = """You are a battery and data analysis/saver system. Analyze the device data and user query below.
Respond with ONLY a valid JSON object matching this structure:
{{
    "batteryScore": "number between 0-100",
    "dataScore": "number between 0-100", 
    "performanceScore": "number between 0-100",
    "insights": [{{"type": "BATTERY|DATA|PERFORMANCE", "title": "string", "description": "string", "severity": "LOW|MEDIUM|HIGH"}}],
    "actionable": [{{"type": "string", "description": "string", "parameters": {{}}}}]
}}

IMPORTANT: The "actionable" array must only contain objects with "type" being one of the following:
- set_standby_bucket: Limits an app's background activity (params: "packageName", "newMode": "active"|"working_set"|"frequent"|"rare"|"restricted")
- restrict_background_data: Prevents background data usage (params: "packageName")
- kill_app: Force stops an app (params: "packageName")
- manage_wake_locks: Restricts wake locks (params: "packageName") 
- set_notification: Sets user notification (params: "condition", "message")
- set_alarm: Sets system alarm (params: "condition", "message")

Device Data (last 24 hours):
DEVICE: {manufacturer} {model}
BATTERY: {battery_level}%{charging_status}
DATA: Current {current_data_mb}MB, Total {total_data_mb}MB
MEMORY: {available_ram}MB available of {total_ram}MB total
CPU: Usage {cpu_usage}%

TOP APPS:
{app_data}

{category_instructions}

User Query: "{user_query}"
"""

# Resource type detection prompt
RESOURCE_TYPE_DETECTION = """Determine if the following user query is primarily about BATTERY, DATA, or OTHER.
Respond with ONLY the resource type: BATTERY, DATA, or OTHER.
Query: "{user_query}" """

# Query categorization prompt
QUERY_CATEGORIZATION = """Categorize this user query into one of these categories based on its intent:
1. Information Queries (e.g., "Which apps use the most {resource_type}?")
2. Predictive Queries (e.g., "Can I use an app with current {resource_type}?") 
3. Optimization Requests (e.g., "Optimize {resource_type} for an activity")
4. Monitoring Triggers (e.g., "Notify me when {resource_type} reaches a threshold")
5. Past Usage Pattern Analysis (e.g., "Optimize {resource_type} based on past usage patterns")
6. Invalid Query (unrelated to {resource_type} or unclear)
Respond with ONLY the category number (1-6).
Query: "{user_query}" """

# Category-specific instruction templates
CATEGORY_INSTRUCTIONS = {
    1: """INSTRUCTIONS FOR INFORMATION QUERY:
- Provide exactly {number} items if specified, else 5.
- Use data from Device Data for {resource_type}.
- Return insights only, do not include any actionables.
- Type: "{resource_type}".
- Focus on providing informative analysis without optimization actions.""",

    2: """INSTRUCTIONS FOR PREDICTIVE QUERY:
- Analyze feasibility based on current {resource_type} and typical app usage.
- Return yes/no with a brief explanation in insights.
- Return insights only, do not include any actionables.
- Type: "{resource_type}".
- Consider current resource levels and typical usage patterns.""",

    3: """INSTRUCTIONS FOR OPTIMIZATION REQUEST:
- Provide recommendations to optimize {resource_type}.
- Include actionables only from: set_standby_bucket, restrict_background_data, kill_app, manage_wake_locks
- For each actionable, include the required parameters as specified above.
- Type: "{resource_type}".
- Focus on apps that consume high {resource_type} but aren't critical.

IMPORTANT EXCLUSION HANDLING:
1. First, identify any apps that should be kept running based on the user query.
2. For each excluded app:
   - Include a "set_standby_bucket" actionable with "newMode" set to "active"
   - Set "packageName" to the appropriate package name
   - Include description like "Keep [AppName] active as requested"
3. Do NOT apply any restrictive actions to excluded apps.
4. For all other apps, apply appropriate restrictions to optimize {resource_type}.""",

    4: """INSTRUCTIONS FOR MONITORING TRIGGER:
- Set up a trigger using set_notification if query mentions "notify", otherwise use set_alarm.
- Do not return any other actionable types
- Include "condition" and "message" in parameters.
- Type: "{resource_type}".
- Create meaningful trigger conditions and user-friendly messages.""",

    5: """INSTRUCTIONS FOR PAST USAGE PATTERN OPTIMIZATION:
- CURRENT TIME: {current_time}
- CURRENT DAY: {current_day}
- BATTERY LEVEL: {battery_level}%{charging_status}
- DATA USAGE: Current {current_data}MB, Total {total_data}MB

1. Analyze the past usage patterns below
2. Identify patterns relevant to current time, day, and resource level
3. For BATTERY patterns:
   - Only suggest actions if current battery <40% AND not charging AND high-usage period approaching
   - Set severity: LOW (>70%), MEDIUM (30-70%), HIGH (<30%)
   - Use set_standby_bucket, kill_app, or manage_wake_locks for critical periods
4. For DATA patterns:
   - Only suggest actions if remaining data <25% AND high-usage period approaching
   - Set severity: LOW (>50%), MEDIUM (25-50%), HIGH (<25%)
   - Use restrict_background_data for critical periods
5. Include insights about patterns even if no action needed
6. If no patterns found, return insight indicating no patterns found
7. If pattern found but resource adequate, include insight but no actionables

PAST USAGE PATTERNS:
{past_usage_patterns}""",

    6: """INSTRUCTIONS FOR INVALID QUERY:
- Return an insight explaining that the query is not related to device optimization.
- Do not include any actionables.
- Suggest how the user might rephrase their query for better results."""
}

def get_resource_type_prompt(user_query: str) -> str:
    """Generate resource type detection prompt."""
    return RESOURCE_TYPE_DETECTION.format(user_query=user_query)

def get_categorization_prompt(user_query: str, resource_type: str) -> str:
    """Generate query categorization prompt."""
    return QUERY_CATEGORIZATION.format(
        user_query=user_query,
        resource_type=resource_type
    )

def get_category_instructions(
    category: int,
    resource_type: str,
    device_data: Dict[str, Any],
    user_query: str,
    number: Optional[int] = None,
    past_usage_patterns: Optional[str] = None
) -> str:
    """Generate category-specific instructions."""
    
    if category not in CATEGORY_INSTRUCTIONS:
        category = 6  # Invalid query fallback
    
    instructions = CATEGORY_INSTRUCTIONS[category]
    
    # Format the instructions based on category
    format_params = {
        "resource_type": resource_type,
        "user_query": user_query,
        "number": number if number else 5  # Default to 5 if no number specified
    }
        
    if category == 5:  # Past usage pattern analysis
        battery_data = device_data.get("battery", {})
        network_data = device_data.get("network", {}).get("dataUsage", {})
        
        current_time = datetime.now().strftime("%H:%M")
        current_day = datetime.now().strftime("%A")
        battery_level = battery_data.get("level", 100)
        charging_status = " (charging)" if battery_data.get("isCharging", False) else ""
        current_data = network_data.get("foreground", 0) + network_data.get("background", 0)
        total_data = current_data * 2  # Estimate total data plan
        
        format_params.update({
            "current_time": current_time,
            "current_day": current_day,
            "battery_level": battery_level,
            "charging_status": charging_status,
            "current_data": current_data,
            "total_data": total_data,
            "past_usage_patterns": past_usage_patterns or "No past usage patterns available."
        })
    
    return instructions.format(**format_params)

def get_main_analysis_prompt(
    user_query: str,
    device_data: Dict[str, Any],
    category: int,
    resource_type: str,
    number: Optional[int] = None,
    past_usage_patterns: Optional[str] = None
) -> str:
    """Generate the main analysis prompt."""
    
    # Extract device information
    device_info = device_data.get("deviceInfo") or {}
    battery_data = device_data.get("battery", {})
    memory_data = device_data.get("memory", {})
    cpu_data = device_data.get("cpu", {})
    network_data = device_data.get("network", {}).get("dataUsage", {})
    
    manufacturer = device_info.get("manufacturer", "Unknown")
    model = device_info.get("model", "Device")
    battery_level = battery_data.get("level", 100)
    charging_status = " (charging)" if battery_data.get("isCharging", False) else ""
    current_data_mb = network_data.get("foreground", 0) + network_data.get("background", 0)
    total_data_mb = current_data_mb * 2  # Estimate
    available_ram = memory_data.get("availableRam", 0)
    total_ram = memory_data.get("totalRam", 0)
    cpu_usage = cpu_data.get("usage", 0) if cpu_data.get("usage", -1) != -1 else 0
    
    # Format app data
    app_data = format_app_data_for_prompt(device_data.get("apps", []))
    
    # Get category-specific instructions
    category_instructions = get_category_instructions(
        category=category,
        resource_type=resource_type,
        device_data=device_data,
        user_query=user_query,
        number=number,
        past_usage_patterns=past_usage_patterns
    )
    
    return MAIN_ANALYSIS_TEMPLATE.format(
        manufacturer=manufacturer,
        model=model,
        battery_level=battery_level,
        charging_status=charging_status,
        current_data_mb=current_data_mb,
        total_data_mb=total_data_mb,
        available_ram=available_ram,
        total_ram=total_ram,
        cpu_usage=cpu_usage,
        app_data=app_data,
        category_instructions=category_instructions,
        user_query=user_query
    )

def format_app_data_for_prompt(apps: list) -> str:
    """Format app data for inclusion in prompts."""
    if not apps:
        return "No app data available."
    
    # Sort by battery usage and take top 10
    sorted_apps = sorted(
        apps, 
        key=lambda x: float(x.get('batteryUsage', 0) or 0), 
        reverse=True
    )[:10]
    
    app_lines = []
    for app in sorted_apps:
        app_name = app.get('appName', 'Unknown App')
        package_name = app.get('packageName', 'unknown.package')
        battery_usage = app.get('batteryUsage', 0) or 0
        
        # Get data usage
        data_usage = app.get('dataUsage', {})
        if isinstance(data_usage, dict):
            fg_data = data_usage.get('foreground', 0) or 0
            bg_data = data_usage.get('background', 0) or 0
            total_data = fg_data + bg_data
        else:
            total_data = 0
            
        # Get time data (convert from ms to minutes)
        fg_time = (app.get('foregroundTime', 0) or 0) / 60000
        bg_time = (app.get('backgroundTime', 0) or 0) / 60000
        
        app_lines.append(
            f"- {app_name} ({package_name}): {battery_usage:.1f}% battery, "
            f"{total_data:.1f}MB data, {fg_time:.1f}min foreground, {bg_time:.1f}min background"
        )
    
    return "\n".join(app_lines)

def extract_number_from_query(user_query: str) -> Optional[int]:
    """Extract number specification from user query (e.g., 'top 5 apps')."""
    import re
    
    # Look for patterns like "top 5", "first 3", "5 apps", etc.
    patterns = [
        r'top (\d+)',
        r'first (\d+)', 
        r'(\d+) apps?',
        r'show (\d+)',
        r'list (\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_query.lower())
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    return None