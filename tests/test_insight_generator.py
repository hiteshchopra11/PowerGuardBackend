import unittest
import sys
import os

# Add parent directory to path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.insight_generator import (
    generate_insights,
    generate_optimization_insights,
    generate_information_insights,
    generate_strategy_description,
    get_top_consuming_apps
)

class TestInsightGenerator(unittest.TestCase):
    
    def test_generate_insights_optimization(self):
        # Test optimization request
        strategy = {
            "focus": "battery",
            "aggressiveness": "aggressive",
            "critical_apps": ["com.whatsapp"],
            "critical_categories": ["messaging"],
            "show_battery_savings": True,
            "show_data_savings": False,
            "time_constraint": 5,
            "data_constraint": None
        }
        
        device_data = {
            "battery": {"level": 15},
            "apps": [
                {"packageName": "com.whatsapp", "batteryUsage": 5, "dataUsage": 50, "foregroundTime": 1800},
                {"packageName": "com.example.app", "batteryUsage": 20, "dataUsage": 200, "foregroundTime": 600}
            ]
        }
        
        insights = generate_insights(strategy, device_data, False)
        
        # Verify insights
        self.assertTrue(len(insights) > 0)
        
        # Verify battery warning is included
        battery_warnings = [i for i in insights if i["type"] == "BatteryWarning"]
        self.assertTrue(len(battery_warnings) > 0)
        
        # Verify time constraint is included
        time_insights = [i for i in insights if i["type"] == "TimeConstraint"]
        self.assertTrue(len(time_insights) > 0)
        self.assertTrue("5 Hours" in time_insights[0]["title"])
    
    def test_generate_insights_information(self):
        # Test information request
        strategy = {
            "focus": "both",
            "aggressiveness": "minimal",
            "critical_apps": [],
            "critical_categories": [],
            "show_battery_savings": False,
            "show_data_savings": False,
            "time_constraint": None,
            "data_constraint": None
        }
        
        device_data = {
            "battery": {"level": 85},
            "apps": [
                {"packageName": "com.example.app1", "batteryUsage": 25, "dataUsage": 50},
                {"packageName": "com.example.app2", "batteryUsage": 15, "dataUsage": 150},
                {"packageName": "com.example.app3", "batteryUsage": 10, "dataUsage": 250},
                {"packageName": "com.example.app4", "batteryUsage": 5, "dataUsage": 10},
                {"packageName": "com.example.app5", "batteryUsage": 2, "dataUsage": 5}
            ]
        }
        
        insights = generate_insights(strategy, device_data, True)
        
        # Verify insights
        self.assertTrue(len(insights) > 0)
        
        # Verify battery usage insight is included
        battery_insights = [i for i in insights if i["type"] == "BatteryUsage"]
        self.assertTrue(len(battery_insights) > 0)
        
        # Verify data usage insight is included
        data_insights = [i for i in insights if i["type"] == "DataUsage"]
        self.assertTrue(len(data_insights) > 0)
    
    def test_generate_strategy_description(self):
        # Test strategy description generation
        strategy = {
            "focus": "both",
            "aggressiveness": "very_aggressive",
            "critical_apps": ["com.whatsapp", "com.google.android.apps.maps"],
            "critical_categories": ["messaging", "navigation"],
            "show_battery_savings": True,
            "show_data_savings": True,
            "time_constraint": 3,
            "data_constraint": 500
        }
        
        description = generate_strategy_description(strategy, 10)
        
        # Verify critical components in description
        self.assertTrue("battery is critically low" in description.lower())
        self.assertTrue("protected critical apps" in description.lower())
        self.assertTrue("whatsapp" in description.lower())
        self.assertTrue("maps" in description.lower())
        self.assertTrue("3 hour" in description.lower())
    
    def test_get_top_consuming_apps(self):
        device_data = {
            "apps": [
                {"packageName": "com.example.app1", "batteryUsage": 25, "dataUsage": 50},
                {"packageName": "com.example.app2", "batteryUsage": 15, "dataUsage": 150},
                {"packageName": "com.example.app3", "batteryUsage": 10, "dataUsage": 250},
                {"packageName": "com.example.app4", "batteryUsage": 5, "dataUsage": 10},
                {"packageName": "com.example.app5", "batteryUsage": 2, "dataUsage": 5}
            ]
        }
        
        # Test top battery apps
        battery_apps = get_top_consuming_apps(device_data, "battery", 3)
        self.assertEqual(len(battery_apps), 3)
        self.assertEqual(battery_apps[0]["usage"], 25)
        self.assertEqual(battery_apps[1]["usage"], 15)
        self.assertEqual(battery_apps[2]["usage"], 10)
        
        # Test top data apps
        data_apps = get_top_consuming_apps(device_data, "data", 3)
        self.assertEqual(len(data_apps), 3)
        self.assertEqual(data_apps[0]["usage"], 250)
        self.assertEqual(data_apps[1]["usage"], 150)
        self.assertEqual(data_apps[2]["usage"], 50)

if __name__ == '__main__':
    unittest.main() 