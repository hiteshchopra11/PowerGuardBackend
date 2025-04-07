from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Union, Any
from datetime import datetime

# Battery info model
class BatteryInfo(BaseModel):
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
    totalRam: float
    availableRam: float
    lowMemory: bool
    threshold: float

class DataUsageInfo(BaseModel):
    foreground: float
    background: float
    rxBytes: float
    txBytes: float

class CpuInfo(BaseModel):
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
    manufacturer: str
    model: str
    osVersion: str
    sdkVersion: int
    screenOnTime: int = 0

class SettingsData(BaseModel):
    powerSaveMode: bool = False
    dataSaver: bool = False
    batteryOptimization: bool = False
    adaptiveBattery: bool = False
    autoSync: bool = True

class DeviceData(BaseModel):
    deviceId: str
    timestamp: float
    battery: BatteryInfo
    memory: MemoryInfo
    cpu: CpuInfo
    network: NetworkInfo
    apps: List[AppInfo]
    deviceInfo: Optional[DeviceInfo] = None
    settings: Optional[SettingsData] = None
    prompt: Optional[str] = None

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
                app.dataUsage.rxBytes > 0 or 
                app.dataUsage.txBytes > 0 or
                app.foregroundTime > 0 or 
                app.backgroundTime > 0
            )
            if has_valid_data:
                valid_apps.append(app)
        
        self.apps = valid_apps
        return self

# Other models

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

class Actionable(BaseModel):
    type: str
    app: Optional[str] = None
    new_mode: Optional[str] = None
    reason: Optional[str] = None
    enabled: Optional[bool] = None

# Response Models
class ActionableItem(BaseModel):
    id: str
    type: str
    packageName: Optional[str] = None
    description: str
    reason: str
    newMode: str
    parameters: Dict[str, Any]

class InsightItem(BaseModel):
    type: str
    title: str
    description: str
    severity: str

class EstimatedSavings(BaseModel):
    batteryMinutes: float
    dataMB: float

class ActionResponse(BaseModel):
    id: str
    success: bool
    timestamp: float
    message: str
    actionable: List[ActionableItem]
    insights: List[InsightItem]
    batteryScore: float = Field(ge=0, le=100, description="Battery health score from 0-100")
    dataScore: float = Field(ge=0, le=100, description="Data usage efficiency score from 0-100")
    performanceScore: float = Field(ge=0, le=100, description="Overall performance score from 0-100")
    estimatedSavings: EstimatedSavings
    
    @classmethod
    def example_response(cls, prompt: Optional[str] = None):
        """Create a sample response for testing/documentation purposes"""
        current_time = datetime.now().timestamp()
        
        battery_focus = prompt and ("battery" in prompt.lower() or "power" in prompt.lower())
        data_focus = prompt and ("data" in prompt.lower() or "network" in prompt.lower())
        
        # Default to both if no specific focus or prompt is None
        if not battery_focus and not data_focus:
            battery_focus = True
            data_focus = True
            
        insights = []
        actionable = []
        
        if battery_focus:
            actionable.append(
                ActionableItem(
                    id="bat-1",
                    type="OPTIMIZE_BATTERY",
                    packageName="com.example.heavybattery",
                    description="Optimize battery usage for Heavy Battery App",
                    reason="App is consuming excessive battery",
                    newMode="optimized",
                    parameters={}
                )
            )
            
            insights.append(
                InsightItem(
                    type="BatteryDrain",
                    title="Battery Drain Detected",
                    description="Heavy Battery App is using significant battery resources",
                    severity="high"
                )
            )
            
        if data_focus:
            actionable.append(
                ActionableItem(
                    id="data-1",
                    type="ENABLE_DATA_SAVER",
                    packageName="com.example.heavydata",
                    description="Enable data saver mode for Heavy Data App",
                    reason="App is consuming excessive data",
                    newMode="restricted",
                    parameters={}
                )
            )
            
            insights.append(
                InsightItem(
                    type="DataUsage",
                    title="High Data Usage Detected",
                    description="Heavy Data App is using significant data resources",
                    severity="medium"
                )
            )
            
        return cls(
            id=f"example-{int(current_time)}",
            success=True,
            timestamp=current_time,
            message=f"Analysis completed based on {'prompt' if prompt else 'default settings'}",
            actionable=actionable,
            insights=insights,
            batteryScore=60.0 if battery_focus else 80.0,
            dataScore=60.0 if data_focus else 80.0,
            performanceScore=70.0,
            estimatedSavings=EstimatedSavings(
                batteryMinutes=30.0 if battery_focus else 0.0,
                dataMB=20.0 if data_focus else 0.0
            )
        )