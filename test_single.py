import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8001"

def test_prompt(prompt="Optimize my battery life"):
    current_time = int(datetime.now().timestamp())
    
    # Create a simplified test payload
    payload = {
        "deviceId": "test_device_001",
        "timestamp": current_time,
        "battery": {
            "level": 25.5,
            "temperature": 38.2,
            "voltage": 3700.0,
            "isCharging": False,
            "chargingType": "None",
            "health": 95,
            "capacity": 4000.0,
            "currentNow": 450.0
        },
        "memory": {
            "totalRam": 8192.0,
            "availableRam": 1024.0,
            "lowMemory": True,
            "threshold": 512.0
        },
        "cpu": {
            "usage": 75.0,
            "temperature": 45.5,
            "frequencies": [1800.0, 2100.0, 2400.0, 1900.0]
        },
        "network": {
            "type": "MOBILE",
            "strength": 65.0,
            "isRoaming": True,
            "dataUsage": {
                "foreground": 175.5,
                "background": 124.5,
                "rxBytes": 328000.0,
                "txBytes": 142000.0
            },
            "activeConnectionInfo": "Mobile-4G",
            "linkSpeed": 40.0,
            "cellularGeneration": "4G"
        },
        "apps": [
            {
                "packageName": "com.example.heavybattery",
                "processName": "com.example.heavybattery",
                "appName": "Heavy Battery App",
                "isSystemApp": False,
                "lastUsed": current_time - 300,
                "foregroundTime": 1800.0,
                "backgroundTime": 3600.0,
                "batteryUsage": 15.5,
                "dataUsage": {
                    "foreground": 5.5,
                    "background": 1.5,
                    "rxBytes": 5000.0,
                    "txBytes": 2000.0
                },
                "memoryUsage": 128.0,
                "cpuUsage": 8.5,
                "notifications": 12,
                "crashes": 0,
                "versionName": "1.2.3",
                "versionCode": 123,
                "targetSdkVersion": 30,
                "installTime": current_time - 86400,
                "updatedTime": current_time - 3600
            }
        ],
        "prompt": prompt
    }
    
    print(f"Testing with prompt: '{prompt}'")
    
    try:
        response = requests.post(f"{BASE_URL}/api/analyze", json=payload)
        response.raise_for_status()
        
        # Parse and print the response
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Success: {result.get('success')}")
        
        print("\nActionable Items:")
        for i, action in enumerate(result.get('actionable', [])):
            print(f"  {i+1}. Type: {action.get('type')}")
            print(f"     Package: {action.get('packageName')}")
            print(f"     Description: {action.get('description')}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")
        return None

if __name__ == "__main__":
    # Test with a battery optimization prompt
    test_prompt("Optimize my battery life") 