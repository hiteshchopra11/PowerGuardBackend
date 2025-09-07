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
        
 