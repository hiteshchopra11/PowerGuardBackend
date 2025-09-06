"""
Configuration file for optimization strategies used in the PowerGuard system.
This defines thresholds and parameters for different levels of optimization.
"""


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

 