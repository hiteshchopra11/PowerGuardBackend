"""
Test file specifically for the 10% battery + Maps scenario
This tests the critical bug case that was fixed
"""
import unittest
import json
import sys
import os

# Add the project directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.strategy_analyzer import determine_strategy, balance_strategy_priority
from app.prompt_analyzer import classify_user_prompt

class Test10PercentBatteryScenario(unittest.TestCase):
    """Test the specific scenario: I'm on a trip with 10% battery and need Maps"""
    
    def setUp(self):
        """Set up the test device data with low battery"""
        self.device_data = {
            "battery": {
                "level": 10,  # Critical battery level
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
                    "packageName": "com.whatsapp",
                    "appName": "WhatsApp",
                    "batteryUsage": 8,
                    "dataUsage": 30
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
    
    def test_critical_battery_with_maps(self):
        """Test the exact prompt from the bug report"""
        prompt = "I'm on a trip with 10% battery and need Maps"
        
        # Run prompt through the analyzer
        classification = classify_user_prompt(prompt)
        
        # Verify prompt classification correctly identified battery focus
        self.assertTrue(classification["optimize_battery"], "Should optimize battery")
        self.assertTrue(classification["is_relevant"], "Should be a relevant prompt")
        
        # Determine strategy
        strategy = determine_strategy(self.device_data, prompt)
        
        # Key assertions for the bug fix
        self.assertEqual(strategy["focus"], "battery", 
                         "Critical 10% battery should set focus to battery")
        self.assertEqual(strategy["aggressiveness"], "very_aggressive", 
                         "Critical battery should be very aggressive")
        self.assertTrue(strategy["show_battery_savings"], 
                        "Should show battery savings for critical battery")
        
        # Verify Maps was correctly identified as critical
        self.assertTrue("navigation" in strategy["critical_categories"] or 
                        "com.google.android.apps.maps" in strategy["critical_apps"], 
                        "Maps should be identified as critical")
        
        print(f"[TEST] Strategy for '{prompt}':")
        print(json.dumps(strategy, indent=2))
    
    def test_multiple_critical_battery_prompts(self):
        """Test various prompts with critical battery to ensure consistent handling"""
        test_prompts = [
            "I'm on a trip with 10% battery and need Maps",
            "My battery is at 10% and I need to use navigation",
            "Low battery but I need to use Google Maps",
            "I need to get home with 10% battery left",
            "Battery almost dead but need directions",
            "Maps needed with critical battery"
        ]
        
        for prompt in test_prompts:
            strategy = determine_strategy(self.device_data, prompt)
            
            # Core assertions for each prompt
            self.assertEqual(strategy["focus"], "battery", 
                            f"For prompt '{prompt}': Critical 10% battery should set focus to battery")
            self.assertEqual(strategy["aggressiveness"], "very_aggressive", 
                            f"For prompt '{prompt}': Aggressiveness should be very_aggressive")
            self.assertTrue(strategy["show_battery_savings"], 
                            f"For prompt '{prompt}': Should show battery savings")
            
            print(f"[TEST] Strategy for '{prompt}':")
            print(json.dumps({
                "focus": strategy["focus"],
                "aggressiveness": strategy["aggressiveness"],
                "critical_categories": strategy["critical_categories"],
                "critical_apps": strategy["critical_apps"]
            }, indent=2))

if __name__ == "__main__":
    unittest.main() 