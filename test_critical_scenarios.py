import unittest
import json
import sys
import os

# Add the project directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.strategy_analyzer import determine_strategy, balance_strategy_priority
from app.config.strategy_config import DEFAULT_DAILY_DATA

class TestCriticalBatteryScenarios(unittest.TestCase):
    """Test specific scenarios for critical battery and data conditions"""
    
    def test_trip_with_low_battery_maps(self):
        """Test the scenario: I'm on a trip with 10% battery and need Maps"""
        prompt = "I'm on a trip with 10% battery and need Maps"
        
        # Create test device data with critically low battery
        device_data = {
            "battery": {
                "level": 10,
                "charging": False
            },
            "network": {
                "dataUsage": {
                    "foreground": 500,
                    "background": 500
                }
            },
            "apps": [
                {
                    "packageName": "com.google.android.apps.maps",
                    "appName": "Google Maps",
                    "batteryUsage": 15,
                    "dataUsage": 50
                },
                {
                    "packageName": "com.example.otherdummy",
                    "appName": "Other App",
                    "batteryUsage": 5,
                    "dataUsage": 10
                }
            ],
            "data": {
                "remaining_mb": 500,
                "plan_mb": 2000
            }
        }
        
        # Determine strategy
        strategy = determine_strategy(device_data, prompt)
        
        # Verify the strategy is appropriate
        self.assertEqual(strategy["focus"], "battery", "Focus should be on battery for critical 10% scenario")
        self.assertEqual(strategy["aggressiveness"], "very_aggressive", "Aggressiveness should be very_aggressive for 10% battery")
        self.assertTrue(strategy["show_battery_savings"], "Should show battery savings for critical battery")
        self.assertTrue("navigation" in strategy["critical_categories"] or "com.google.android.apps.maps" in strategy["critical_apps"], 
                    "Maps should be identified as critical")
        
        print("Strategy for 10% battery scenario:")
        print(json.dumps(strategy, indent=2))
    
    def test_high_battery_low_data(self):
        """Test the scenario: High battery but low data remaining"""
        prompt = "I need to use my phone for the rest of the day"
        
        # Create test device data with high battery but low data
        device_data = {
            "battery": {
                "level": 85,
                "charging": False
            },
            "network": {
                "dataUsage": {
                    "foreground": 1700,
                    "background": 300
                }
            },
            "data": {
                "remaining_mb": 200,   # Only 200MB left
                "plan_mb": 2000
            },
            "apps": []
        }
        
        # Determine strategy
        strategy = determine_strategy(device_data, prompt)
        
        # Verify the strategy is appropriate
        self.assertEqual(strategy["focus"], "network", "Focus should be on network for high battery + low data scenario")
        self.assertTrue(strategy["show_data_savings"], "Should show data savings for low data")
        self.assertIn(strategy["aggressiveness"], ["aggressive", "very_aggressive"], 
                      "Aggressiveness should be high for low data")
        
        print("Strategy for high battery + low data scenario:")
        print(json.dumps(strategy, indent=2))
    
    def test_balance_strategy_priority_directly(self):
        """Test the balance_strategy_priority function directly"""
        prompt = "I'm on a trip with 10% battery and need Maps"
        
        # Initial strategy with mixed focus
        strategy = {
            "focus": "both",
            "aggressiveness": "moderate",
            "show_battery_savings": True,
            "show_data_savings": True,
            "critical_categories": ["navigation"]
        }
        
        # Device data with critical battery
        device_data = {
            "battery": {
                "level": 10,
                "charging": False
            },
            "data": {
                "remaining_mb": 500,
                "plan_mb": 2000
            }
        }
        
        # Apply balancing
        updated_strategy = balance_strategy_priority(prompt, device_data, strategy)
        
        # Check that critical battery is properly handled
        self.assertEqual(updated_strategy["focus"], "battery", 
                         "Critical 10% battery should override to battery focus")
        self.assertEqual(updated_strategy["aggressiveness"], "very_aggressive",
                         "Critical battery should use very aggressive strategy")

if __name__ == "__main__":
    unittest.main() 