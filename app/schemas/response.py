from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AnalysisResponseSchema(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    analysis: str = Field(..., description="Detailed analysis of device data")
    recommendations: List[str] = Field(..., description="List of improvement recommendations")
    energy_savings: Optional[float] = Field(None, description="Estimated energy savings in kWh")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device_001",
                "timestamp": "2024-03-20T10:00:00",
                "analysis": "Device is operating at 75% efficiency",
                "recommendations": [
                    "Consider upgrading to energy-efficient components",
                    "Schedule maintenance for optimal performance"
                ],
                "energy_savings": 0.5
            }
        } 