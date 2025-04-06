import requests
import json
from datetime import datetime
import time

# Base URL for the API
BASE_URL = "https://powerguardbackend.onrender.com"

def test_api_with_prompt(prompt=None):
    """Test the API with the given prompt or without a prompt if None"""
    current_time = int(datetime.now().timestamp())
    
    # Create a test payload
    payload = {
        "deviceId": "test_device_001",
        "timestamp": current_time,
        "battery": {
            "level": 25.5,  # Low battery to trigger battery-related actions
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
            "availableRam": 1024.0,  # Low available RAM
            "lowMemory": True,
            "threshold": 512.0
        },
        "cpu": {
            "usage": 75.0,  # High CPU usage
            "temperature": 45.5,  # High temperature
            "frequencies": [1800.0, 2100.0, 2400.0, 1900.0]
        },
        "network": {
            "type": "MOBILE",
            "strength": 65.0,
            "isRoaming": True,  # Roaming to encourage data saving
            "dataUsage": {
                "foreground": 175.5,  # High data usage
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
                "backgroundTime": 3600.0,  # High background usage
                "batteryUsage": 15.5,  # High battery usage
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
            },
            {
                "packageName": "com.example.heavydata",
                "processName": "com.example.heavydata",
                "appName": "Heavy Data App",
                "isSystemApp": False,
                "lastUsed": current_time - 600,
                "foregroundTime": 1200.0,
                "backgroundTime": 1800.0,
                "batteryUsage": 5.5,
                "dataUsage": {
                    "foreground": 85.5,  # High data usage
                    "background": 45.5,  # High background data
                    "rxBytes": 88000.0,
                    "txBytes": 42000.0
                },
                "memoryUsage": 256.0,
                "cpuUsage": 12.5,
                "notifications": 8,
                "crashes": 1,
                "versionName": "2.0.1",
                "versionCode": 201,
                "targetSdkVersion": 31,
                "installTime": current_time - 172800,
                "updatedTime": current_time - 7200
            }
        ]
    }
    
    # Add the prompt if provided
    if prompt is not None:
        payload["prompt"] = prompt
    
    # Make the API call
    prompt_desc = f" with prompt: '{prompt}'" if prompt else " without prompt"
    print(f"\n=== Testing API{prompt_desc} ===")
    
    try:
        response = requests.post(f"{BASE_URL}/api/analyze", json=payload)
        response.raise_for_status()
        
        # Parse and print the response
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response ID: {result.get('id')}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        
        print("\nScores:")
        print(f"  Battery Score: {result.get('batteryScore')}")
        print(f"  Data Score: {result.get('dataScore')}")
        print(f"  Performance Score: {result.get('performanceScore')}")
        
        print("\nEstimated Savings:")
        savings = result.get('estimatedSavings', {})
        print(f"  Battery Minutes: {savings.get('batteryMinutes')}")
        print(f"  Data MB: {savings.get('dataMB')}")
        
        print("\nActionable Items:")
        for i, action in enumerate(result.get('actionable', [])):
            print(f"  {i+1}. Type: {action.get('type')}")
            print(f"     Package: {action.get('packageName')}")
            print(f"     Description: {action.get('description')}")
            print(f"     Reason: {action.get('reason')}")
            print(f"     New Mode: {action.get('newMode')}")
        
        print("\nInsights:")
        for i, insight in enumerate(result.get('insights', [])):
            print(f"  {i+1}. Type: {insight.get('type')}")
            print(f"     Title: {insight.get('title')}")
            print(f"     Severity: {insight.get('severity')}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")
        return None

def main():
    # Test with no prompt
    test_api_with_prompt()
    
    # Test with battery optimization prompt
    test_api_with_prompt("Optimize my battery life")
    
    # Test with data optimization prompt
    test_api_with_prompt("Save my network data")
    
    # Test with both optimizations
    test_api_with_prompt("Save both battery and network data")
    
    # Test with specific action
    test_api_with_prompt("Kill background apps that drain battery")
    
    # Test with negation
    test_api_with_prompt("Optimize battery but not data")
    
    # Test with irrelevant prompt
    test_api_with_prompt("What's the weather like today?")

if __name__ == "__main__":
    # Ensure the server is ready
    time.sleep(2)
    main() 