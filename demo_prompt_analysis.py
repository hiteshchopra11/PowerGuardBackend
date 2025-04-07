import sys
import os
import json
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

# Add parent directory to path to allow imports from app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.llm_service import analyze_device_data
from app.utils.actionable_generator import is_information_request

# Sample device data
BASE_DEVICE_DATA = {
    "deviceId": "demo-device-001",
    "timestamp": 1686123456,
    "battery": {
        "level": 50,
        "health": 95,
        "temperature": 35
    },
    "memory": {
        "total": 8000000000,
        "used": 4000000000,
        "free": 4000000000
    },
    "cpu": {
        "usage": 45,
        "temperature": 45
    },
    "network": {
        "dataUsed": 500,
        "wifiEnabled": True,
        "mobileDataEnabled": False
    },
    "apps": [
        {
            "packageName": "com.whatsapp",
            "batteryUsage": 15,
            "dataUsage": 50,
            "foregroundTime": 3600
        },
        {
            "packageName": "com.google.android.apps.maps",
            "batteryUsage": 20,
            "dataUsage": 200,
            "foregroundTime": 1800
        },
        {
            "packageName": "com.example.app1",
            "batteryUsage": 25,
            "dataUsage": 150,
            "foregroundTime": 900
        },
        {
            "packageName": "com.example.app2",
            "batteryUsage": 10,
            "dataUsage": 75,
            "foregroundTime": 600
        },
        {
            "packageName": "com.example.app3",
            "batteryUsage": 5,
            "dataUsage": 300,
            "foregroundTime": 300
        }
    ]
}

# Test scenarios
SCENARIOS = [
    {
        "name": "Information Request - Battery",
        "prompt": "What apps are using the most battery?",
        "battery_level": 75,
        "expected_type": "Information Request"
    },
    {
        "name": "Information Request - Data",
        "prompt": "Show me my top data consuming apps",
        "battery_level": 85,
        "expected_type": "Information Request"
    },
    {
        "name": "Optimization - Low Battery",
        "prompt": "Save my battery, I'm running low",
        "battery_level": 15,
        "expected_type": "Optimization Request"
    },
    {
        "name": "Optimization - Critical Apps",
        "prompt": "I need maps and messages for my trip",
        "battery_level": 40,
        "expected_type": "Optimization Request"
    },
    {
        "name": "Optimization - Time Constraint",
        "prompt": "Make my battery last for 5 hours",
        "battery_level": 25,
        "expected_type": "Optimization Request"
    },
    {
        "name": "Optimization - Data Constraint",
        "prompt": "I only have 200MB of data left, help me save it",
        "battery_level": 60,
        "expected_type": "Optimization Request"
    },
    {
        "name": "Complex Scenario",
        "prompt": "I'm traveling for 3 hours with 10% battery and need maps and WhatsApp",
        "battery_level": 10,
        "expected_type": "Optimization Request"
    }
]

def run_demo():
    """Run the demo for different prompt analysis scenarios."""
    # Create mock DB session
    mock_db = MagicMock()
    mock_db.query = MagicMock(return_value=MagicMock())
    mock_db.query().filter = MagicMock(return_value=MagicMock())
    mock_db.query().filter().order_by = MagicMock(return_value=MagicMock())
    mock_db.query().filter().order_by().all = MagicMock(return_value=[])
    
    print("=" * 80)
    print("PowerGuard AI Backend - Prompt Analysis Demo")
    print("=" * 80)
    
    for scenario in SCENARIOS:
        print("\n" + "=" * 80)
        print(f"SCENARIO: {scenario['name']}")
        print(f"PROMPT: \"{scenario['prompt']}\"")
        print(f"BATTERY: {scenario['battery_level']}%")
        print("-" * 80)
        
        # Create device data for this scenario
        device_data = BASE_DEVICE_DATA.copy()
        device_data["battery"] = device_data["battery"].copy()
        device_data["battery"]["level"] = scenario["battery_level"]
        device_data["prompt"] = scenario["prompt"]
        
        # Classify the prompt
        is_info = is_information_request(scenario["prompt"])
        print(f"CLASSIFIED AS: {'Information Request' if is_info else 'Optimization Request'}")
        
        # Process the request
        response = analyze_device_data(device_data, mock_db)
        
        # Print summary of actionables
        actionables = response["actionable"]
        print(f"ACTIONABLES: {len(actionables)} item(s)")
        if actionables:
            # Group by type
            action_types = {}
            for action in actionables:
                action_type = action["type"]
                if action_type not in action_types:
                    action_types[action_type] = 0
                action_types[action_type] += 1
            
            # Print summary
            for action_type, count in action_types.items():
                print(f"  - {action_type}: {count}")
            
            # Print critical apps being protected
            critical_apps = [a for a in actionables if a["newMode"] == "normal"]
            if critical_apps:
                print("\nCRITICAL APPS PROTECTED:")
                for app in critical_apps:
                    print(f"  - {app['packageName']}")
        
        # Print insights
        insights = response["insights"]
        print(f"\nINSIGHTS: {len(insights)} item(s)")
        for insight in insights:
            print(f"  - {insight['title']}")
        
        # Print estimated savings
        savings = response["estimatedSavings"]
        if savings["batteryMinutes"] > 0:
            print(f"\nESTIMATED BATTERY SAVINGS: {savings['batteryMinutes']} minutes")
        if savings["dataMB"] > 0:
            print(f"ESTIMATED DATA SAVINGS: {savings['dataMB']} MB")

if __name__ == "__main__":
    run_demo() 