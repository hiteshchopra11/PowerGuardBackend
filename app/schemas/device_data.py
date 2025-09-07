# This file contains schema definitions for PowerGuard device data.
# The main models are defined in app/models.py
# This file is kept for compatibility but should reference the main models.

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

# Import the actual models used by the API
from ..models import (
    DeviceData,
    BatteryInfo,
    MemoryInfo,
    CpuInfo,
    NetworkInfo,
    AppInfo,
    DeviceInfo,
    SettingsData,
    DataUsageInfo,
    ActionResponse,
    ActionableItem,
    InsightItem,
    EstimatedSavings
)

# Re-export the main models for backwards compatibility
__all__ = [
    'DeviceData',
    'BatteryInfo', 
    'MemoryInfo',
    'CpuInfo',
    'NetworkInfo',
    'AppInfo',
    'DeviceInfo',
    'SettingsData',
    'DataUsageInfo',
    'ActionResponse',
    'ActionableItem',
    'InsightItem',
    'EstimatedSavings'
]