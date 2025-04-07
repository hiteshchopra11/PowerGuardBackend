"""
Configuration file for optimization strategies used in the PowerGuard system.
This defines thresholds and parameters for different levels of optimization.
"""

import random

# Battery optimization strategies
BATTERY_STRATEGIES = {
    "very_aggressive": {"threshold": 10, "savings_range": (15, 25)},
    "aggressive": {"threshold": 30, "savings_range": (10, 20)},
    "moderate": {"threshold": 80, "savings_range": (5, 15)},
    "minimal": {"threshold": 100, "savings_range": (2, 8)}
}

# Data optimization strategies
DATA_STRATEGIES = {
    "very_aggressive": {"threshold": 500, "savings_range": (150, 250)},
    "aggressive": {"threshold": 1000, "savings_range": (80, 150)},
    "moderate": {"threshold": 1500, "savings_range": (30, 80)},
    "minimal": {"threshold": 2000, "savings_range": (5, 30)}
}

# Aggressiveness levels (for comparison)
AGGRESSIVENESS_LEVELS = {
    "very_aggressive": 4,
    "aggressive": 3,
    "moderate": 2,
    "minimal": 1
}

# Default daily data allowance in MB
DEFAULT_DAILY_DATA = 2000  # 2GB

def get_battery_strategy(battery_level: float) -> str:
    """Get the appropriate battery strategy based on battery level."""
    for strategy, config in sorted(
        BATTERY_STRATEGIES.items(), 
        key=lambda x: x[1]["threshold"]
    ):
        if battery_level <= config["threshold"]:
            return strategy
    return "minimal"

def get_data_strategy(data_remaining: float) -> str:
    """Get the appropriate data strategy based on remaining data (in MB)."""
    for strategy, config in sorted(
        DATA_STRATEGIES.items(), 
        key=lambda x: x[1]["threshold"]
    ):
        if data_remaining <= config["threshold"]:
            return strategy
    return "minimal"

def get_battery_savings(strategy: str, num_critical_apps: int = 0) -> int:
    """
    Get the estimated battery savings in minutes for a given strategy.
    Adjusts based on the number of critical apps being protected.
    
    Note: Estimates are intentionally conservative to manage user expectations.
    """
    min_val, max_val = BATTERY_STRATEGIES.get(
        strategy, 
        BATTERY_STRATEGIES["minimal"]
    )["savings_range"]
    
    # Adjust based on number of critical apps (10% reduction per app)
    adjustment = max(0.5, 1 - (num_critical_apps * 0.1))
    
    base_value = random.randint(min_val, max_val)
    
    # Return the conservative estimate
    return int(base_value * adjustment)

def get_data_savings(strategy: str, num_critical_apps: int = 0) -> int:
    """
    Get the estimated data savings in MB for a given strategy.
    Adjusts based on the number of critical apps being protected.
    
    Note: Estimates are intentionally conservative to manage user expectations.
    """
    min_val, max_val = DATA_STRATEGIES.get(
        strategy, 
        DATA_STRATEGIES["minimal"]
    )["savings_range"]
    
    # Adjust based on number of critical apps (10% reduction per app)
    adjustment = max(0.5, 1 - (num_critical_apps * 0.1))
    
    base_value = random.randint(min_val, max_val)
    
    # Return the conservative estimate
    return int(base_value * adjustment) 