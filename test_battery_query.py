import json
import time
import requests
import sys
import traceback

# Base device data template with all required fields
BASE_DEVICE_DATA = {
    "deviceId": "test-device-001",
    "timestamp": int(time.time()),
    "battery": {
        "level": 32,
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