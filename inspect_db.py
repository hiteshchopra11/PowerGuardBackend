from app.database import SessionLocal, UsagePattern
from datetime import datetime
from collections import defaultdict
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_inspect')

def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to readable format"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def inspect_database():
    """Inspect the database contents and constraints"""
    db = SessionLocal()
    try:
        # Get all unique device IDs
        device_ids = db.query(UsagePattern.device_id).distinct().all()
        device_ids = [d[0] for d in device_ids]
        
        logger.info(f"\n=== Database Inspection Report ===")
        logger.info(f"Total number of devices: {len(device_ids)}")
        
        # Overall statistics
        total_patterns = db.query(UsagePattern).count()
        unique_packages = db.query(UsagePattern.package_name).distinct().count()
        logger.info(f"\nOverall Statistics:")
        logger.info(f"- Total patterns: {total_patterns}")
        logger.info(f"- Unique packages across all devices: {unique_packages}")
        
        # Per-device analysis
        for device_id in device_ids:
            logger.info(f"\n=== Device: {device_id} ===")
            
            # Get patterns for this device
            patterns = db.query(UsagePattern).filter(
                UsagePattern.device_id == device_id
            ).order_by(UsagePattern.timestamp.desc()).all()
            
            logger.info(f"Total patterns for device: {len(patterns)}")
            
            # Group by package name
            package_patterns = defaultdict(list)
            for pattern in patterns:
                package_patterns[pattern.package_name].append(pattern)
            
            logger.info(f"Unique packages for device: {len(package_patterns)}")
            
            # Show patterns for each package
            for package_name, pkg_patterns in package_patterns.items():
                logger.info(f"\nPackage: {package_name}")
                logger.info(f"Number of patterns: {len(pkg_patterns)}")
                
                # Show the most recent pattern
                latest = pkg_patterns[0]
                logger.info(f"Latest pattern ({format_timestamp(latest.timestamp)}):")
                logger.info(f"- {latest.pattern}")
                
                # Show pattern history if available
                if len(pkg_patterns) > 1:
                    logger.info("Pattern history:")
                    for pattern in pkg_patterns[1:3]:  # Show up to 2 previous patterns
                        logger.info(f"- [{format_timestamp(pattern.timestamp)}] {pattern.pattern}")
            
            # Time span analysis
            if patterns:
                oldest = min(p.timestamp for p in patterns)
                newest = max(p.timestamp for p in patterns)
                logger.info(f"\nTime span: {format_timestamp(oldest)} to {format_timestamp(newest)}")
        
        # Cross-device analysis
        logger.info("\n=== Cross-Device Analysis ===")
        package_usage = defaultdict(list)
        for pattern in db.query(UsagePattern).all():
            package_usage[pattern.package_name].append(pattern.device_id)
        
        logger.info("Package usage across devices:")
        for package, devices in package_usage.items():
            logger.info(f"\n{package}:")
            logger.info(f"- Used by {len(devices)} devices")
            logger.info(f"- Device IDs: {', '.join(devices)}")
        
    except Exception as e:
        logger.error(f"Error inspecting database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_database() 