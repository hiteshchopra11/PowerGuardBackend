import unittest
import sys
import os

# Add parent directory to path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.actionable_generator import (
    generate_actionables,
    generate_global_actionables,
    generate_app_actionables,
    is_information_request
)

class TestActionableGenerator(unittest.TestCase):
    
    def test_is_information_request(self):
        # Test information requests
        self.assertTrue(is_information_request("What apps are using the most battery?"))
        self.assertTrue(is_information_request("Show me the top data consuming apps"))
        self.assertTrue(is_information_request("Tell me which apps are draining my battery"))
        self.assertTrue(is_information_request("List apps using most data"))
        
        # Test optimization requests
        self.assertFalse(is_information_request("Save my battery"))
        self.assertFalse(is_information_request("Optimize my data usage"))
        self.assertFalse(is_information_request("I need to make my battery last longer"))
    
    def test_generate_global_actionables(self):
        # Test battery focus with low battery
        strategy = {"focus": "battery"}
        battery_level = 15
        
        actionables = generate_global_actionables(strategy, battery_level)
        
        # Verify battery saver is recommended
        self.assertTrue(len(actionables) > 0)
        self.assertTrue(any(a["type"] == "ENABLE_BATTERY_SAVER" for a in actionables))
        
        # Test network focus
        strategy = {"focus": "network"}
        battery_level = 90
        
        actionables = generate_global_actionables(strategy, battery_level)
        
        # Verify data saver is recommended
        self.assertTrue(len(actionables) > 0)
        self.assertTrue(any(a["type"] == "ENABLE_DATA_SAVER" for a in actionables))
    
    def test_generate_app_actionables(self):
        # Test with critical apps
        strategy = {
            "focus": "both",
            "aggressiveness": "very_aggressive",
            "critical_apps": ["com.whatsapp"]
        }
        
        apps = [
            {"packageName": "com.whatsapp", "batteryUsage": 10, "dataUsage": 100},
            {"packageName": "com.example.app", "batteryUsage": 20, "dataUsage": 200}
        ]
        
        device_data = {"battery": {"level": 15}}
        
        actionables = generate_app_actionables(strategy, apps, device_data)
        
        # Verify WhatsApp is not restricted
        whatsapp_actionables = [a for a in actionables if a["packageName"] == "com.whatsapp"]
        self.assertTrue(len(whatsapp_actionables) > 0)
        self.assertEqual(whatsapp_actionables[0]["newMode"], "normal")
        
        # Verify other app is restricted
        other_actionables = [a for a in actionables if a["packageName"] == "com.example.app"]
        self.assertTrue(len(other_actionables) > 0)
        self.assertEqual(other_actionables[0]["newMode"], "restricted")
    
    def test_generate_actionables(self):
        # Test complete actionable generation
        strategy = {
            "focus": "both",
            "aggressiveness": "aggressive",
            "critical_apps": ["com.whatsapp"],
            "critical_categories": ["messaging"]
        }
        
        device_data = {
            "battery": {"level": 20},
            "apps": [
                {"packageName": "com.whatsapp", "batteryUsage": 5, "dataUsage": 50},
                {"packageName": "com.example.app1", "batteryUsage": 15, "dataUsage": 150},
                {"packageName": "com.example.app2", "batteryUsage": 10, "dataUsage": 100}
            ]
        }
        
        actionables = generate_actionables(strategy, device_data)
        
        # Verify number of actionables
        # Should have: 
        # - 1 global battery saver
        # - 1 global data saver
        # - 1 for WhatsApp normal mode
        # - 1-2 for each non-critical app (battery/data)
        min_expected = 5  # At minimum
        self.assertTrue(len(actionables) >= min_expected)
        
        # Verify critical app is preserved
        critical_actions = [a for a in actionables if a["packageName"] == "com.whatsapp"]
        self.assertTrue(len(critical_actions) > 0)
        self.assertEqual(critical_actions[0]["newMode"], "normal")
        
        # Verify global actions are included
        global_actions = [a for a in actionables if a["packageName"] == "system"]
        self.assertTrue(len(global_actions) > 0)

if __name__ == '__main__':
    unittest.main() 