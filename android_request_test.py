import requests
import json
import time

# Sample Android request JSON
android_request = {
  "apps": [
    {
      "appName": "WhatsApp",
      "backgroundTime": 7200,
      "batteryUsage": 15.0,
      "cpuUsage": 12.0,
      "crashes": 0,
      "dataUsage": {
        "background": 40,
        "foreground": 80,
        "rxBytes": 60000000,
        "txBytes": 20000000
      },
      "foregroundTime": 3600,
      "installTime": 1743726957061,
      "isSystemApp": False,
      "lastUsed": int(time.time()) - 300,
      "memoryUsage": 200000000,
      "notifications": 25,
      "packageName": "com.whatsapp",
      "processName": "com.whatsapp",
      "targetSdkVersion": 31,
      "updatedTime": int(time.time()) - 1000000,
      "versionCode": 221512,
      "versionName": "2.22.15.12"
    },
    {
      "appName": "Gmail",
      "backgroundTime": 6000,
      "batteryUsage": -1,  # Invalid value to test handling
      "cpuUsage": -1,  # Invalid value to test handling
      "crashes": 0,
      "dataUsage": {
        "background": 60,
        "foreground": 120,
        "rxBytes": 100000000,
        "txBytes": 30000000
      },
      "foregroundTime": 2500,
      "installTime": 1743726957061,
      "isSystemApp": False,
      "lastUsed": int(time.time()) - 400,
      "memoryUsage": -1,  # Invalid value to test handling
      "notifications": 30,
      "packageName": "com.google.android.gm",
      "processName": "com.google.android.gm",
      "targetSdkVersion": 33,
      "updatedTime": int(time.time()) - 900000,
      "versionCode": 20230528,
      "versionName": "2023.05.28"
    }
  ],
  "battery": {
    "capacity": 4410,
    "chargingType": "AC",
    "currentNow": 69,
    "health": 2,
    "isCharging": True,
    "level": 86,
    "temperature": 31.2,
    "voltage": 4344
  },
  "cpu": {
    "frequencies": [],
    "temperature": -1,  # Invalid value to test handling
    "usage": -1  # Invalid value to test handling
  },
  "deviceId": "c6aec2400e45a761",
  "deviceInfo": {
    "manufacturer": "Google",
    "model": "Pixel 6a",
    "osVersion": "15",
    "screenOnTime": 0,
    "sdkVersion": 35
  },
  "memory": {
    "availableRam": 1217622016,
    "lowMemory": False,
    "threshold": 226492416,
    "totalRam": 5849210880
  },
  "network": {
    "activeConnectionInfo": "SSID: <unknown ssid>",
    "cellularGeneration": "",
    "dataUsage": {
      "background": 13838855,
      "foreground": 41823050,
      "rxBytes": 49464078,
      "txBytes": 6197827
    },
    "isRoaming": False,
    "linkSpeed": 585,
    "strength": -57,
    "type": "WiFi"
  },
  "prompt": "Save my data",
  "settings": {
    "adaptiveBattery": False,
    "autoSync": True,
    "batteryOptimization": True,
    "dataSaver": False,
    "powerSaveMode": False
  },
  "timestamp": int(time.time() * 1000)
}

def test_android_request():
    print("Testing Android request format...")
    
    try:
        # Send the request to the localhost API
        response = requests.post(
            "http://localhost:8000/api/analyze",
            json=android_request
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            print(f"Success! Status code: {response.status_code}")
            
            # Parse and display the response
            try:
                result = response.json()
                print("\nResponse summary:")
                print(f"ID: {result.get('id', 'N/A')}")
                print(f"Success: {result.get('success', False)}")
                print(f"Message: {result.get('message', 'N/A')}")
                print(f"Battery Score: {result.get('batteryScore', 'N/A')}")
                print(f"Data Score: {result.get('dataScore', 'N/A')}")
                print(f"Performance Score: {result.get('performanceScore', 'N/A')}")
                
                # Show estimated savings
                savings = result.get('estimatedSavings', {})
                print(f"Estimated Battery Savings: {savings.get('batteryMinutes', 0)} minutes")
                print(f"Estimated Data Savings: {savings.get('dataMB', 0)} MB")
                
                # Show actionable items
                actionable_items = result.get('actionable', [])
                print(f"\nActionable Items ({len(actionable_items)}):")
                for i, item in enumerate(actionable_items, 1):
                    print(f"  {i}. {item.get('type')} - {item.get('description')}")
                
                # Show insights
                insights = result.get('insights', [])
                print(f"\nInsights ({len(insights)}):")
                for i, insight in enumerate(insights, 1):
                    print(f"  {i}. {insight.get('title')} - {insight.get('description')[:80]}...")
                
                return True
            
            except json.JSONDecodeError:
                print("Error: Failed to parse JSON response")
                print(f"Raw response: {response.text[:500]}")
                return False
            
        else:
            print(f"Error! Status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error during request: {str(e)}")
        return False

if __name__ == "__main__":
    test_android_request() 