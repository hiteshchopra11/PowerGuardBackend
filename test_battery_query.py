import json
import time
import requests
import sys
import traceback

# Base device data template with all required fields
BASE_DEVICE_DATA = {
    "deviceId": "test_device_001",
    "timestamp": int(time.time()),
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
            "lastUsed": int(time.time()) - 300,
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
            "installTime": int(time.time()) - 86400,
            "updatedTime": int(time.time()) - 3600
        },
        {
            "packageName": "com.example.heavydata",
            "processName": "com.example.heavydata",
            "appName": "Heavy Data App",
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 600,
            "foregroundTime": 1200.0,
            "backgroundTime": 1800.0,
            "batteryUsage": 5.5,
            "dataUsage": {
                "foreground": 85.5,
                "background": 45.5,
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
            "installTime": int(time.time()) - 172800,
            "updatedTime": int(time.time()) - 7200
        },
        {
            "packageName": "com.example.normalapp",
            "processName": "com.example.normalapp",
            "appName": "Normal App",
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 900,
            "foregroundTime": 900.0,
            "backgroundTime": 300.0,
            "batteryUsage": 2.5,
            "dataUsage": {
                "foreground": 10.5,
                "background": 5.0,
                "rxBytes": 15000.0,
                "txBytes": 8000.0
            },
            "memoryUsage": 80.0,
            "cpuUsage": 3.0,
            "notifications": 5,
            "crashes": 0,
            "versionName": "1.5.0",
            "versionCode": 150,
            "targetSdkVersion": 31,
            "installTime": int(time.time()) - 172800,
            "updatedTime": int(time.time()) - 86400
        },
        {
            "packageName": "com.example.mediumbattery",
            "processName": "com.example.mediumbattery",
            "appName": "Medium Battery App",
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 1200,
            "foregroundTime": 1500.0,
            "backgroundTime": 2400.0,
            "batteryUsage": 8.5,
            "dataUsage": {
                "foreground": 15.5,
                "background": 8.0,
                "rxBytes": 25000.0,
                "txBytes": 12000.0
            },
            "memoryUsage": 160.0,
            "cpuUsage": 6.0,
            "notifications": 7,
            "crashes": 0,
            "versionName": "1.8.0",
            "versionCode": 180,
            "targetSdkVersion": 31,
            "installTime": int(time.time()) - 259200,
            "updatedTime": int(time.time()) - 14400
        },
        {
            "packageName": "com.example.lightbattery",
            "processName": "com.example.lightbattery",
            "appName": "Light Battery App",
            "isSystemApp": False,
            "lastUsed": int(time.time()) - 1500,
            "foregroundTime": 600.0,
            "backgroundTime": 1200.0,
            "batteryUsage": 1.5,
            "dataUsage": {
                "foreground": 5.5,
                "background": 2.5,
                "rxBytes": 8000.0,
                "txBytes": 4000.0
            },
            "memoryUsage": 64.0,
            "cpuUsage": 2.0,
            "notifications": 3,
            "crashes": 0,
            "versionName": "1.2.0",
            "versionCode": 120,
            "targetSdkVersion": 30,
            "installTime": int(time.time()) - 345600,
            "updatedTime": int(time.time()) - 21600
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

def test_battery_query():
    """Test the battery query to verify our fix."""
    prompt = "What are the top 3 apps draining my battery?"
    
    print(f"\nTESTING PROMPT: '{prompt}'")
    print("-" * 80)
    
    # Create device data
    device_data = json.loads(json.dumps(BASE_DEVICE_DATA))  # Deep copy
    device_data["prompt"] = prompt
    
    # Add a test app with None battery usage to test our fix
    device_data["apps"].append({
        "packageName": "com.test.app",
        "processName": "com.test.app",
        "appName": "Test App",
        "batteryUsage": None,
        "dataUsage": {
            "foreground": 50,
            "background": 20,
            "rxBytes": 30000000,
            "txBytes": 5000000
        },
        "foregroundTime": 1000,
        "backgroundTime": 500,
        "memoryUsage": 100000000,
        "cpuUsage": 5,
        "notifications": 3,
        "crashes": 0,
        "isSystemApp": False,
        "lastUsed": int(time.time()) - 1000,
        "versionName": "1.0.0",
        "versionCode": 100,
        "targetSdkVersion": 32,
        "installTime": int(time.time()) - 3000000,
        "updatedTime": int(time.time()) - 300000
    })
    
    # Save the test data to a temp file for validation
    with open("temp_device_data.json", "w") as f:
        json.dump(device_data, f)
    
    print(f"Device Data:")
    print(f"  Battery Level: {device_data['battery']['level']}%")
    print(f"  Data Downloaded: {device_data['network']['dataUsage']['foreground']} MB")
    print(f"  Data Uploaded: {device_data['network']['dataUsage']['background']} MB")
    print(f"  Number of Apps: {len(device_data['apps'])}")
    
    # Debug: Print all apps with their battery usage values
    print("\nApp Battery Usage Values (Client-side):")
    for app in device_data["apps"]:
        print(f"  {app['appName']}: batteryUsage={app.get('batteryUsage')}, type={type(app.get('batteryUsage'))}")
    
    # First, check the debug endpoint to see how the server processes our values
    print("\nCALLING DEBUG ENDPOINT...")
    try:
        debug_response = requests.post(
            "http://localhost:8000/api/debug/app-values",
            json=device_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print("\nServer-side App Battery Usage Values:")
            for app_info in debug_data.get("battery_values", []):
                print(f"  {app_info['app_name']}: batteryUsage={app_info['battery_usage']}, type={app_info['battery_usage_type']}")
        else:
            print(f"Debug endpoint error: {debug_response.status_code}, {debug_response.text}")
    except Exception as e:
        print(f"Error calling debug endpoint: {str(e)}")
    
    # Run the curl command and display it
    curl_cmd = f"curl -X POST \"http://localhost:8000/api/analyze\" -H \"Content-Type: application/json\" -d @temp_device_data.json"
    print(f"\nCURL COMMAND: {curl_cmd}")
    
    # Call the API
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8000/api/analyze",
            json=device_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract and display actionables
            actionables = data.get("actionable", [])
            if actionables:
                print("\nACTIONABLES:")
                for i, actionable in enumerate(actionables, 1):
                    print(f"  {i}. {actionable.get('type')}: {actionable.get('description')}")
            else:
                print("\nACTIONABLES: None")
            
            # Extract and display insights
            insights = data.get("insights", [])
            if insights:
                for i, insight in enumerate(insights, 1):
                    print(f"\nINSIGHT {i}:")
                    print(f"  Type: {insight.get('type')}")
                    print(f"  Title: {insight.get('title')}")
                    print(f"  Description: {insight.get('description')}")
                    print(f"  Severity: {insight.get('severity')}")
            else:
                print("\nINSIGHTS: None")
            
            # Display scores
            scores = data.get("scores", {})
            print("\nSCORES:")
            for key, value in scores.items():
                print(f"  {key}: {value}")
            
            # Display savings
            savings = data.get("estimatedSavings", {})
            print("\nESTIMATED SAVINGS:")
            print(f"  Battery: {savings.get('batteryMinutes', 0)} minutes")
            print(f"  Data: {savings.get('dataMB', 0)} MB")
            
            print(f"\nRequest completed in {execution_time:.2f} seconds")
            print(f"\nTest completed successfully!")
            
        else:
            print(f"\nAPI request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\nError during API request: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_battery_query() 