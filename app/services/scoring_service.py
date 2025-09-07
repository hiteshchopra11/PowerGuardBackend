"""Service for calculating device scores."""

import logging
from typing import Dict, Any

logger = logging.getLogger('powerguard_scoring_service')


class ScoringService:
    """Service for calculating device performance scores."""
    
    @staticmethod
    def calculate_battery_score(device_data: Dict[str, Any]) -> float:
        """Calculate battery health score from device data."""
        try:
            battery = device_data.get("battery", {})
            battery_level = battery.get("level", 50)
            battery_health = battery.get("health", 2)
            is_charging = battery.get("isCharging", False)
            temperature = battery.get("temperature", 30)
            
            settings = device_data.get("settings", {})
            power_save_mode = settings.get("powerSaveMode", False) if settings else False
            battery_optimization = settings.get("batteryOptimization", False) if settings else False
            
            # Calculate base score
            base_score = min(100, battery_level + 40)
            
            # Health adjustment
            health_adj = 0
            if battery_health < 2:
                health_adj = -20
            elif battery_health > 2:
                health_adj = 10
            
            # Temperature adjustment
            temp_adj = 0
            if temperature > 40:
                temp_adj = -15
            elif temperature > 35:
                temp_adj = -5
            
            # Settings adjustment
            settings_adj = 0
            if power_save_mode:
                settings_adj += 10
            if battery_optimization:
                settings_adj += 5
            
            # Charging bonus
            charging_adj = 5 if is_charging else 0
            
            score = base_score + health_adj + temp_adj + settings_adj + charging_adj
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating battery score: {str(e)}")
            return 50.0
    
    @staticmethod
    def calculate_data_score(device_data: Dict[str, Any]) -> float:
        """Calculate data usage efficiency score."""
        try:
            network = device_data.get("network", {})
            data_usage = network.get("dataUsage", {})
            background_usage = data_usage.get("background", 0)
            foreground_usage = data_usage.get("foreground", 0)
            network_type = network.get("type", "").lower()
            is_roaming = network.get("isRoaming", False)
            
            settings = device_data.get("settings", {})
            data_saver = settings.get("dataSaver", False) if settings else False
            auto_sync = settings.get("autoSync", True) if settings else True
            
            total_usage = background_usage + foreground_usage
            base_score = 80
            
            if total_usage == 0:
                return 90
            
            # Background ratio adjustment
            bg_ratio = background_usage / total_usage if total_usage > 0 else 0
            bg_adj = 0
            if bg_ratio > 0.7:
                bg_adj = -20
            elif bg_ratio > 0.5:
                bg_adj = -10
            elif bg_ratio < 0.3:
                bg_adj = +10
            
            # Network type adjustment
            network_adj = 0
            if network_type == "wifi":
                network_adj = 15
            elif network_type == "cellular" and is_roaming:
                network_adj = -20
            
            # Settings adjustment
            settings_adj = 0
            if data_saver:
                settings_adj += 15
            if not auto_sync:
                settings_adj += 5
            
            score = base_score + bg_adj + network_adj + settings_adj
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating data score: {str(e)}")
            return 50.0
    
    @staticmethod
    def calculate_performance_score(device_data: Dict[str, Any]) -> float:
        """Calculate general performance score."""
        try:
            memory = device_data.get("memory", {})
            total_ram = memory.get("totalRam", 0)
            available_ram = memory.get("availableRam", 0)
            low_memory = memory.get("lowMemory", False)
            
            cpu = device_data.get("cpu", {})
            cpu_usage = cpu.get("usage")
            
            apps = device_data.get("apps", [])
            crash_count = sum(app.get("crashes", 0) for app in apps)
            
            base_score = 70
            
            # Memory adjustment
            memory_adj = 0
            if total_ram > 0:
                free_memory_percent = (available_ram / total_ram) * 100
                if free_memory_percent < 15:
                    memory_adj = -25
                elif free_memory_percent < 30:
                    memory_adj = -15
                elif free_memory_percent > 60:
                    memory_adj = +15
            
            if low_memory:
                memory_adj -= 20
            
            # CPU adjustment
            cpu_adj = 0
            if cpu_usage is not None:
                if cpu_usage > 70:
                    cpu_adj = -15
                elif cpu_usage < 30:
                    cpu_adj = +10
            
            # Crashes adjustment
            crash_adj = 0
            if crash_count > 3:
                crash_adj = -20
            elif crash_count > 0:
                crash_adj = -10
            
            score = base_score + memory_adj + cpu_adj + crash_adj
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {str(e)}")
            return 50.0