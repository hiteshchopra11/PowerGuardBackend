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
    get_top_consuming_apps,
    extract_app_count_from_prompt
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
            "data_constraint": None,
            "optimize_battery": True,
            "optimize_data": True
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
            "data_constraint": 500,
            "optimize_battery": True,
            "optimize_data": True
        }
        
        description = generate_strategy_description(strategy, 10)
        
        # Verify that data constraint takes precedence 
        self.assertTrue("Optimizing data usage with 500MB remaining" in description)
        # Critical apps and time constraint should no longer be in description
        self.assertNotIn("protected critical apps", description.lower())
        self.assertNotIn("whatsapp", description.lower())
        self.assertNotIn("maps", description.lower())
        self.assertNotIn("3 hour", description.lower())
    
    def test_generate_strategy_description_data_focus(self):
        """Test that data-focused strategies prioritize data messaging."""
        # Test with network focus
        strategy = {
            "focus": "network",
            "aggressiveness": "aggressive",
            "critical_apps": ["com.example.app"],
            "time_constraint": 5,
            "data_constraint": None,
            "show_battery_savings": True,
            "show_data_savings": True,
            "optimize_battery": False,
            "optimize_data": True
        }
        
        description = generate_strategy_description(strategy, 100)
        
        # Verify that description starts with data optimization
        self.assertTrue(description.startswith("Optimizing data consumption"))
        
        # Verify no redundant information
        self.assertNotIn("Protected critical apps", description)
        self.assertNotIn("Optimized for 5 hours", description)
        self.assertNotIn("Estimated battery extension", description)
        self.assertNotIn("Estimated data savings", description)
        
        # Test with data constraint
        strategy = {
            "focus": "battery",  # Even with battery focus
            "aggressiveness": "moderate",
            "critical_apps": [],
            "time_constraint": None,
            "data_constraint": 500,  # Data constraint should override
            "show_battery_savings": False,
            "show_data_savings": True,
            "optimize_battery": False,
            "optimize_data": True
        }
        
        description = generate_strategy_description(strategy, 100)
        
        # Verify that description prioritizes data constraint
        self.assertTrue("Optimizing data usage with 500MB remaining" in description)
        self.assertNotIn("As battery is sufficient", description)

    def test_generate_strategy_description_no_redundancy(self):
        """Test that strategy description doesn't include redundant information."""
        strategy = {
            "focus": "both",
            "aggressiveness": "aggressive",
            "critical_apps": ["com.example.app1", "com.example.app2"],
            "time_constraint": 8,
            "data_constraint": None,
            "show_battery_savings": True,
            "show_data_savings": True,
            "calculated_savings": {
                "batteryMinutes": 120,
                "dataMB": 250
            }
        }
        
        description = generate_strategy_description(strategy, 100)
        
        # Verify no redundant information
        self.assertNotIn("Protected critical apps", description)
        self.assertNotIn("Optimized for 8 hours", description)
        self.assertNotIn("Estimated battery extension: 120 minutes", description)
        self.assertNotIn("Estimated data savings: 250 MB", description)
    
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
        
    def test_get_top_consuming_apps_with_none_values(self):
        # Test handling of None values in app usage data
        device_data = {
            "apps": [
                {"packageName": "com.example.app1", "batteryUsage": 25, "dataUsage": 50},
                {"packageName": "com.example.app2", "batteryUsage": None, "dataUsage": 150},
                {"packageName": "com.example.app3", "batteryUsage": 10, "dataUsage": None},
                {"packageName": "com.example.app4", "batteryUsage": 5, "dataUsage": 10},
                {"packageName": "com.example.app5", "batteryUsage": None, "dataUsage": None}
            ]
        }
        
        # Test top battery apps with None values
        battery_apps = get_top_consuming_apps(device_data, "battery", 3)
        self.assertEqual(len(battery_apps), 3)
        self.assertEqual(battery_apps[0]["usage"], 25)
        self.assertEqual(battery_apps[1]["usage"], 10)
        self.assertEqual(battery_apps[2]["usage"], 5)
        
        # Test top data apps with None values
        data_apps = get_top_consuming_apps(device_data, "data", 3)
        self.assertEqual(len(data_apps), 3)
        self.assertEqual(data_apps[0]["usage"], 150)
        self.assertEqual(data_apps[1]["usage"], 50)
        self.assertEqual(data_apps[2]["usage"], 10)

    def test_extract_app_count_from_prompt(self):
        """Test that app count is correctly extracted from various prompt formats."""
        test_cases = [
            # Basic patterns
            ("top 3 apps", 3),
            ("3 top apps", 3),
            ("3 apps using battery", 3),
            ("show me 5 apps", 5),
            ("tell me 4 apps", 4),
            ("list 2 apps", 2),
            
            # Battery patterns
            ("tell me top 4 battery consuming apps", 4),
            ("give me top 3 battery consuming apps", 3),
            
            # Data patterns
            ("tell me top 4 data consuming apps", 4),
            ("give me top 3 data consuming apps", 3),
            ("show me the top 5 data consuming apps", 5),
            ("list the top 2 data consuming apps", 2),
            
            # Edge cases
            ("the top app", 1),
            ("the top battery app", 1),
            ("the top data app", 1),
            ("which app is using most battery", 1),
            ("what app is draining battery", 1),
            ("which app is using most data", 1),
            ("what app is using most data", 1),
            
            # Invalid cases should return default (3)
            ("show me apps", 3),
            ("tell me about battery", 3),
            ("tell me about data usage", 3),
            ("optimize my battery", 3),
            ("optimize my data", 3),
            ("", 3),
            (None, 3),
            
            # Boundary cases
            ("show me 0 apps", 1),  # Should be minimum 1
            ("show me 15 apps", 10),  # Should be maximum 10
        ]
        
        for prompt, expected_count in test_cases:
            with self.subTest(prompt=prompt):
                actual_count = extract_app_count_from_prompt(prompt)
                self.assertEqual(actual_count, expected_count, 
                    f"Failed for prompt '{prompt}': expected {expected_count}, got {actual_count}")

if __name__ == '__main__':
    unittest.main() 