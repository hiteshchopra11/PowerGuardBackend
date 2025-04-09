import json
import time
import requests
import sys

# Base device data template with all required fields
BASE_DEVICE_DATA = {
    "deviceId": "test-device-001",
    "timestamp": int(time.time()),
    "battery": {
        "level": 50,
        "health": 85,
        "temperature": 38,
        "voltage": 3800,
        "isCharging": False,
        "chargingType": "none",
        "capacity": 4000,
        "currentNow": 500
    },
    "memory": {
        "totalRam": 6000000000,
        "availableRam": 2500000000,
        "lowMemory": False,
        "threshold": 500000000
    },
    "cpu": {
        "usage": 45,
        "temperature": 40,
        "frequencies": [1800000, 2000000, 2200000, 1900000]
    },
    "network": {
        "type": "wifi",
        "strength": 85,
        "isRoaming": False,
        "dataUsage": {
            "foreground": 1200,
            "background": 300,
            "rxBytes": 800000000,
            "txBytes": 200000000
        },
        "activeConnectionInfo": "wifi",
        "linkSpeed": 300,
        "cellularGeneration": "none"
    },
    "apps": [
        {
            "packageName": "com.whatsapp",
            "processName": "com.whatsapp",
            "appName": "WhatsApp",
            "batteryUsage": 15,
            "dataUsage": {
                "foreground": 80,
                "background": 40,
                "rxBytes": 60000000,
                "txBytes": 20000000
            },
            "foregroundTime": 3600,
            "backgroundTime": 7200,
            "memoryUsage": 200000000,
            "cpuUsage": 12,
            "notifications": 25,
            "crashes": 0,
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 300,
            "versionName": "2.22.15.12",
            "versionCode": 221512,
            "targetSdkVersion": 31,
            "installTime": int(time.time()) - 5000000,
            "updatedTime": int(time.time()) - 1000000
        },
        {
            "packageName": "com.google.android.gm",
            "processName": "com.google.android.gm",
            "appName": "Gmail",
            "batteryUsage": 18,
            "dataUsage": {
                "foreground": 120,
                "background": 60,
                "rxBytes": 100000000,
                "txBytes": 30000000
            },
            "foregroundTime": 2500,
            "backgroundTime": 6000,
            "memoryUsage": 180000000,
            "cpuUsage": 10,
            "notifications": 30,
            "crashes": 0,
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 400,
            "versionName": "2023.05.28",
            "versionCode": 20230528,
            "targetSdkVersion": 33,
            "installTime": int(time.time()) - 4500000,
            "updatedTime": int(time.time()) - 900000
        },
        {
            "packageName": "com.google.android.apps.maps",
            "processName": "com.google.android.apps.maps",
            "appName": "Google Maps",
            "batteryUsage": 20,
            "dataUsage": {
                "foreground": 150,
                "background": 50,
                "rxBytes": 120000000,
                "txBytes": 30000000
            },
            "foregroundTime": 1200,
            "backgroundTime": 3600,
            "memoryUsage": 350000000,
            "cpuUsage": 15,
            "notifications": 5,
            "crashes": 1,
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 1800,
            "versionName": "11.68.0",
            "versionCode": 116800,
            "targetSdkVersion": 33,
            "installTime": int(time.time()) - 8000000,
            "updatedTime": int(time.time()) - 1500000
        },
        {
            "packageName": "com.facebook.katana",
            "processName": "com.facebook.katana",
            "appName": "Facebook",
            "batteryUsage": 25,
            "dataUsage": {
                "foreground": 200,
                "background": 50,
                "rxBytes": 180000000,
                "txBytes": 50000000
            },
            "foregroundTime": 2400,
            "backgroundTime": 9000,
            "memoryUsage": 400000000,
            "cpuUsage": 18,
            "notifications": 40,
            "crashes": 2,
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 600,
            "versionName": "405.0.0.0.15",
            "versionCode": 405015,
            "targetSdkVersion": 32,
            "installTime": int(time.time()) - 10000000,
            "updatedTime": int(time.time()) - 2000000
        },
        {
            "packageName": "com.spotify.music",
            "processName": "com.spotify.music",
            "appName": "Spotify",
            "batteryUsage": 10,
            "dataUsage": {
                "foreground": 250,
                "background": 50,
                "rxBytes": 220000000,
                "txBytes": 10000000
            },
            "foregroundTime": 4500,
            "backgroundTime": 1800,
            "memoryUsage": 280000000,
            "cpuUsage": 8,
            "notifications": 15,
            "crashes": 0,
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 120,
            "versionName": "8.7.70.835",
            "versionCode": 87070835,
            "targetSdkVersion": 33,
            "installTime": int(time.time()) - 7000000,
            "updatedTime": int(time.time()) - 500000
        },
        {
            "packageName": "com.netflix.mediaclient",
            "processName": "com.netflix.mediaclient",
            "appName": "Netflix",
            "batteryUsage": 30,
            "dataUsage": {
                "foreground": 400,
                "background": 100,
                "rxBytes": 450000000,
                "txBytes": 5000000
            },
            "foregroundTime": 3000,
            "backgroundTime": 600,
            "memoryUsage": 450000000,
            "cpuUsage": 22,
            "notifications": 8,
            "crashes": 1,
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 3600,
            "versionName": "8.53.0",
            "versionCode": 85300,
            "targetSdkVersion": 33,
            "installTime": int(time.time()) - 6000000,
            "updatedTime": int(time.time()) - 800000
        }
    ],
    "deviceInfo": {
        "manufacturer": "Google",
        "model": "Pixel 6",
        "osVersion": "14",
        "sdkVersion": 33,
        "screenOnTime": 12500
    },
    "settings": {
        "powerSaveMode": False,
        "dataSaver": False,
        "batteryOptimization": True,
        "adaptiveBattery": True,
        "autoSync": True
    },
    "prompt": ""
}

def test_single_scenario(prompt, battery_level, data_remaining):
    """Test a single scenario with the specified prompt, battery level, and data remaining."""
    print(f"\nTesting: '{prompt}' with Battery: {battery_level}%, Data Remaining: {data_remaining}MB")
    
    # Create device data with specific battery and data values
    device_data = json.loads(json.dumps(BASE_DEVICE_DATA))  # Deep copy
    device_data["prompt"] = prompt
    device_data["battery"]["level"] = battery_level
    
    # Set data usage to simulate remaining data
    total_data = 3000  # Assume 3GB total monthly data
    used_data = total_data - data_remaining
    device_data["network"]["dataUsage"]["foreground"] = used_data * 0.7  # 70% used in foreground
    device_data["network"]["dataUsage"]["background"] = used_data * 0.3  # 30% used in background
    device_data["network"]["dataUsage"]["rxBytes"] = int(device_data["network"]["dataUsage"]["foreground"] * 1000000)
    device_data["network"]["dataUsage"]["txBytes"] = int(device_data["network"]["dataUsage"]["background"] * 500000)
    
    test_result = {
        "prompt": prompt,
        "battery_level": battery_level,
        "data_remaining": data_remaining,
        "success": False
    }
    
    try:
        # Call the API
        print("Calling API...")
        response = requests.post(
            "http://localhost:8000/api/analyze",
            json=device_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            test_result["success"] = True
            test_result["response"] = data
            
            # Extract key information
            insights = data.get("insights", [])
            actionables = data.get("actionable", [])
            
            # Check focus based on battery and data levels
            battery_actionables = [a for a in actionables if "BATTERY" in a.get("type", "") or a.get("type") == "OPTIMIZE_BATTERY"]
            data_actionables = [a for a in actionables if "DATA" in a.get("type", "") or a.get("type") == "ENABLE_DATA_SAVER"]
            
            test_result["battery_action_count"] = len(battery_actionables)
            test_result["data_action_count"] = len(data_actionables)
            
            # Determine if the focus is correct based on the scenario
            battery_critical = battery_level <= 20
            data_critical = data_remaining <= 100
            
            if battery_critical and data_critical:
                # Both low - should have both types of actions
                test_result["expected_focus"] = "both"
                test_result["correct_focus"] = len(battery_actionables) > 0 and len(data_actionables) > 0
            elif battery_critical:
                # Low battery, high data - should focus on battery
                test_result["expected_focus"] = "battery"
                test_result["correct_focus"] = len(battery_actionables) > len(data_actionables)
            elif data_critical:
                # High battery, low data - should focus on data
                test_result["expected_focus"] = "data"
                test_result["correct_focus"] = len(data_actionables) > len(battery_actionables)
            else:
                # Both high - general optimization
                test_result["expected_focus"] = "balanced"
                test_result["correct_focus"] = True
            
            print(f"Focus correct: {test_result['correct_focus']} (Battery actions: {test_result['battery_action_count']}, Data actions: {test_result['data_action_count']})")
            
            # Print all actionables
            print("\nActionables:")
            for action in actionables:
                print(f"  - Type: {action.get('type')}")
                print(f"    Description: {action.get('description')}")
                print(f"    Reason: {action.get('reason')}")
                print("")
            
            # Print strategy insights
            strategy_insights = [i for i in insights if i.get("type") == "Strategy"]
            if strategy_insights:
                print("\nStrategy Insight:")
                print(f"  Title: {strategy_insights[0].get('title')}")
                print(f"  Description: {strategy_insights[0].get('description')}")
            
        elif response.status_code == 429:
            print(f"Rate limit exceeded.")
            test_result["error"] = f"API returned status code {response.status_code}"
        else:
            print(f"API Error: {response.status_code}")
            test_result["error"] = f"API returned status code {response.status_code}"
    except Exception as e:
        print(f"Request Error: {str(e)}")
        test_result["error"] = f"Request failed: {str(e)}"
    
    return test_result

def main():
    # Check command line arguments
    if len(sys.argv) < 4:
        print("Usage: python test_single_scenario.py \"<prompt>\" <battery_level> <data_remaining>")
        print("Example: python test_single_scenario.py \"Optimize my device\" 15 50")
        return
    
    # Parse command line arguments
    prompt = sys.argv[1]
    try:
        battery_level = float(sys.argv[2])
        data_remaining = float(sys.argv[3])
    except ValueError:
        print("Battery level and data remaining must be numbers")
        return
    
    # Run the test
    result = test_single_scenario(prompt, battery_level, data_remaining)
    
    # Save the result to a file
    output_file = f"scenario_result_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResult saved to {output_file}")

if __name__ == "__main__":
    main() 