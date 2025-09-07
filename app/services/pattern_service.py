"""Service for managing usage patterns."""

import logging
from typing import Dict, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.usage_pattern_repository import UsagePatternRepository
from app.core.exceptions import DatabaseException

logger = logging.getLogger('powerguard_pattern_service')


class PatternService:
    """Service for managing usage patterns."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsagePatternRepository(db)
    
    def get_patterns_for_device(self, device_id: str) -> Dict[str, str]:
        """Get usage patterns for a specific device."""
        try:
            return self.repository.get_patterns_as_dict(device_id)
        except Exception as e:
            logger.error(f"Error getting patterns for device {device_id}: {str(e)}")
            raise DatabaseException(f"Failed to retrieve patterns: {str(e)}")
    
    def store_device_patterns(self, device_data: Dict, strategy: Dict) -> None:
        """Store usage patterns for device apps."""
        try:
            device_id = device_data.get("deviceId")
            if not device_id:
                logger.warning("Cannot store patterns: Missing device ID")
                return
            
            apps = device_data.get("apps", [])
            timestamp = int(datetime.now().timestamp())
            
            for app in apps:
                package_name = app.get("packageName")
                if not package_name:
                    continue
                
                pattern = self._generate_usage_pattern(app, strategy)
                self.repository.upsert_pattern(device_id, package_name, pattern, timestamp)
                
            logger.info(f"Stored usage patterns for {len(apps)} apps")
            
        except Exception as e:
            logger.error(f"Error storing usage patterns: {str(e)}")
            raise DatabaseException(f"Failed to store patterns: {str(e)}")
    
    def get_all_entries(self) -> List[Dict]:
        """Get all database entries with formatted timestamps."""
        try:
            patterns = self.repository.get_all()
            result = []
            
            for pattern in patterns:
                result.append({
                    "id": pattern.id,
                    "device_id": pattern.deviceId,
                    "package_name": pattern.packageName,
                    "pattern": pattern.pattern,
                    "timestamp": datetime.fromtimestamp(pattern.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                    "raw_timestamp": pattern.timestamp
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting all entries: {str(e)}")
            raise DatabaseException(f"Failed to get entries: {str(e)}")
    
    def _generate_usage_pattern(self, app: Dict, strategy: Dict) -> str:
        """Generate usage pattern description for an app."""
        patterns = []
        
        package_name = app.get("packageName")
        battery_usage = app.get("batteryUsage")
        foreground_time = app.get("foregroundTime")
        
        # Handle data usage
        data_usage_obj = app.get("dataUsage", {})
        total_data_usage = 0
        if isinstance(data_usage_obj, dict):
            foreground_data = data_usage_obj.get("foreground", 0)
            background_data = data_usage_obj.get("background", 0)
            total_data_usage = foreground_data + background_data
        
        # Battery usage patterns
        if battery_usage is not None:
            if battery_usage > 20:
                patterns.append("Very high battery usage")
            elif battery_usage > 10:
                patterns.append("High battery usage")
            elif battery_usage > 5:
                patterns.append("Moderate battery usage")
        
        # Data usage patterns
        if total_data_usage > 500:
            patterns.append("Very high data usage")
        elif total_data_usage > 200:
            patterns.append("High data usage")
        elif total_data_usage > 50:
            patterns.append("Moderate data usage")
        
        # Foreground time patterns
        if foreground_time is not None:
            if foreground_time > 3600:  # More than 1 hour
                patterns.append("Frequently used in foreground")
            elif foreground_time > 1800:  # More than 30 minutes
                patterns.append("Moderately used in foreground")
            elif foreground_time < 300:  # Less than 5 minutes
                patterns.append("Rarely used in foreground")
        
        # Check if it's a critical app
        if package_name in strategy.get("critical_apps", []):
            patterns.append("Critical app for user")
        
        return "; ".join(patterns) if patterns else "Normal usage pattern"