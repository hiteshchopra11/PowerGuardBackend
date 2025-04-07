import subprocess
import json
import os
import time
import random
import requests

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

# List of test prompts covering all cases
TEST_PROMPTS = [
    # Default prompts (always sent from Android)
    "Choose the best battery saving strategy",
    "Choose the best data saving strategy",
    
    # Custom user prompts
    "Save my data",
    
    # Battery optimization prompts
    "My battery is at 5% and I need it to last for 2 more hours",
    "Save my battery, it's critically low",
    "I'm traveling for 3 hours with 15% battery left",
    "Optimize battery but keep WhatsApp working",
    
    # Data optimization prompts
    "I only have 50MB data left until tomorrow",
    "Save data but ensure my email still works",
    "Traveling abroad with limited data plan",
    
    # Information requests
    "Which apps are draining my battery?",
    "What's using all my data?",
    "Show me my battery usage for the past day",
    
    # Complex/combined prompts
    "Need Maps and WhatsApp for 4 hours but battery at 20%",
    "Can I stream Netflix for 2 hours with 30% battery?",
    "I need to make an important call in 1 hour but battery is at 10%",
    "Optimize battery and data but keep messaging apps working",
    "I have 15% battery and 100MB data left for a 2 hour trip",
    
    # Additional email test
    "Save battery but make sure I can still use Gmail"
]

def reset_database():
    """Reset the database before running tests"""
    print("Resetting database...")
    try:
        response = requests.post("http://localhost:8000/api/reset-db")
        if response.status_code == 200:
            print("Database reset successfully")
        else:
            print(f"Failed to reset database: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error resetting database: {e}")

# Create variations of device data for different test scenarios
def create_device_data(prompt):
    device_data = json.loads(json.dumps(BASE_DEVICE_DATA))  # Deep copy
    
    # Set prompt
    device_data["prompt"] = prompt
    
    # Modify device data based on prompt content
    if "battery" in prompt.lower() or "power" in prompt.lower():
        # For battery optimization prompt, set lower battery level
        device_data["battery"]["level"] = random.randint(30, 40)
        
        # Set specific values for quantified battery prompts
        if "5%" in prompt or "critically low" in prompt or "10%" in prompt:
            device_data["battery"]["level"] = random.randint(5, 10)
        elif "15%" in prompt:
            device_data["battery"]["level"] = 15
        elif "20%" in prompt:
            device_data["battery"]["level"] = 20
        elif "30%" in prompt:
            device_data["battery"]["level"] = 30
        
        # Set more battery-hungry apps
        for app in device_data["apps"]:
            app["batteryUsage"] = random.randint(15, 35)
            
    elif "data" in prompt.lower() or "network" in prompt.lower():
        # For data optimization prompt, set higher data usage
        device_data["network"]["dataUsage"]["foreground"] = random.randint(1500, 1800)
        device_data["network"]["dataUsage"]["background"] = random.randint(500, 700)
        device_data["network"]["dataUsage"]["rxBytes"] = device_data["network"]["dataUsage"]["foreground"] * 1000000
        device_data["network"]["dataUsage"]["txBytes"] = device_data["network"]["dataUsage"]["background"] * 500000
        
        # Set specific values for quantified data prompts
        if "50MB" in prompt:
            device_data["network"]["dataUsage"]["rxBytes"] = device_data["network"]["dataUsage"]["foreground"] * 1000000
            device_data["network"]["dataUsage"]["txBytes"] = device_data["network"]["dataUsage"]["background"] * 500000
        elif "100MB" in prompt:
            device_data["network"]["dataUsage"]["rxBytes"] = device_data["network"]["dataUsage"]["foreground"] * 1000000
            device_data["network"]["dataUsage"]["txBytes"] = device_data["network"]["dataUsage"]["background"] * 500000
        
        # Set more data-hungry apps
        for app in device_data["apps"]:
            app["dataUsage"]["foreground"] = random.randint(200, 400)
            app["dataUsage"]["background"] = random.randint(50, 150)
            app["dataUsage"]["rxBytes"] = app["dataUsage"]["foreground"] * 1000000
            app["dataUsage"]["txBytes"] = app["dataUsage"]["background"] * 500000
    
    return device_data

def run_api_test(prompt):
    """Run API test with the given prompt"""
    print(f'Testing prompt: "{prompt}"')
    
    # Create device data specific to this prompt
    device_data = create_device_data(prompt)
    
    # Write temporary device data to file
    with open("temp_device_data.json", "w") as f:
        json.dump(device_data, f)
    
    # Run curl command to send the request
    curl_command = f'curl -X POST "http://localhost:8000/api/analyze" -H "Content-Type: application/json" -d @temp_device_data.json'
    
    result = {
        "prompt": prompt,
        "device_data": device_data,
        "curl_command": curl_command
    }
    
    try:
        output = subprocess.check_output(curl_command, shell=True)
        response = json.loads(output)
        result["success"] = True
        result["response"] = response
    except subprocess.CalledProcessError as e:
        result["success"] = False
        result["error"] = str(e)
        result["output"] = e.output.decode() if hasattr(e, "output") else ""
    except json.JSONDecodeError as e:
        result["success"] = False
        result["error"] = f"Failed to parse JSON response: {str(e)}"
        result["output"] = output.decode() if isinstance(output, bytes) else str(output)
    
    return result

def format_results(results):
    """Format test results as text"""
    output = []
    output.append("POWERGUARD AI BACKEND - REAL API TEST RESULTS")
    output.append("=" * 80)
    output.append(f"Total prompts tested: {len(results)}")
    output.append("")
    
    # Generate summary table
    output.append("SUMMARY TABLE:")
    output.append("-" * 80)
    output.append(f"{'PROMPT':<40} | {'BATTERY':<8} | {'ACTIONABLES':<12} | {'INSIGHTS':<10} | {'BATTERY SAVED':<15} | {'DATA SAVED':10}")
    output.append("-" * 80)
    
    for result in results:
        prompt = result["prompt"]
        if len(prompt) > 35:
            prompt = prompt[:35] + "..."
            
        if result.get("success", False) and "response" in result:
            resp = result["response"]
            battery_score = resp.get("batteryScore", "N/A")
            actionables = len(resp.get("actionable", []))
            insights = len(resp.get("insights", []))
            battery_saved = resp.get("estimatedSavings", {}).get("batteryMinutes", 0)
            data_saved = resp.get("estimatedSavings", {}).get("dataMB", 0)
            
            output.append(f"{prompt:<40} | {battery_score:<8} | {actionables:<12} | {insights:<10} | {battery_saved:<15} | {data_saved:<10}")
        else:
            output.append(f"{prompt:<40} | {'ERROR':<8} | {'N/A':<12} | {'N/A':<10} | {'N/A':<15} | {'N/A':<10}")
            
        output.append("")
    
    # Add detailed results for each prompt
    for result in results:
        output.append("=" * 80)
        output.append(f"PROMPT: \"{result['prompt']}\"")
        output.append("-" * 80)
        
        output.append(f"DEVICE DATA:")
        output.append(f"  Battery Level: {result['device_data']['battery']['level']}%")
        output.append(f"  Data Used: {result['device_data']['network']['dataUsage']['rxBytes'] // 1000000} MB")
        output.append(f"  Number of Apps: {len(result['device_data']['apps'])}")
        output.append("-" * 80)
        
        output.append(f"CURL COMMAND: {result['curl_command']}")
        output.append("-" * 80)
        
        if result.get("success", False) and "response" in result:
            resp = result["response"]
            
            # Display actionables
            actionables = resp.get("actionable", [])
            output.append(f"ACTIONABLES:")
            if actionables:
                for a in actionables:
                    output.append(f"  - Type: {a.get('type')}")
                    output.append(f"    Package: {a.get('packageName', 'system')}")
                    output.append(f"    Description: {a.get('description')}")
                    output.append(f"    Mode: {a.get('newMode')}")
                    output.append(f"")
            else:
                output.append("  None")
                output.append("")
                
            # Display insights
            insights = resp.get("insights", [])
            output.append(f"INSIGHTS:")
            if insights:
                for i in insights:
                    output.append(f"  - Type: {i.get('type')}")
                    output.append(f"    Title: {i.get('title')}")
                    output.append(f"    Description: {i.get('description')[:100]}..." if len(i.get('description', '')) > 100 else i.get('description', ''))
                    output.append(f"    Severity: {i.get('severity')}")
                    output.append(f"")
            else:
                output.append("  None")
                output.append("")
                
            # Display scores
            output.append(f"SCORES:")
            output.append(f"  Battery Score: {resp.get('batteryScore')}")
            output.append(f"  Data Score: {resp.get('dataScore')}")
            output.append(f"  Performance Score: {resp.get('performanceScore')}")
            output.append(f"")
            
            # Display estimated savings
            savings = resp.get("estimatedSavings", {})
            output.append(f"ESTIMATED SAVINGS:")
            output.append(f"  Battery: {savings.get('batteryMinutes', 0)} minutes")
            output.append(f"  Data: {savings.get('dataMB', 0)} MB")
            output.append(f"")
        else:
            output.append(f"ERROR: {result.get('error', 'Unknown error')}")
            output.append(f"RAW RESPONSE: {result.get('output', '')}")
            output.append(f"")
    
    return "\n".join(output)

def main():
    # First, reset the database
    reset_database()
    
    print(f"Running REAL API tests for {len(TEST_PROMPTS)} prompts...")
    
    results = []
    for prompt in TEST_PROMPTS:
        result = run_api_test(prompt)
        results.append(result)
    
    # Format and save results
    formatted_results = format_results(results)
    with open("real_api_test_results.txt", "w") as f:
        f.write(formatted_results)
    
    print("All test results saved to real_api_test_results.txt")

if __name__ == "__main__":
    main() 