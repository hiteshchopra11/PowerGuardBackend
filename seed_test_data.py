from app.database import SessionLocal, UsagePattern
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_seed')

def seed_test_data():
    """Add some test data to the database"""
    db = SessionLocal()
    try:
        # Test data for multiple devices
        test_patterns = [
            # Device 1 patterns
            UsagePattern(
                deviceId="android_device_123",
                packageName="com.android.chrome",
                pattern="High background usage during night hours",
                timestamp=int(datetime.now().timestamp())
            ),
            UsagePattern(
                deviceId="android_device_123",
                packageName="com.whatsapp",
                pattern="Frequent background syncs",
                timestamp=int(datetime.now().timestamp())
            ),
            # Device 2 patterns
            UsagePattern(
                deviceId="android_device_456",
                packageName="com.android.chrome",
                pattern="Moderate usage throughout the day",
                timestamp=int(datetime.now().timestamp())
            ),
            UsagePattern(
                deviceId="android_device_456",
                packageName="com.spotify.music",
                pattern="Heavy background music streaming",
                timestamp=int(datetime.now().timestamp())
            ),
            # Device 3 patterns
            UsagePattern(
                deviceId="android_device_789",
                packageName="com.netflix.mediaclient",
                pattern="Evening video streaming sessions",
                timestamp=int(datetime.now().timestamp())
            ),
            UsagePattern(
                deviceId="android_device_789",
                packageName="com.google.android.youtube",
                pattern="Regular short video consumption",
                timestamp=int(datetime.now().timestamp())
            )
        ]
        
        # Add patterns one by one, handling potential duplicates
        added_count = 0
        for pattern in test_patterns:
            try:
                # Check if a pattern for this device and package already exists
                existing = db.query(UsagePattern).filter(
                    UsagePattern.deviceId == pattern.deviceId,
                    UsagePattern.packageName == pattern.packageName
                ).first()
                
                if existing:
                    # Update the existing pattern
                    existing.pattern = pattern.pattern
                    existing.timestamp = pattern.timestamp
                    logger.debug(f"Updated pattern for device {pattern.deviceId}, package {pattern.packageName}")
                else:
                    # Add new pattern
                    db.add(pattern)
                    logger.debug(f"Added new pattern for device {pattern.deviceId}, package {pattern.packageName}")
                
                added_count += 1
            except Exception as e:
                logger.error(f"Error adding pattern: {e}")
        
        db.commit()
        logger.info(f"Test data added successfully! Added/updated {added_count} patterns.")
        logger.info("\nAdded patterns for devices:")
        for device_id in set(p.deviceId for p in test_patterns):
            logger.info(f"- {device_id}")
        
    except Exception as e:
        logger.error(f"Error adding test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_data() 