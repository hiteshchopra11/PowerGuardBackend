import subprocess
import json
import os
import time
import random

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
        "total": 8000000000,
        "used": 4500000000,
        "free": 3500000000,
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
        "dataUsed": 1500,
        "wifiEnabled": True,
        "mobileDataEnabled": False,
        "type": "wifi",
        "strength": 85,
        "isRoaming": False,
        "dataUsage": {
            "daily": 150,
            "weekly": 750,
            "monthly": 3000,
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
    ]
}

# List of test prompts covering different scenarios
TEST_PROMPTS = [
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

# Create variations of device data for different test scenarios
def create_device_data(prompt):
    device_data = json.loads(json.dumps(BASE_DEVICE_DATA))  # Deep copy
    
    # Modify device data based on prompt content
    if "5%" in prompt or "critically low" in prompt or "10%" in prompt:
        device_data["battery"]["level"] = random.randint(5, 10)
    elif "15%" in prompt:
        device_data["battery"]["level"] = 15
    elif "20%" in prompt:
        device_data["battery"]["level"] = 20
    elif "30%" in prompt:
        device_data["battery"]["level"] = 30
    
    # Set high data usage for data-related prompts
    if "data" in prompt.lower() or "MB" in prompt:
        device_data["network"]["dataUsed"] = random.randint(1800, 2000)
        device_data["network"]["dataUsage"]["daily"] = random.randint(400, 500)
        device_data["network"]["dataUsage"]["monthly"] = random.randint(4500, 5000)
        device_data["network"]["dataUsage"]["foreground"] = random.randint(1500, 1800)
        device_data["network"]["dataUsage"]["background"] = random.randint(500, 700)
        
        # Set specific values for quantified data prompts
        if "50MB" in prompt:
            device_data["network"]["dataUsed"] = 1950
        elif "10MB" in prompt:
            device_data["network"]["dataUsed"] = 1990
        elif "100MB" in prompt:
            device_data["network"]["dataUsed"] = 1900
    
    # Update app data usage for data prompts
    if "data" in prompt.lower():
        for app in device_data["apps"]:
            if isinstance(app["dataUsage"], dict):
                app["dataUsage"]["foreground"] = random.randint(50, 200)
                app["dataUsage"]["background"] = random.randint(20, 100)
                app["dataUsage"]["rxBytes"] = app["dataUsage"]["foreground"] * 1000000
                app["dataUsage"]["txBytes"] = app["dataUsage"]["background"] * 500000
    
    # Add the prompt to the device data
    device_data["prompt"] = prompt
    
    return device_data

# Function to run a test and return the results
def run_test(prompt):
    device_data = create_device_data(prompt)
    
    # Save the device data to a temporary file
    with open("temp_device_data.json", "w") as f:
        json.dump(device_data, f)
    
    # Create curl command for the real API
    curl_command = 'curl -X POST "http://localhost:8000/api/analyze" -H "Content-Type: application/json" -d @temp_device_data.json'
    
    # Execute the curl command and capture output
    result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
    
    # Remove the temporary file
    if os.path.exists("temp_device_data.json"):
        os.remove("temp_device_data.json")
    
    try:
        # Parse the JSON response
        response_data = json.loads(result.stdout)
        return {
            "prompt": prompt,
            "device_data": device_data,
            "curl_command": curl_command,
            "response": response_data,
            "actionables": response_data.get("actionable", []),
            "insights": response_data.get("insights", []),
            "estimated_savings": response_data.get("estimatedSavings", {})
        }
    except json.JSONDecodeError:
        return {
            "prompt": prompt,
            "device_data": device_data,
            "curl_command": curl_command,
            "error": "Failed to parse JSON response",
            "raw_response": result.stdout
        }

# Function to format results for output
def format_result(result):
    output = []
    output.append("=" * 80)
    output.append(f"PROMPT: \"{result['prompt']}\"")
    output.append("-" * 80)
    output.append(f"DEVICE DATA:")
    output.append(f"  Battery Level: {result['device_data']['battery']['level']}%")
    output.append(f"  Data Used: {result['device_data']['network']['dataUsed']} MB")
    output.append(f"  Number of Apps: {len(result['device_data']['apps'])}")
    output.append("-" * 80)
    output.append(f"CURL COMMAND: {result['curl_command']}")
    output.append("-" * 80)
    
    if "error" in result:
        output.append(f"ERROR: {result['error']}")
        output.append(f"RAW RESPONSE: {result['raw_response']}")
        return "\n".join(output)
    
    # Format actionables
    output.append("ACTIONABLES:")
    if result["actionables"]:
        for a in result["actionables"]:
            output.append(f"  - Type: {a.get('type')}")
            output.append(f"    Package: {a.get('packageName')}")
            output.append(f"    Description: {a.get('description')}")
            output.append(f"    Mode: {a.get('newMode')}")
            output.append("")
    else:
        output.append("  No actionables generated")
    
    # Format insights
    output.append("INSIGHTS:")
    if result["insights"]:
        for i in result["insights"]:
            output.append(f"  - Title: {i.get('title')}")
            output.append(f"    Description: {i.get('description')}")
            output.append(f"    Severity: {i.get('severity', 'N/A')}")
            output.append("")
    else:
        output.append("  No insights generated")
    
    # Format savings
    savings = result["estimated_savings"]
    output.append("ESTIMATED SAVINGS:")
    output.append(f"  Battery: {savings.get('batteryMinutes', 0)} minutes")
    output.append(f"  Data: {savings.get('dataMB', 0)} MB")
    
    # Include the raw JSON for reference
    output.append("-" * 80)
    output.append("RAW JSON RESPONSE:")
    output.append(json.dumps(result["response"], indent=2))
    
    return "\n".join(output)

# Main function to run all tests and save results
def run_all_tests():
    print(f"Running REAL API tests for {len(TEST_PROMPTS)} prompts...")
    results = []
    
    # Run each test
    for prompt in TEST_PROMPTS:
        print(f"Testing prompt: \"{prompt}\"")
        result = run_test(prompt)
        results.append(result)
        time.sleep(1)  # Small delay to prevent overwhelming the server
    
    # Format and save all results
    output = []
    output.append("POWERGUARD AI BACKEND - REAL API TEST RESULTS")
    output.append("=" * 80)
    output.append(f"Total prompts tested: {len(results)}")
    output.append("")
    
    # Add a summary table
    output.append("SUMMARY TABLE:")
    output.append("-" * 80)
    output.append(f"{'PROMPT':<45} | {'BATTERY':<8} | {'ACTIONABLES':<12} | {'INSIGHTS':<10} | {'BATTERY SAVED':<15} | {'DATA SAVED':<10}")
    output.append("-" * 80)
    
    for r in results:
        if "error" in r:
            continue
        
        battery_level = r["device_data"]["battery"]["level"]
        num_actionables = len(r["actionables"])
        num_insights = len(r["insights"])
        battery_saved = r["estimated_savings"].get("batteryMinutes", 0)
        data_saved = r["estimated_savings"].get("dataMB", 0)
        
        truncated_prompt = r["prompt"][:42] + "..." if len(r["prompt"]) > 45 else r["prompt"].ljust(45)
        output.append(f"{truncated_prompt} | {battery_level:<8} | {num_actionables:<12} | {num_insights:<10} | {battery_saved:<15} | {data_saved:<10}")
    
    output.append("")
    
    # Add detailed results for each prompt
    for r in results:
        output.append(format_result(r))
        output.append("")
    
    # Save to file
    with open("real_api_test_results.txt", "w") as f:
        f.write("\n".join(output))
    
    print(f"All test results saved to real_api_test_results.txt")

if __name__ == "__main__":
    run_all_tests() 