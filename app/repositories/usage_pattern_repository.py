"""Repository for usage pattern data access."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.usage_pattern import UsagePattern
from .base import BaseRepository


class UsagePatternRepository(BaseRepository[UsagePattern]):
    """Repository for usage pattern operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, UsagePattern)
    
    def get_by_device_id(self, device_id: str) -> List[UsagePattern]:
        """Get all usage patterns for a specific device."""
        return (
            self.db.query(UsagePattern)
            .filter(UsagePattern.deviceId == device_id)
            .order_by(UsagePattern.timestamp.desc())
            .all()
        )
    
    def get_by_device_and_package(self, device_id: str, package_name: str) -> Optional[UsagePattern]:
        """Get usage pattern for specific device and package."""
        return (
            self.db.query(UsagePattern)
            .filter(
                UsagePattern.deviceId == device_id,
                UsagePattern.packageName == package_name
            )
            .first()
        )
    
    def upsert_pattern(self, device_id: str, package_name: str, pattern: str, timestamp: int) -> UsagePattern:
        """Create or update usage pattern."""
        existing = self.get_by_device_and_package(device_id, package_name)
        
        if existing:
            existing.pattern = pattern
            existing.timestamp = timestamp
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            return self.create(
                deviceId=device_id,
                packageName=package_name,
                pattern=pattern,
                timestamp=timestamp
            )
    
    def get_patterns_as_dict(self, device_id: str) -> Dict[str, str]:
        """Get usage patterns as dictionary (package_name -> pattern)."""
        patterns = self.get_by_device_id(device_id)
        
        result = {}
        for pattern in patterns:
            if pattern.packageName not in result:
                result[pattern.packageName] = pattern.pattern
        
        return result