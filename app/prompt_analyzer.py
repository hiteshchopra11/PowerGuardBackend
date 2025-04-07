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
            "actionable_focus": ["OPTIMIZE_BATTERY", "ENABLE_DATA_SAVER"],
            "is_relevant": True        # Consider empty prompts as relevant
        }
    
    # Map containing keywords and their associated goals and actions
    keywords = {
        "battery": {
            "goals": ["optimize_battery"],
            "actions": ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER", "RESTRICT_BACKGROUND", "ADJUST_SCREEN"]
        },
        "power": {
            "goals": ["optimize_battery"],
            "actions": ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER", "DISABLE_FEATURES"]
        },
        "charge": {
            "goals": ["optimize_battery"],
            "actions": ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER", "ENABLE_AIRPLANE_MODE"]
        },
        "data": {
            "goals": ["optimize_data"],
            "actions": ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND", "MANAGE_LOCATION"]
        },
        "network": {
            "goals": ["optimize_data"],
            "actions": ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]
        },
        "internet": {
            "goals": ["optimize_data"],
            "actions": ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]
        },
        "wifi": {
            "goals": ["optimize_data"],
            "actions": ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]
        },
        "clean": {
            "goals": [],
            "actions": ["CLEAR_CACHE", "UNINSTALL_APP"]
        },
        "background": {
            "goals": ["optimize_battery", "optimize_data"],
            "actions": ["RESTRICT_BACKGROUND", "SCHEDULE_TASKS"]
        },
        "performance": {
            "goals": [],
            "actions": ["UPDATE_APP", "CLEAR_CACHE"]
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
        # If no specific keywords found, consider it a general optimization request
        result["optimize_battery"] = True
        result["optimize_data"] = True
        result["actionable_focus"] = ["OPTIMIZE_BATTERY", "ENABLE_DATA_SAVER"]
        result["is_relevant"] = True
        return result
    
    # Populate actionable_focus based on keywords
    if has_battery_keyword:
        result["optimize_battery"] = True
        for action in ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER"]:
            if action not in result["actionable_focus"]:
                result["actionable_focus"].append(action)
    
    if has_data_keyword:
        result["optimize_data"] = True
        for action in ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]:
            if action not in result["actionable_focus"]:
                result["actionable_focus"].append(action)
    
    if has_kill_keyword:
        if "KILL_APP" not in result["actionable_focus"]:
            result["actionable_focus"].append("KILL_APP")
    
    if has_background_keyword:
        if "RESTRICT_BACKGROUND" not in result["actionable_focus"]:
            result["actionable_focus"].append("RESTRICT_BACKGROUND")
    
    if has_performance_keyword:
        for action in ["SET_STANDBY_BUCKET", "CATEGORIZE_APP"]:
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
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER"]]
    
    data_negation_patterns = [
        r"(?:don't|do not|dont)\s+(?:optimize|save|worry|care|about)\s+(?:the\s+)?(?:data|network)",
        r"not\s+(?:optimizing|saving|worrying|caring|about)\s+(?:the\s+)?(?:data|network)",
        r"no\s+(?:data|network)\s+(?:optimization|saving)",
        r"ignore\s+(?:the\s+)?(?:data|network)",
        r"without\s+(?:data|network)\s+(?:optimization|saving)"
    ]
    
    if any(re.search(pattern, lowered) for pattern in data_negation_patterns):
        result["optimize_data"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]]
    
    # Handle specific case of "but not data" constructions
    if "battery" in lowered and ("but not data" in lowered or "but no data" in lowered):
        result["optimize_battery"] = True
        result["optimize_data"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]]
    
    # Handle specific case of "but not battery" constructions
    if "data" in lowered and ("but not battery" in lowered or "but no battery" in lowered):
        result["optimize_data"] = True
        result["optimize_battery"] = False
        result["actionable_focus"] = [action for action in result["actionable_focus"] if action not in ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER"]]
    
    # If we found keywords but no specific optimization goals after negation processing,
    # check if we have actionable_focus and set defaults accordingly
    if result["is_relevant"] and not any([result["optimize_battery"], result["optimize_data"]]):
        if result["actionable_focus"]:
            # Check if actions are more battery or data related
            battery_actions = ["OPTIMIZE_BATTERY", "ENABLE_BATTERY_SAVER"]
            data_actions = ["ENABLE_DATA_SAVER", "RESTRICT_BACKGROUND"]
            
            battery_focus = any(action in battery_actions for action in result["actionable_focus"])
            data_focus = any(action in data_actions for action in result["actionable_focus"])
            
            result["optimize_battery"] = battery_focus
            result["optimize_data"] = data_focus
            
            # If still no optimization goals, default to both
            if not any([result["optimize_battery"], result["optimize_data"]]):
                result["optimize_battery"] = True
                result["optimize_data"] = True
                result["actionable_focus"].extend(["OPTIMIZE_BATTERY", "ENABLE_DATA_SAVER"])
    
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
        
        Is it related to optimizing battery usage or network/data usage on a mobile device?
        If yes, which of these does it focus on: battery, data/network, or both?
        
        Reply with ONLY a JSON object like this example:
        {{
          "is_relevant": true/false,
          "optimize_battery": true/false,
          "optimize_data": true/false,
          "actionable_focus": ["ACTION_TYPE1", "ACTION_TYPE2"]
        }}
        
        The actionable_focus array should ONLY include items from this list:
        {", ".join(ALLOWED_ACTIONABLE_TYPES)}
        
        Select actions that best match the user's intent.
        """
        
        completion = llm_client.chat.completions.create(
            model="llama3-8b-8192",
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
    
    # Customize for specific optimization goals
    if classification["optimize_battery"] and classification["optimize_data"]:
        optimization_goal = """
        OPTIMIZATION GOAL: Optimize both battery life and network data usage
        
        Focus on identifying apps that are consuming excessive battery AND network resources.
        Prioritize actions that will reduce both battery and data consumption.
        """
    elif classification["optimize_battery"]:
        optimization_goal = """
        OPTIMIZATION GOAL: Optimize battery life
        
        Focus on identifying apps that are consuming excessive battery resources.
        Prioritize actions that will extend battery life, even at the expense of some network functionality.
        """
    elif classification["optimize_data"]:
        optimization_goal = """
        OPTIMIZATION GOAL: Optimize network data usage
        
        Focus on identifying apps that are consuming excessive network data.
        Prioritize actions that will reduce data consumption, even at the expense of some battery life.
        """
    else:
        # Default goal if classification was relevant but didn't specify goals
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
       - type: the type of action (MUST be one of these EXACT values: {", ".join(ALLOWED_ACTIONABLE_TYPES)})
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