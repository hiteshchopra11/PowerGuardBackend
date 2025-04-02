from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import datetime

class AppUsageInfo(BaseModel):
    package_name: str
    app_name: str
    foreground_time_ms: int
    background_time_ms: int
    last_used: int
    launch_count: int

class BatteryStats(BaseModel):
    level: int
    temperature: float
    is_charging: bool
    charging_type: str
    voltage: int
    health: str
    estimated_remaining_time: Optional[int] = None

class AppNetworkInfo(BaseModel):
    package_name: str
    data_usage_bytes: int
    wifi_usage_bytes: int

class NetworkUsage(BaseModel):
    app_network_usage: List[AppNetworkInfo]
    wifi_connected: bool
    mobile_data_connected: bool
    network_type: str

class WakeLockInfo(BaseModel):
    package_name: str
    wake_lock_name: str
    time_held_ms: int

class DeviceData(BaseModel):
    app_usage: List[AppUsageInfo]
    battery_stats: BatteryStats
    network_usage: NetworkUsage
    wake_locks: List[WakeLockInfo]
    device_id: str
    timestamp: Union[str, int]

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if isinstance(data['timestamp'], str):
            try:
                dt = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                data['timestamp'] = int(dt.timestamp())
            except ValueError:
                data['timestamp'] = int(datetime.now().timestamp())
        return data

class Actionable(BaseModel):
    type: str
    app: Optional[str] = None
    new_mode: Optional[str] = None
    reason: Optional[str] = None
    enabled: Optional[bool] = None

class ActionResponse(BaseModel):
    actionables: List[Actionable]
    summary: str
    usage_patterns: Dict[str, str]
    timestamp: int 