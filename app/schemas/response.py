"""Response schemas for PowerGuard API."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ActionableItemSchema(BaseModel):
    """Schema for actionable items in response."""
    id: str
    type: str
    description: str
    package_name: Optional[str] = None
    estimated_battery_savings: Optional[float] = 0.0
    estimated_data_savings: Optional[float] = 0.0
    severity: Optional[int] = 1
    new_mode: Optional[str] = None
    enabled: Optional[bool] = True
    throttle_level: Optional[str] = None
    reason: str
    parameters: Dict[str, Any]


class InsightItemSchema(BaseModel):
    """Schema for insight items in response."""
    type: str
    title: str
    description: str
    severity: str


class EstimatedSavingsSchema(BaseModel):
    """Schema for estimated savings."""
    batteryMinutes: float
    dataMB: float


class ActionResponseSchema(BaseModel):
    """Main response schema for analysis endpoint."""
    id: str
    success: bool
    timestamp: float
    message: str
    responseType: str = "BATTERY_OPTIMIZATION"
    actionable: List[ActionableItemSchema]
    insights: List[InsightItemSchema]
    batteryScore: float = Field(ge=0, le=100, description="Battery health score from 0-100")
    dataScore: float = Field(ge=0, le=100, description="Data usage efficiency score from 0-100")
    performanceScore: float = Field(ge=0, le=100, description="Overall performance score from 0-100")
    estimatedSavings: EstimatedSavingsSchema


class UsagePatternsResponseSchema(BaseModel):
    """Response schema for usage patterns."""
    patterns: Dict[str, str]


class DatabaseEntrySchema(BaseModel):
    """Schema for database entries."""
    id: int
    device_id: str
    package_name: str
    pattern: str
    timestamp: str
    raw_timestamp: int 