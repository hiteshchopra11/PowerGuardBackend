"""Device data schemas for PowerGuard API."""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Any
from datetime import datetime


class BatteryInfo(BaseModel):
    """Battery information schema."""
    level: float
    temperature: float
    voltage: float
    isCharging: bool
    chargingType: str
    health: int
    capacity: float
    currentNow: float
    
    @model_validator(mode='after')
    def validate_negative_values(self):
        if self.temperature == -1:
            self.temperature = 0.0
        return self


class MemoryInfo(BaseModel):
    """Memory information schema."""
    totalRam: float
    availableRam: float
    lowMemory: bool
    threshold: float


class DataUsageInfo(BaseModel):
    """Data usage information schema."""
    foreground: float
    background: float
    rxBytes: float
    txBytes: float


class CpuInfo(BaseModel):
    """CPU information schema."""
    usage: Optional[float] = None
    temperature: Optional[float] = None
    frequencies: List[float] = []
    
    @model_validator(mode='after')
    def validate_negative_values(self):
        if hasattr(self, 'usage') and self.usage == -1:
            self.usage = None
        if hasattr(self, 'temperature') and self.temperature == -1:
            self.temperature = None
        return self


class NetworkInfo(BaseModel):
    """Network information schema."""
    type: str
    strength: Optional[float] = None
    isRoaming: bool
    dataUsage: DataUsageInfo
    activeConnectionInfo: str
    linkSpeed: float
    cellularGeneration: str
    
    @model_validator(mode='after')
    def validate_negative_values(self):
        if hasattr(self, 'strength') and self.strength == -1:
            self.strength = None
        return self


class AppInfo(BaseModel):
    """Application information schema."""
    packageName: str
    processName: str
    appName: str
    isSystemApp: bool
    lastUsed: float
    foregroundTime: float
    backgroundTime: float
    batteryUsage: Optional[float] = None
    dataUsage: DataUsageInfo
    memoryUsage: Optional[float] = None
    cpuUsage: Optional[float] = None
    notifications: int
    crashes: int
    versionName: str
    versionCode: int
    targetSdkVersion: int
    installTime: float
    updatedTime: float
    alarmWakeups: Optional[int] = 0
    currentPriority: Optional[str] = "UNKNOWN"
    bucket: Optional[str] = "ACTIVE"
    
    @model_validator(mode='after')
    def validate_negative_values(self):
        if hasattr(self, 'batteryUsage') and self.batteryUsage == -1:
            self.batteryUsage = None
        if hasattr(self, 'cpuUsage') and self.cpuUsage == -1:
            self.cpuUsage = None
        if hasattr(self, 'memoryUsage') and self.memoryUsage == -1:
            self.memoryUsage = None
        return self


class DeviceInfo(BaseModel):
    """Device information schema."""
    manufacturer: str
    model: str
    osVersion: str
    sdkVersion: int
    screenOnTime: int = 0


class SettingsData(BaseModel):
    """Device settings schema."""
    powerSaveMode: bool = False
    dataSaver: bool = False
    batteryOptimization: bool = False
    adaptiveBattery: bool = False
    autoSync: bool = True


class DeviceData(BaseModel):
    """Main device data schema."""
    deviceId: str
    timestamp: float
    battery: BatteryInfo
    memory: MemoryInfo
    cpu: CpuInfo
    network: NetworkInfo
    apps: List[AppInfo]
    deviceInfo: Optional[DeviceInfo] = None
    settings: Optional[SettingsData] = None
    prompt: str
    currentDataMb: Optional[float] = None
    totalDataMb: Optional[float] = None
    pastUsagePatterns: Optional[List[str]] = []

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Ensure timestamp is a number
        if isinstance(data['timestamp'], str):
            try:
                dt = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                data['timestamp'] = float(dt.timestamp())
            except ValueError:
                data['timestamp'] = float(datetime.now().timestamp())
        return data
    
    @model_validator(mode='after')
    def filter_invalid_apps(self):
        # Filter out apps with all invalid data
        valid_apps = []
        for app in self.apps:
            # Keep if it has any valid data
            has_valid_data = (
                app.batteryUsage is not None or 
                app.memoryUsage is not None or
                app.cpuUsage is not None or
                (hasattr(app.dataUsage, 'rxBytes') and app.dataUsage.rxBytes is not None and app.dataUsage.rxBytes > 0) or 
                (hasattr(app.dataUsage, 'txBytes') and app.dataUsage.txBytes is not None and app.dataUsage.txBytes > 0) or
                (app.foregroundTime is not None and app.foregroundTime > 0) or 
                (app.backgroundTime is not None and app.backgroundTime > 0)
            )
            if has_valid_data:
                valid_apps.append(app)
        
        self.apps = valid_apps
        return self


# Re-export for backwards compatibility
__all__ = [
    'DeviceData',
    'BatteryInfo', 
    'MemoryInfo',
    'CpuInfo',
    'NetworkInfo',
    'AppInfo',
    'DeviceInfo',
    'SettingsData',
    'DataUsageInfo'
]