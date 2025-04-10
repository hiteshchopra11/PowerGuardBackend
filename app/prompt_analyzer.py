from typing import Dict, Any, List, Optional
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_prompt_analyzer')

# Define all supported actionable types
ALLOWED_ACTIONABLE_TYPES = {
    "SET_STANDBY_BUCKET",
    "RESTRICT_BACKGROUND_DATA",
    "KILL_APP", 
    "MANAGE_WAKE_LOCKS",
    "THROTTLE_CPU_USAGE"
}

def classify_user_prompt(prompt: str) -> Dict[str, Any]:
    """
    Analyze a user prompt to determine the optimization goals and relevant actionable types.
    
    Args:
        prompt: User-provided prompt text
        
    Returns:
        Dictionary with optimization flags and relevant actionable types
    """
    if not prompt or not isinstance(prompt, str):
        return {
            "optimize_battery": True,  # Default to True for empty prompts
            "optimize_data": True,     # Default to True for empty prompts
            "actionable_focus": ["SET_STANDBY_BUCKET", "RESTRICT_BACKGROUND_DATA"],
            "is_relevant": True        # Consider empty prompts as relevant
        }
    
    # Map containing keywords and their associated goals and actions
    keywords = {
        "battery": {
            "goals": ["optimize_battery"],
            "actions": ["SET_STANDBY_BUCKET", "MANAGE_WAKE_LOCKS", "THROTTLE_CPU_USAGE"]
        },
        "power": {
            "goals": ["optimize_battery"],
            "actions": ["SET_STANDBY_BUCKET", "MANAGE_WAKE_LOCKS", "THROTTLE_CPU_USAGE"]
        },
        "charge": {
            "goals": ["optimize_battery"],
            "actions": ["KILL_APP", "MANAGE_WAKE_LOCKS"]
        },
        "data": {
            "goals": ["optimize_data"],
            "actions": ["RESTRICT_BACKGROUND_DATA", "KILL_APP"]
        },
        "network": {
            "goals": ["optimize_data"],
            "actions": ["RESTRICT_BACKGROUND_DATA"]
        },
        "internet": {
            "goals": ["optimize_data"],
            "actions": ["RESTRICT_BACKGROUND_DATA"]
        },
        "wifi": {
            "goals": ["optimize_data"],
            "actions": ["RESTRICT_BACKGROUND_DATA"]
        },
        "clean": {
            "goals": [],
            "actions": ["KILL_APP"]
        },
        "background": {
            "goals": ["optimize_battery", "optimize_data"],
            "actions": ["SET_STANDBY_BUCKET", "RESTRICT_BACKGROUND_DATA"]
        },
        "performance": {
            "goals": [],
            "actions": ["SET_STANDBY_BUCKET", "THROTTLE_CPU_USAGE"]
        }
    }
    
    result = {
        "optimize_battery": False,
        "optimize_data": False,
        "actionable_focus": [],
        "is_relevant": False
    }
    
    lowered = prompt.lower()
    
    # Add flags for keywords before attempting to detect negations
    has_battery_keyword = any(keyword in lowered for keyword in ["battery", "power", "charge", "drain", "consumption"])
    has_data_keyword = any(keyword in lowered for keyword in ["data", "network", "internet", "wifi", "cellular", "mobile"])
    
    # Check for other action-specific keywords
    has_kill_keyword = "kill" in lowered
    has_background_keyword = "background" in lowered
    has_performance_keyword = "performance" in lowered
    
    # If any relevant keyword is found, mark the prompt as relevant
    if has_battery_keyword or has_data_keyword or has_kill_keyword or has_background_keyword or has_performance_keyword:
        result["is_relevant"] = True
    else:
        # Check for common optimization terms
        optimization_terms = ["optimize", "optimization", "save", "conserve", "extend", "improve", "boost", "reduce usage"]
        has_optimization_term = any(term in lowered for term in optimization_terms)
        
        if has_optimization_term:
            # General optimization request
            result["optimize_battery"] = True
            result["optimize_data"] = True
            result["actionable_focus"] = ["SET_STANDBY_BUCKET", "RESTRICT_BACKGROUND_DATA"]
            result["is_relevant"] = True
        else:
            # Not related to optimization
            result["is_relevant"] = False
        
        return result
    
    # Populate actionable_focus based on keywords
    if has_battery_keyword:
        result["optimize_battery"] = True
        for action in ["SET_STANDBY_BUCKET", "MANAGE_WAKE_LOCKS", "THROTTLE_CPU_USAGE"]:
            if action not in result["actionable_focus"]:
                result["actionable_focus"].append(action)
    
    if has_data_keyword:
        result["optimize_data"] = True
        for action in ["RESTRICT_BACKGROUND_DATA", "KILL_APP"]:
            if action not in result["actionable_focus"]:
                result["actionable_focus"].append(action)
    
    if has_kill_keyword:
        if "KILL_APP" not in result["actionable_focus"]:
            result["actionable_focus"].append("KILL_APP")
    
    if has_background_keyword:
        if "RESTRICT_BACKGROUND_DATA" not in result["actionable_focus"]:
            result["actionable_focus"].append("RESTRICT_BACKGROUND_DATA")
    
    if has_performance_keyword:
        for action in ["SET_STANDBY_BUCKET", "THROTTLE_CPU_USAGE"]:
            if action not in result["actionable_focus"]:
                result["actionable_focus"].append(action)
    
    # Now check for negations and override the simple matches if found
    battery_negation_patterns = [
        r"(?:don't|do not|dont)\s+(?:optimize|save|worry|care|about)\s+(?:the\s+)?battery",
        r"not\s+(?:optimizing|saving|worrying|caring|about)\s+(?:the\s+)?battery",
        r"no\s+(?:battery|power)\s+(?:optimization|saving)",
        r"ignore\s+(?:the\s+)?battery",
        r"without\s+(?:battery|power)\s+(?:optimization|saving)"
    ]
    
    if any(re.search(pattern, lowered) for pattern in battery_negation_patterns):
        result["optimize_battery"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["SET_STANDBY_BUCKET", "MANAGE_WAKE_LOCKS", "THROTTLE_CPU_USAGE"]]
    
    data_negation_patterns = [
        r"(?:don't|do not|dont)\s+(?:optimize|save|worry|care|about)\s+(?:the\s+)?(?:data|network)",
        r"not\s+(?:optimizing|saving|worrying|caring|about)\s+(?:the\s+)?(?:data|network)",
        r"no\s+(?:data|network)\s+(?:optimization|saving)",
        r"ignore\s+(?:the\s+)?(?:data|network)",
        r"without\s+(?:data|network)\s+(?:optimization|saving)"
    ]
    
    if any(re.search(pattern, lowered) for pattern in data_negation_patterns):
        result["optimize_data"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["RESTRICT_BACKGROUND_DATA", "KILL_APP"]]
    
    # Handle specific case of "but not data" constructions
    if "battery" in lowered and ("but not data" in lowered or "but no data" in lowered):
        result["optimize_battery"] = True
        result["optimize_data"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["RESTRICT_BACKGROUND_DATA", "KILL_APP"]]
    
    # Handle specific case of "but not battery" constructions
    if "data" in lowered and ("but not battery" in lowered or "but no battery" in lowered):
        result["optimize_data"] = True
        result["optimize_battery"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["SET_STANDBY_BUCKET", "MANAGE_WAKE_LOCKS", "THROTTLE_CPU_USAGE"]]
    
    # If we found keywords but no specific optimization goals after negation processing,
    # check if we have actionable_focus and set defaults accordingly
    if result["is_relevant"] and not any([result["optimize_battery"], result["optimize_data"]]):
        if result["actionable_focus"]:
            # Check if actions are more battery or data related
            battery_actions = ["SET_STANDBY_BUCKET", "MANAGE_WAKE_LOCKS", "THROTTLE_CPU_USAGE"]
            data_actions = ["RESTRICT_BACKGROUND_DATA", "KILL_APP"]
            
            battery_focus = any(action in battery_actions for action in result["actionable_focus"])
            data_focus = any(action in data_actions for action in result["actionable_focus"])
            
            result["optimize_battery"] = battery_focus
            result["optimize_data"] = data_focus
            
            # If still no optimization goals, default to both
            if not any([result["optimize_battery"], result["optimize_data"]]):
                result["optimize_battery"] = True
                result["optimize_data"] = True
                result["actionable_focus"].extend(["SET_STANDBY_BUCKET", "RESTRICT_BACKGROUND_DATA"])
    
    logger.debug(f"[PowerGuard] Classified prompt '{prompt}': {result}")
    return result

def is_prompt_relevant(prompt: str) -> bool:
    """
    Determine if a user prompt is relevant for resource optimization.
    
    Args:
        prompt: User-provided prompt text
        
    Returns:
        Boolean indicating if the prompt is relevant
    """
    if not prompt or not isinstance(prompt, str):
        return False
        
    classification = classify_user_prompt(prompt)
    return classification["is_relevant"]

def classify_with_llm(prompt: str, llm_client=None) -> Dict[str, Any]:
    """
    Use LLM to classify a prompt when rule-based classification is insufficient.
    This is a fallback method for ambiguous prompts.
    
    Args:
        prompt: User-provided prompt text
        llm_client: Optional LLM client (will use the default if None)
        
    Returns:
        Dictionary with optimization flags and relevant actionable types
    """
    # Default result structure
    result = {
        "optimize_battery": False,
        "optimize_data": False,
        "actionable_focus": [],
        "is_relevant": False
    }
    
    try:
        # Basic rule-based check first
        basic_check = classify_user_prompt(prompt)
        if basic_check["is_relevant"]:
            return basic_check
            
        logger.debug(f"[PowerGuard] Rule-based classification failed, using LLM for prompt: '{prompt}'")
        
        # If no LLM client is provided, try to use the global one if available
        if llm_client is None:
            from app.llm_service import groq_client
            llm_client = groq_client
            
        # Simple classification prompt
        classification_prompt = f"""
        Analyze this user prompt: "{prompt}"
        
        Identify:
        1. Is it related to optimizing battery usage or network/data usage on a mobile device?
        2. Which specific apps need to be protected/kept running? (e.g., WhatsApp, Maps, Messages)
        3. Are there any time constraints mentioned? (e.g., "next 5 hours", "2 hour drive")
        
        Reply with ONLY a JSON object like this example:
        {{
          "is_relevant": true/false,
          "optimize_battery": true/false,
          "optimize_data": true/false,
          "protected_apps": ["APP1", "APP2"],
          "time_constraint_minutes": number or null,
          "actionable_focus": ["ACTION_TYPE1", "ACTION_TYPE2"]
        }}
        
        The actionable_focus array should ONLY include items from this list:
        {", ".join(ALLOWED_ACTIONABLE_TYPES)}
        
        Select actions that best match the user's intent while respecting protected apps and time constraints.
        """
        
        completion = llm_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a specialized AI that only classifies prompts related to mobile device resource optimization."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content.strip()
        import json
        llm_result = json.loads(response_text)
        
        # Validate and clean the result
        if "is_relevant" in llm_result:
            result["is_relevant"] = bool(llm_result["is_relevant"])
            
        if "optimize_battery" in llm_result:
            result["optimize_battery"] = bool(llm_result["optimize_battery"])
            
        if "optimize_data" in llm_result:
            result["optimize_data"] = bool(llm_result["optimize_data"])
            
        if "protected_apps" in llm_result and isinstance(llm_result["protected_apps"], list):
            result["protected_apps"] = llm_result["protected_apps"]
            
        if "time_constraint_minutes" in llm_result and isinstance(llm_result["time_constraint_minutes"], (int, type(None))):
            result["time_constraint_minutes"] = llm_result["time_constraint_minutes"]
            
        if "actionable_focus" in llm_result and isinstance(llm_result["actionable_focus"], list):
            # Filter to only include valid action types
            result["actionable_focus"] = [
                action for action in llm_result["actionable_focus"] 
                if action in ALLOWED_ACTIONABLE_TYPES
            ]
            
        logger.debug(f"[PowerGuard] LLM classification result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[PowerGuard] Error in LLM classification: {str(e)}", exc_info=True)
        # Fall back to rule-based classification
        return classify_user_prompt(prompt)
        
def generate_optimization_prompt(classification: Dict[str, Any], device_data: Dict[str, Any], historical_patterns_text: str) -> str:
    """
    Generate a specialized LLM prompt based on the classification of the user's prompt.
    
    Args:
        classification: Result from prompt classification
        device_data: Current device data
        historical_patterns_text: Text of historical usage patterns
        
    Returns:
        Specialized prompt for the LLM
    """
    # Base prompt structure
    base_prompt = f"""
    As an AI resource optimization expert, analyze this Android device data:
    
    {historical_patterns_text}
    
    Current Device Data:
    Battery:
    - Level: {device_data['battery']['level']}%
    - Temperature: {device_data['battery']['temperature']}°C
    - Charging: {device_data['battery']['isCharging']}
    - Voltage: {device_data['battery']['voltage']}
    - Health: {device_data['battery']['health']}
    
    Memory:
    - Total RAM: {device_data['memory']['totalRam']} MB
    - Available RAM: {device_data['memory']['availableRam']} MB
    - Low Memory: {device_data['memory']['lowMemory']}
    
    CPU:
    - Usage: {device_data['cpu']['usage'] if device_data['cpu'].get('usage') is not None else 'N/A'}%
    - Temperature: {device_data['cpu']['temperature'] if device_data['cpu'].get('temperature') is not None else 'N/A'}°C
    
    Network:
    - Type: {device_data['network']['type']}
    - Strength: {device_data['network']['strength']}
    - Roaming: {device_data['network']['isRoaming']}
    - Data Usage: {device_data['network']['dataUsage']['foreground'] + device_data['network']['dataUsage']['background']} MB
    - Cellular Generation: {device_data['network']['cellularGeneration']}
    """
    
    # Add app data section
    app_data = format_apps_for_prompt(device_data['apps'])
    base_prompt += f"\nApp Data:\n{app_data}\n"
    
    # Determine device conditions
    battery_level = device_data['battery']['level']
    data_usage = device_data['network']['dataUsage']['foreground'] + device_data['network']['dataUsage']['background']
    total_data_plan = 3000  # Assume 3GB standard data plan
    data_remaining = total_data_plan - data_usage
    
    battery_critical = battery_level <= 20
    data_critical = data_remaining <= 100
    
    # Customize for specific optimization goals based on device conditions and user request
    if classification["optimize_battery"] and classification["optimize_data"]:
        if battery_critical and data_critical:
            # Both critical - focus on both
            optimization_goal = f"""
            OPTIMIZATION GOAL: Critical optimization of both battery life and network data usage
            
            IMPORTANT: Battery level is critically low at {battery_level}% and data remaining is only about {data_remaining}MB.
            Focus intensely on identifying apps that are consuming excessive battery AND network resources.
            Prioritize actions that will reduce both battery and data consumption, with special attention to background activities.
            """
        elif battery_critical:
            # Battery critical, data ok - prioritize battery
            optimization_goal = f"""
            OPTIMIZATION GOAL: Critical battery optimization with secondary data optimization
            
            IMPORTANT: Battery level is critically low at {battery_level}%.
            Focus primarily on extending battery life as the main priority.
            As a secondary goal, also optimize network data usage where possible, but battery conservation must take precedence.
            Prioritize battery-saving actions, even at the expense of some network functionality if necessary.
            """
        elif data_critical:
            # Data critical, battery ok - prioritize data
            optimization_goal = f"""
            OPTIMIZATION GOAL: Critical data optimization with secondary battery optimization
            
            IMPORTANT: Data remaining is critically low at approximately {data_remaining}MB.
            Focus primarily on minimizing data consumption as the main priority.
            As a secondary goal, also optimize battery usage where possible, but data conservation must take precedence.
            Prioritize data-saving actions, even at the expense of some battery life if necessary.
            """
        else:
            # Both ok - balance optimization
            optimization_goal = """
            OPTIMIZATION GOAL: Balanced optimization of both battery life and network data usage
            
            Focus on identifying apps that are consuming excessive battery AND network resources.
            Provide a balanced approach to optimizing both resources without extreme measures.
            Prioritize actions that will improve efficiency without significantly impacting user experience.
            """
    elif classification["optimize_battery"]:
        if battery_critical:
            # Battery critical - aggressive battery focus
            optimization_goal = f"""
            OPTIMIZATION GOAL: Critical battery life optimization
            
            IMPORTANT: Battery level is critically low at {battery_level}%.
            Focus exclusively on extending battery life as the highest priority.
            Take aggressive measures to reduce battery consumption by all apps.
            Identify and restrict background processes that consume battery.
            Recommend essential system changes to maximize remaining battery life.
            """
        else:
            # Battery ok - normal battery focus
            optimization_goal = """
            OPTIMIZATION GOAL: Standard battery life optimization
            
            Focus on identifying apps that are consuming excessive battery resources.
            Suggest reasonable optimizations to extend battery life without extreme measures.
            Balance battery optimization with maintaining normal device functionality.
            """
    elif classification["optimize_data"]:
        if data_critical:
            # Data critical - aggressive data focus
            optimization_goal = f"""
            OPTIMIZATION GOAL: Critical network data optimization
            
            IMPORTANT: Data remaining is critically low at approximately {data_remaining}MB.
            Focus exclusively on minimizing data consumption as the highest priority.
            Take aggressive measures to reduce data usage by all apps.
            Identify and restrict background processes that consume data.
            Recommend essential system changes to minimize data usage.
            """
        else:
            # Data ok - normal data focus
            optimization_goal = """
            OPTIMIZATION GOAL: Standard network data optimization
            
            Focus on identifying apps that are consuming excessive network data.
            Suggest reasonable optimizations to reduce data usage without extreme measures.
            Balance data optimization with maintaining normal device functionality.
            """
    else:
        # Default goal if classification was relevant but didn't specify goals
        if battery_critical and data_critical:
            optimization_goal = f"""
            OPTIMIZATION GOAL: Critical system optimization
            
            IMPORTANT: Battery level is critically low at {battery_level}% and data remaining is only about {data_remaining}MB.
            Focus on aggressive optimization of both battery and data resources.
            Take immediate action to extend battery life and conserve data usage.
            """
        elif battery_critical:
            optimization_goal = f"""
            OPTIMIZATION GOAL: Battery-focused system optimization
            
            IMPORTANT: Battery level is critically low at {battery_level}%.
            Prioritize battery life extension while also optimizing general system resources.
            Focus on the most battery-intensive apps and suggest appropriate actions.
            """
        elif data_critical:
            optimization_goal = f"""
            OPTIMIZATION GOAL: Data-focused system optimization
            
            IMPORTANT: Data remaining is critically low at approximately {data_remaining}MB.
            Prioritize data conservation while also optimizing general system resources.
            Focus on the most data-intensive apps and suggest appropriate actions.
            """
        else:
            optimization_goal = """
            OPTIMIZATION GOAL: General system optimization
            
            Balance battery life and network data optimization.
            Focus on the most resource-intensive apps and suggest appropriate actions.
            """
    
    # User's original prompt if available
    if "original_prompt" in classification and classification["original_prompt"]:
        optimization_goal += f"\nUser's goal: \"{classification['original_prompt']}\"\n"
    
    # Action focus
    if classification["actionable_focus"]:
        action_focus = "\nFocus on these action types: " + ", ".join(classification["actionable_focus"]) + "\n"
    else:
        action_focus = "\nConsider all available action types as appropriate.\n"
    
    # Complete the prompt with structured output requirements
    output_instructions = f"""
    Based on this data and the optimization goal, generate a comprehensive analysis with:
    
    1. actionable: A list of specific actions to take, including:
       - id: unique identifier for the action
       - type: the type of action (MUST be one of these EXACT values: {", ".join(ALLOWED_ACTIONABLE_TYPES)}
       - packageName: affected app's package name
       - description: what the action will do
       - reason: why this action is recommended
       - newMode: target state (e.g., "restricted")
       - parameters: additional context as key-value pairs
    
    2. insights: List of insights discovered about the device's behavior:
       - type: insight category (e.g., "BatteryDrain")
       - title: summary title
       - description: detailed explanation
       - severity: e.g., "low", "medium", "high"
    
    3. scores and estimates:
       - batteryScore: from 0-100 evaluating battery health
       - dataScore: from 0-100 evaluating data usage efficiency
       - performanceScore: from 0-100 evaluating overall performance
       - estimatedSavings: with batteryMinutes and dataMB values
    
    Return ONLY valid JSON with an id, success flag (true), timestamp, message, and the above fields.
    """
    
    # Combine all parts
    complete_prompt = base_prompt + optimization_goal + action_focus + output_instructions
    
    return complete_prompt

def format_apps_for_prompt(apps):
    """Format apps data for the prompt"""
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
                foreground_time = float(app.get('foregroundTime', 0) or 0) / 60
                background_time = float(app.get('backgroundTime', 0) or 0) / 60
                
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
        logger.error(f"[PowerGuard] Error in format_apps_for_prompt: {str(e)}")
        return "Error formatting app data.\n" 