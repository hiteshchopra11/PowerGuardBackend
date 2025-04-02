from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DeviceDataSchema(BaseModel):
    device_id: str = Field(..., description="Unique identifier for the device")
    timestamp: datetime = Field(..., description="Timestamp of the measurement")
    power_consumption: float = Field(..., description="Power consumption in kWh")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    status: str = Field(..., description="Current status of the device")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device_001",
                "timestamp": "2024-03-20T10:00:00",
                "power_consumption": 2.5,
                "temperature": 25.5,
                "status": "active"
            }
        } 