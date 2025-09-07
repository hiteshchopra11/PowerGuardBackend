"""Usage pattern database model."""

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from app.core.database import Base


class UsagePattern(Base):
    """Database model for storing device usage patterns."""
    
    __tablename__ = "usage_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    deviceId = Column(String, index=True, nullable=False)
    packageName = Column(String, index=True, nullable=False)
    pattern = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('deviceId', 'packageName', name='uix_device_package'),
    )