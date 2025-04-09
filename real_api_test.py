import subprocess
import json
import os
import time
import random
import requests
import datetime

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

# List of test prompts specified by the user
TEST_PROMPTS = [
    "What are the top 3 apps draining my battery?",
    "What are the top 3 apps draining my data?",
    "Show me the top data-consuming app",
    "Save my battery",
    "I urgently need my battery to last for the next 2 hours while I keep using WhatsApp.",
    "Reduce data usage",
    "Save data but keep messages running",
    "I'm on a trip with 10% battery and need Maps",
    "Going on a 2-hour drive — save battery and data"
]

def reset_database():
    """Reset the database before running tests"""
    print("\n🔄 Resetting database...")
    try:
        response = requests.post("http://localhost:8000/api/reset-db")
        if response.status_code == 200:
            print("✅ Database reset successfully")
        else:
            print(f"❌ Failed to reset database: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

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
        if "5%" in prompt or "critically low" in prompt:
            device_data["battery"]["level"] = random.randint(5, 10)
        elif "10%" in prompt:
            device_data["battery"]["level"] = 10
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

def print_colored(text, color):
    """Print colored text in terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "reset": "\033[0m"
    }
    
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print_colored(f" {text} ", "bold")
    print("=" * 80)

def print_section(text):
    """Print a formatted section header."""
    print("\n" + "-" * 80)
    print_colored(f" {text} ", "cyan")
    print("-" * 80)

def run_api_test(prompt, log_file):
    """Run API test with the given prompt and display results in real-time"""
    print_header(f"TESTING PROMPT: '{prompt}'")
    
    # Create device data specific to this prompt
    device_data = create_device_data(prompt)
    
    # Display key device data in real-time
    print_section("DEVICE DATA USED")
    print(f"🔋 Battery Level: {device_data['battery']['level']}%")
    print(f"📊 Data Downloaded: {device_data['network']['dataUsage']['rxBytes'] // 1000000} MB")
    print(f"📤 Data Uploaded: {device_data['network']['dataUsage']['txBytes'] // 1000000} MB")
    print(f"📱 Number of Apps: {len(device_data['apps'])}")
    
    # Top battery-consuming apps
    apps_by_battery = sorted(device_data['apps'], key=lambda x: float(x.get('batteryUsage', 0) or 0), reverse=True)[:3]
    print("\nTop 3 Battery-Consuming Apps:")
    for idx, app in enumerate(apps_by_battery, 1):
        print(f"  {idx}. {app['appName']}: {app['batteryUsage']}%")
    
    # Top data-consuming apps
    apps_by_data = sorted(device_data['apps'], 
                         key=lambda x: float(x.get('dataUsage', {}).get('foreground', 0) or 0) + 
                                      float(x.get('dataUsage', {}).get('background', 0) or 0), 
                         reverse=True)[:3]
    print("\nTop 3 Data-Consuming Apps:")
    for idx, app in enumerate(apps_by_data, 1):
        total_data = float(app.get('dataUsage', {}).get('foreground', 0) or 0) + float(app.get('dataUsage', {}).get('background', 0) or 0)
        print(f"  {idx}. {app['appName']}: {total_data} MB")
    
    # Log to file
    log_file.write(f"\n{'=' * 80}\n")
    log_file.write(f"PROMPT: '{prompt}'\n")
    log_file.write(f"{'=' * 80}\n\n")
    log_file.write(f"DEVICE DATA:\n")
    log_file.write(f"  Battery Level: {device_data['battery']['level']}%\n")
    log_file.write(f"  Data Downloaded: {device_data['network']['dataUsage']['rxBytes'] // 1000000} MB\n")
    log_file.write(f"  Data Uploaded: {device_data['network']['dataUsage']['txBytes'] // 1000000} MB\n")
    log_file.write(f"  Number of Apps: {len(device_data['apps'])}\n\n")
    
    # Write temporary device data to file
    with open("temp_device_data.json", "w") as f:
        json.dump(device_data, f)
    
    # Run curl command to send the request
    curl_command = f'curl -X POST "http://localhost:8000/api/analyze" -H "Content-Type: application/json" -d @temp_device_data.json'
    
    print_section("SENDING API REQUEST")
    print(f"⏳ Sending request to PowerGuard API...\n")
    
    log_file.write(f"CURL COMMAND: {curl_command}\n\n")
    
    result = {
        "prompt": prompt,
        "device_data": device_data,
        "curl_command": curl_command,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    start_time = time.time()
    
    try:
        output = subprocess.check_output(curl_command, shell=True)
        response = json.loads(output)
        result["success"] = True
        result["response"] = response
        
        # Display API response in real-time
        print_section("API RESPONSE")
        
        # Display actionables
        actionables = response.get("actionable", [])
        print_colored("ACTIONABLES:", "green")
        if actionables:
            for idx, a in enumerate(actionables, 1):
                print(f"  {idx}. Type: {a.get('type')}")
                print(f"     Package: {a.get('packageName', 'system')}")
                print(f"     Description: {a.get('description')}")
                print(f"     Mode: {a.get('newMode')}")
                print()
                
                # Log to file
                log_file.write(f"ACTIONABLE {idx}:\n")
                log_file.write(f"  Type: {a.get('type')}\n")
                log_file.write(f"  Package: {a.get('packageName', 'system')}\n")
                log_file.write(f"  Description: {a.get('description')}\n")
                log_file.write(f"  Mode: {a.get('newMode')}\n\n")
        else:
            print("  None\n")
            log_file.write("ACTIONABLES: None\n\n")
            
        # Display insights
        insights = response.get("insights", [])
        print_colored("INSIGHTS:", "blue")
        if insights:
            for idx, i in enumerate(insights, 1):
                print(f"  {idx}. Type: {i.get('type')}")
                print(f"     Title: {i.get('title')}")
                desc = i.get('description', '')
                print(f"     Description: {desc[:100]}..." if len(desc) > 100 else f"     Description: {desc}")
                print(f"     Severity: {i.get('severity')}")
                print()
                
                # Log to file
                log_file.write(f"INSIGHT {idx}:\n")
                log_file.write(f"  Type: {i.get('type')}\n")
                log_file.write(f"  Title: {i.get('title')}\n")
                log_file.write(f"  Description: {desc}\n")
                log_file.write(f"  Severity: {i.get('severity')}\n\n")
        else:
            print("  None\n")
            log_file.write("INSIGHTS: None\n\n")
            
        # Display scores
        print_colored("SCORES:", "yellow")
        print(f"  Battery Score: {response.get('batteryScore')}")
        print(f"  Data Score: {response.get('dataScore')}")
        print(f"  Performance Score: {response.get('performanceScore')}")
        print()
        
        # Log to file
        log_file.write(f"SCORES:\n")
        log_file.write(f"  Battery Score: {response.get('batteryScore')}\n")
        log_file.write(f"  Data Score: {response.get('dataScore')}\n")
        log_file.write(f"  Performance Score: {response.get('performanceScore')}\n\n")
        
        # Display estimated savings
        savings = response.get("estimatedSavings", {})
        print_colored("ESTIMATED SAVINGS:", "purple")
        print(f"  Battery: {savings.get('batteryMinutes', 0)} minutes")
        print(f"  Data: {savings.get('dataMB', 0)} MB")
        
        # Log to file
        log_file.write(f"ESTIMATED SAVINGS:\n")
        log_file.write(f"  Battery: {savings.get('batteryMinutes', 0)} minutes\n")
        log_file.write(f"  Data: {savings.get('dataMB', 0)} MB\n\n")
        
        # NEW: Add a human-readable summary of the response
        print_section("SUMMARY OF RECOMMENDATIONS")
        
        # Collect system-level actions
        system_actions = [a for a in actionables if a.get('packageName') == 'system']
        app_actions = [a for a in actionables if a.get('packageName') != 'system']
        
        # Determine focus based on actionables
        battery_actions = [a for a in actionables if "BATTERY" in a.get("type", "") or a.get("type") == "OPTIMIZE_BATTERY"]
        data_actions = [a for a in actionables if "DATA" in a.get("type", "") or a.get("type") == "ENABLE_DATA_SAVER"]
        
        # Find critical apps (apps set to normal priority)
        critical_apps = []
        for a in actionables:
            if a.get("newMode") == "normal" and a.get("packageName") != "system":
                app_name = next((app["appName"] for app in device_data["apps"] if app["packageName"] == a.get("packageName")), a.get("packageName"))
                critical_apps.append(app_name)
        
        # Determine focus from insights
        strategy_focus = "balanced"
        critical_categories = []
        for i in insights:
            if i.get("type") == "Strategy" and "battery" in i.get("description", "").lower() and "data" not in i.get("description", "").lower():
                strategy_focus = "battery"
            elif i.get("type") == "Strategy" and "data" in i.get("description", "").lower() and "battery" not in i.get("description", "").lower():
                strategy_focus = "data"
            elif i.get("type") == "Strategy" and "both" in i.get("description", "").lower():
                strategy_focus = "both"
            
            if i.get("type") == "CriticalApps":
                critical_text = i.get("description", "")
                if ":" in critical_text:
                    critical_categories = critical_text.split(":", 1)[1].strip().split(", ")
        
        # Human-readable summary
        print_colored("WHAT POWERGUARD IS SUGGESTING:", "bold")
        
        # Print overall focus
        if strategy_focus == "battery":
            print(f"💡 PowerGuard is focusing on optimizing BATTERY usage")
        elif strategy_focus == "data":
            print(f"💡 PowerGuard is focusing on optimizing DATA usage")
        elif strategy_focus == "both":
            print(f"💡 PowerGuard is optimizing BOTH battery and data usage")
        else:
            print(f"💡 PowerGuard is providing general optimization suggestions")
        
        # Print system-level recommendations
        if system_actions:
            print("\n📱 System-wide changes recommended:")
            for action in system_actions:
                print(f"  • {action.get('description')}")
        
        # Print critical apps
        if critical_apps:
            print(f"\n⭐ Preserving functionality for critical apps:")
            for app in critical_apps:
                print(f"  • {app}")
        
        # Print app-specific recommendations
        if app_actions and len(app_actions) > len(critical_apps):
            print(f"\n📊 Optimizing {len(app_actions) - len(critical_apps)} apps:")
            # Group by app name
            app_dict = {}
            for action in app_actions:
                if action.get("newMode") == "normal":
                    continue  # Skip critical apps already covered
                
                pkg_name = action.get("packageName")
                app_name = next((app["appName"] for app in device_data["apps"] if app["packageName"] == pkg_name), pkg_name)
                
                if app_name not in app_dict:
                    app_dict[app_name] = []
                
                app_dict[app_name].append(action.get("type"))
            
            # Print grouped actions
            for app_name, action_types in app_dict.items():
                actions_str = ""
                if any("BATTERY" in t for t in action_types):
                    actions_str += "battery "
                if any("DATA" in t for t in action_types):
                    actions_str += "data "
                
                print(f"  • {app_name}: Optimizing {actions_str.strip()}")
        
        # Print estimated savings with more context
        if savings.get('batteryMinutes', 0) > 0 or savings.get('dataMB', 0) > 0:
            print("\n🔋 Estimated impact of these changes:")
            if savings.get('batteryMinutes', 0) > 0:
                print(f"  • Battery life extended by ~{savings.get('batteryMinutes', 0)} minutes")
            if savings.get('dataMB', 0) > 0:
                print(f"  • Data usage reduced by ~{savings.get('dataMB', 0)} MB")
        
        # Log human-readable summary to file
        log_file.write("HUMAN-READABLE SUMMARY:\n")
        
        if strategy_focus == "battery":
            log_file.write("PowerGuard is focusing on optimizing BATTERY usage\n")
        elif strategy_focus == "data":
            log_file.write("PowerGuard is focusing on optimizing DATA usage\n")
        elif strategy_focus == "both":
            log_file.write("PowerGuard is optimizing BOTH battery and data usage\n")
        else:
            log_file.write("PowerGuard is providing general optimization suggestions\n")
        
        # Log system-level recommendations
        if system_actions:
            log_file.write("\nSystem-wide changes recommended:\n")
            for action in system_actions:
                log_file.write(f"- {action.get('description')}\n")
        
        # Log critical apps
        if critical_apps:
            log_file.write(f"\nPreserving functionality for critical apps:\n")
            for app in critical_apps:
                log_file.write(f"- {app}\n")
        
        # Log app-specific recommendations
        if app_actions and len(app_actions) > len(critical_apps):
            log_file.write(f"\nOptimizing {len(app_actions) - len(critical_apps)} apps:\n")
            for app_name, action_types in app_dict.items():
                actions_str = ""
                if any("BATTERY" in t for t in action_types):
                    actions_str += "battery "
                if any("DATA" in t for t in action_types):
                    actions_str += "data "
                
                log_file.write(f"- {app_name}: Optimizing {actions_str.strip()}\n")
        
        # Log estimated savings with more context
        if savings.get('batteryMinutes', 0) > 0 or savings.get('dataMB', 0) > 0:
            log_file.write("\nEstimated impact of these changes:\n")
            if savings.get('batteryMinutes', 0) > 0:
                log_file.write(f"- Battery life extended by ~{savings.get('batteryMinutes', 0)} minutes\n")
            if savings.get('dataMB', 0) > 0:
                log_file.write(f"- Data usage reduced by ~{savings.get('dataMB', 0)} MB\n")
        
        log_file.write("\n")
        
    except subprocess.CalledProcessError as e:
        result["success"] = False
        result["error"] = str(e)
        result["output"] = e.output.decode() if hasattr(e, "output") else ""
        
        print_colored("ERROR OCCURRED:", "red")
        print(f"  {result['error']}")
        print(f"  Output: {result['output']}")
        
        # Log to file
        log_file.write(f"ERROR OCCURRED:\n")
        log_file.write(f"  {result['error']}\n")
        log_file.write(f"  Output: {result['output']}\n\n")
        
    except json.JSONDecodeError as e:
        result["success"] = False
        result["error"] = f"Failed to parse JSON response: {str(e)}"
        result["output"] = output.decode() if isinstance(output, bytes) else str(output)
        
        print_colored("JSON PARSING ERROR:", "red")
        print(f"  {result['error']}")
        print(f"  Output: {result['output']}")
        
        # Log to file
        log_file.write(f"JSON PARSING ERROR:\n")
        log_file.write(f"  {result['error']}\n")
        log_file.write(f"  Output: {result['output']}\n\n")
    
    # Display request time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\n⏱️ Request completed in {execution_time:.2f} seconds\n")
    log_file.write(f"Request completed in {execution_time:.2f} seconds\n\n")
    
    return result

def test_battery_data_combinations(log_file):
    """Test combinations of battery and data conditions with specific prompts."""
    print_header("TESTING BATTERY AND DATA COMBINATIONS")
    log_file.write("\n\nTESTING BATTERY AND DATA COMBINATIONS\n")
    log_file.write("=" * 80 + "\n\n")
    
    # Using the same prompts as main tests
    test_prompts = TEST_PROMPTS
    
    # Combinations of battery and data states with 5GB total data
    scenarios = [
        {"name": "Low Battery, Low Data", "battery_level": 15, "data_remaining": 500},
        {"name": "Low Battery, High Data", "battery_level": 15, "data_remaining": 4000},
        {"name": "High Battery, Low Data", "battery_level": 85, "data_remaining": 500},
        {"name": "High Battery, High Data", "battery_level": 85, "data_remaining": 4000}
    ]
    
    all_results = []
    
    for prompt in test_prompts:
        prompt_results = []
        
        for scenario in scenarios:
            print_section(f"TESTING '{prompt}' with {scenario['name']}")
            log_file.write(f"TESTING '{prompt}' with {scenario['name']}\n")
            log_file.write("-" * 80 + "\n\n")
            
            # Create device data with specific battery and data values
            device_data = json.loads(json.dumps(BASE_DEVICE_DATA))  # Deep copy
            device_data["prompt"] = prompt
            device_data["battery"]["level"] = scenario["battery_level"]
            
            # Set data usage to simulate remaining data (using 5GB total)
            total_data = 5000  # 5GB total monthly data
            used_data = total_data - scenario["data_remaining"]
            device_data["network"]["dataUsage"]["foreground"] = used_data * 0.7  # 70% used in foreground
            device_data["network"]["dataUsage"]["background"] = used_data * 0.3  # 30% used in background
            device_data["network"]["dataUsage"]["rxBytes"] = int(device_data["network"]["dataUsage"]["foreground"] * 1000000)
            device_data["network"]["dataUsage"]["txBytes"] = int(device_data["network"]["dataUsage"]["background"] * 500000)
            
            # Display key device data in real-time
            print(f"🔋 Battery Level: {device_data['battery']['level']}%")
            print(f"📊 Data Remaining: {scenario['data_remaining']} MB")
            
            log_file.write(f"Battery Level: {device_data['battery']['level']}%\n")
            log_file.write(f"Data Remaining: {scenario['data_remaining']} MB\n\n")
            
            test_result = {
                "prompt": prompt,
                "scenario": scenario["name"],
                "device_data": device_data,
                "success": False
            }
            
            try:
                # Call the API
                start_time = time.time()
                print(f"⏳ Sending request to PowerGuard API...")
                
                response = requests.post(
                    "http://localhost:8000/api/analyze",
                    json=device_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
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
                    if scenario["battery_level"] <= 20 and scenario["data_remaining"] <= 1000:
                        # Both low - should have both types of actions
                        test_result["expected_focus"] = "both"
                        
                        # For information queries with no actions, check the scores instead
                        if len(battery_actionables) == 0 and len(data_actionables) == 0:
                            # It's likely an informational query, so check scores 
                            battery_score = data.get("scores", {}).get("batteryScore", 100)
                            data_score = data.get("scores", {}).get("dataScore", 100)
                            
                            # Consider it correct if both scores are below 90 (indicates both resources are constrained)
                            test_result["correct_focus"] = battery_score < 90 and data_score < 100
                        else:
                            test_result["correct_focus"] = len(battery_actionables) > 0 and len(data_actionables) > 0
                    elif scenario["battery_level"] <= 20:
                        # Low battery, high data - should focus on battery
                        test_result["expected_focus"] = "battery"
                        
                        # For information queries with no actions, check the scores
                        if len(battery_actionables) == 0 and len(data_actionables) == 0:
                            battery_score = data.get("scores", {}).get("batteryScore", 100)
                            test_result["correct_focus"] = battery_score < 90
                        else:
                            test_result["correct_focus"] = len(battery_actionables) >= len(data_actionables)
                    elif scenario["data_remaining"] <= 1000:
                        # High battery, low data - should focus on data
                        test_result["expected_focus"] = "data"
                        
                        # For information queries with no actions, check the scores
                        if len(battery_actionables) == 0 and len(data_actionables) == 0:
                            data_score = data.get("scores", {}).get("dataScore", 100)
                            test_result["correct_focus"] = data_score < 100
                        else: 
                            test_result["correct_focus"] = len(data_actionables) >= len(battery_actionables)
                    else:
                        # Both high - general optimization
                        test_result["expected_focus"] = "balanced"
                        test_result["correct_focus"] = True
                    
                    # Display result in real-time
                    focus_status = "✅ Correct" if test_result["correct_focus"] else "❌ Incorrect"
                    print(f"\n🎯 Expected Focus: {test_result['expected_focus']}")
                    print(f"🔍 Focus Result: {focus_status}")
                    print(f"🔋 Battery Actions: {len(battery_actionables)}")
                    print(f"📊 Data Actions: {len(data_actionables)}")
                    print(f"⏱️ Request completed in {execution_time:.2f} seconds\n")
                    
                    log_file.write(f"Expected Focus: {test_result['expected_focus']}\n")
                    log_file.write(f"Focus Result: {'Correct' if test_result['correct_focus'] else 'Incorrect'}\n")
                    log_file.write(f"Battery Actions: {len(battery_actionables)}\n")
                    log_file.write(f"Data Actions: {len(data_actionables)}\n")
                    log_file.write(f"Request completed in {execution_time:.2f} seconds\n\n")
                    
                    # NEW: Add a simplified human-readable summary
                    if actionables:
                        # Determine system and app-specific actions
                        system_actions = [a for a in actionables if a.get('packageName') == 'system']
                        app_actions = [a for a in actionables if a.get('packageName') != 'system']
                        
                        # Find critical apps (apps set to normal priority)
                        critical_apps = []
                        for a in actionables:
                            if a.get("newMode") == "normal" and a.get("packageName") != "system":
                                app_name = next((app["appName"] for app in device_data["apps"] if app["packageName"] == a.get("packageName")), a.get("packageName"))
                                critical_apps.append(app_name)
                        
                        # Determine primary focus from insights
                        strategy_focus = "balanced"
                        for i in insights:
                            if i.get("type") == "Strategy" and "battery" in i.get("description", "").lower() and "data" not in i.get("description", "").lower():
                                strategy_focus = "battery"
                            elif i.get("type") == "Strategy" and "data" in i.get("description", "").lower() and "battery" not in i.get("description", "").lower():
                                strategy_focus = "data"
                            elif i.get("type") == "Strategy" and "both" in i.get("description", "").lower():
                                strategy_focus = "both"
                        
                        # Print a summary of what PowerGuard is recommending
                        print_colored("RECOMMENDATION SUMMARY:", "bold")
                        
                        # Show what PowerGuard is focusing on
                        if strategy_focus == "battery":
                            print(f"💡 Focus: Battery optimization ({len(battery_actionables)} actions)")
                        elif strategy_focus == "data":
                            print(f"💡 Focus: Data optimization ({len(data_actionables)} actions)")
                        elif strategy_focus == "both":
                            print(f"💡 Focus: Both battery and data ({len(battery_actionables)} battery actions, {len(data_actionables)} data actions)")
                        else:
                            print(f"💡 Focus: General optimization")
                        
                        # Show system-level recommendations
                        if system_actions:
                            system_types = [a.get("type") for a in system_actions]
                            print(f"📱 System changes: {', '.join(system_types)}")
                        
                        # Show critical apps
                        if critical_apps:
                            print(f"⭐ Protected apps: {', '.join(critical_apps)}")
                        
                        # Show savings
                        savings = data.get("estimatedSavings", {})
                        if savings.get('batteryMinutes', 0) > 0 or savings.get('dataMB', 0) > 0:
                            savings_text = []
                            if savings.get('batteryMinutes', 0) > 0:
                                savings_text.append(f"{savings.get('batteryMinutes', 0)} min battery")
                            if savings.get('dataMB', 0) > 0:
                                savings_text.append(f"{savings.get('dataMB', 0)} MB data")
                            
                            print(f"🔋 Savings: {', '.join(savings_text)}")
                        
                        # Log to file
                        log_file.write("RECOMMENDATION SUMMARY:\n")
                        if strategy_focus == "battery":
                            log_file.write(f"Focus: Battery optimization ({len(battery_actionables)} actions)\n")
                        elif strategy_focus == "data":
                            log_file.write(f"Focus: Data optimization ({len(data_actionables)} actions)\n")
                        elif strategy_focus == "both":
                            log_file.write(f"Focus: Both battery and data ({len(battery_actionables)} battery actions, {len(data_actionables)} data actions)\n")
                        else:
                            log_file.write(f"Focus: General optimization\n")
                        
                        if system_actions:
                            system_types = [a.get("type") for a in system_actions]
                            log_file.write(f"System changes: {', '.join(system_types)}\n")
                        
                        if critical_apps:
                            log_file.write(f"Protected apps: {', '.join(critical_apps)}\n")
                        
                        if savings.get('batteryMinutes', 0) > 0 or savings.get('dataMB', 0) > 0:
                            savings_text = []
                            if savings.get('batteryMinutes', 0) > 0:
                                savings_text.append(f"{savings.get('batteryMinutes', 0)} min battery")
                            if savings.get('dataMB', 0) > 0:
                                savings_text.append(f"{savings.get('dataMB', 0)} MB data")
                            
                            log_file.write(f"Savings: {', '.join(savings_text)}\n")
                        
                        log_file.write("\n")
                    
                else:
                    print_colored(f"❌ API Error: {response.status_code}", "red")
                    test_result["error"] = f"API returned status code {response.status_code}"
                    
                    log_file.write(f"API Error: {response.status_code}\n\n")
            except Exception as e:
                print_colored(f"❌ Request Error: {str(e)}", "red")
                test_result["error"] = f"Request failed: {str(e)}"
                
                log_file.write(f"Request Error: {str(e)}\n\n")
            
            prompt_results.append(test_result)
        
        all_results.append({
            "prompt": prompt,
            "results": prompt_results
        })
    
    print_header("BATTERY AND DATA COMBINATIONS TESTING COMPLETE")
    log_file.write("\nBATTERY AND DATA COMBINATIONS TESTING COMPLETE\n")
    log_file.write("=" * 80 + "\n\n")
    
    return all_results

def format_summary_results(results, combination_results, log_file):
    """Format summary results and save to log file"""
    print_header("TEST SUMMARY")
    log_file.write("\nTEST SUMMARY\n")
    log_file.write("=" * 80 + "\n\n")
    
    # Main results summary
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get("success", False))
    
    print(f"Total Prompts Tested: {total_tests}")
    print(f"Successful Tests: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    
    log_file.write(f"Total Prompts Tested: {total_tests}\n")
    log_file.write(f"Successful Tests: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)\n\n")
    
    # Summary table
    print_section("PROMPT SUMMARY TABLE")
    log_file.write("PROMPT SUMMARY TABLE:\n")
    log_file.write("-" * 110 + "\n")
    
    header = f"{'PROMPT':<40} | {'SUCCESS':<8} | {'ACTIONABLES':<12} | {'INSIGHTS':<10} | {'BATTERY SAVED':<15} | {'DATA SAVED':10}"
    print(header)
    print("-" * len(header))
    log_file.write(f"{header}\n")
    log_file.write("-" * 110 + "\n")
    
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
            
            row = f"{prompt:<40} | {'✅':<8} | {actionables:<12} | {insights:<10} | {battery_saved:<15} | {data_saved:<10}"
            print(row)
            log_file.write(f"{prompt:<40} | {'Success':<8} | {actionables:<12} | {insights:<10} | {battery_saved:<15} | {data_saved:<10}\n")
        else:
            row = f"{prompt:<40} | {'❌':<8} | {'N/A':<12} | {'N/A':<10} | {'N/A':<15} | {'N/A':<10}"
            print(row)
            log_file.write(f"{prompt:<40} | {'Error':<8} | {'N/A':<12} | {'N/A':<10} | {'N/A':<15} | {'N/A':<10}\n")
    
    # Combination results summary
    if combination_results:
        print_section("COMBINATION TEST SUMMARY")
        log_file.write("\n\nCOMBINATION TEST SUMMARY:\n")
        log_file.write("-" * 80 + "\n")
        
        total_combo_tests = sum(len(prompt_data["results"]) for prompt_data in combination_results)
        correct_focus_count = 0
        
        for prompt_data in combination_results:
            for result in prompt_data["results"]:
                if result.get("success", False) and result.get("correct_focus", False):
                    correct_focus_count += 1
        
        accuracy = (correct_focus_count / total_combo_tests) * 100 if total_combo_tests > 0 else 0
        
        print(f"Total Combination Tests: {total_combo_tests}")
        print(f"Correct Focus Predictions: {correct_focus_count}/{total_combo_tests} ({accuracy:.1f}%)")
        
        log_file.write(f"Total Combination Tests: {total_combo_tests}\n")
        log_file.write(f"Correct Focus Predictions: {correct_focus_count}/{total_combo_tests} ({accuracy:.1f}%)\n\n")

def format_api_response(response, device_data, curl_cmd, start_time, prompt):
    """Format the API response for display"""
    end_time = time.time()
    execution_time = end_time - start_time
    
    result = f"\n\n================================================================================\n"
    result += f"PROMPT: '{prompt}'\n"
    result += f"================================================================================\n\n"
    
    # Add device data summary
    result += f"DEVICE DATA:\n"
    result += f"  Battery Level: {device_data['battery']['level']}%\n"
    result += f"  Data Downloaded: {int(device_data['network']['dataUsage']['foreground'])} MB\n"
    result += f"  Data Uploaded: {int(device_data['network']['dataUsage']['background'])} MB\n"
    result += f"  Number of Apps: {len(device_data['apps'])}\n\n"
    
    # Add curl command
    result += f"CURL COMMAND: {curl_cmd}\n\n"
    
    if response.status_code != 200:
        result += f"ERROR: {response.status_code}\n"
        result += f"Response: {response.text}\n"
        return result
    
    data = response.json()
    
    # Add actionables
    actionables = data.get("actionable", [])
    if actionables:
        for i, actionable in enumerate(actionables, 1):
            result += f"ACTIONABLE {i}:\n"
            result += f"  Type: {actionable.get('type')}\n"
            result += f"  Package: {actionable.get('packageName', 'system')}\n"
            result += f"  Description: {actionable.get('description')}\n"
            result += f"  Mode: {actionable.get('newMode')}\n\n"
    else:
        result += f"ACTIONABLES: None\n\n"
    
    # Add insights
    insights = data.get("insights", [])
    if insights:
        for i, insight in enumerate(insights, 1):
            result += f"INSIGHT {i}:\n"
            result += f"  Type: {insight.get('type')}\n"
            result += f"  Title: {insight.get('title')}\n"
            result += f"  Description: {insight.get('description')}\n"
            result += f"  Severity: {insight.get('severity')}\n\n"
    
    # Add scores
    scores = data.get("scores", {})
    if scores:
        result += f"SCORES:\n"
        for key, value in scores.items():
            result += f"  {key}: {value}\n"
        result += "\n"
    
    # Add savings
    savings = data.get("estimatedSavings", {})
    if savings:
        result += f"ESTIMATED SAVINGS:\n"
        result += f"  Battery: {savings.get('batteryMinutes', 0)} minutes\n"
        result += f"  Data: {savings.get('dataMB', 0)} MB\n\n"
    
    # Add summary
    result += f"HUMAN-READABLE SUMMARY:\n"
    result += format_human_readable_summary(data)
    result += f"\n\nRequest completed in {execution_time:.2f} seconds\n"
    
    return result

def analyze_temperature_data(device_data, data_apps, battery_apps):
    """Analyze temperature data to detect potential issues"""
    # Check battery temperature
    battery_temp = device_data.get("battery", {}).get("temperature", 0)
    if battery_temp > 42:
        return {
            "type": "Warning",
            "title": "High Battery Temperature",
            "description": f"Your device battery temperature is {battery_temp}°C, which is higher than normal. This can cause faster battery drain and potential damage.",
            "severity": "high"
        }
    
    # Check CPU temperature
    cpu_temp = device_data.get("cpu", {}).get("temperature", 0)
    if cpu_temp > 50:
        return {
            "type": "Warning",
            "title": "High CPU Temperature",
            "description": f"Your device CPU temperature is {cpu_temp}°C, which is higher than normal. This can affect performance and battery life.",
            "severity": "medium"
        }
    
    return None

def add_mock_data_to_json(device_data):
    """Add mock data to the device data"""
    # If testing apps that drain battery, shuffle the battery usage values
    if "battery" in device_data.get("prompt", "").lower():
        # Sort apps by battery usage for consistent results in test
        apps_by_battery = sorted(device_data['apps'], key=lambda x: float(x.get('batteryUsage', 0) or 0), reverse=True)[:3]
        
        # Ensure these use the most battery
        for i, app in enumerate(apps_by_battery):
            app['batteryUsage'] = 30 - (i * 5)  # 30%, 25%, 20%
            
    # If testing apps that drain data, shuffle the data usage values
    if "data" in device_data.get("prompt", "").lower():
        # Sort apps by data usage
        apps_by_data = sorted(device_data['apps'], 
                              key=lambda x: float(x.get('dataUsage', {}).get('foreground', 0) or 0) + 
                                           float(x.get('dataUsage', {}).get('background', 0) or 0), 
                              reverse=True)[:3]
        
        # Set to consistent data usage values
        data_values = [450, 380, 340]
        for i, app in enumerate(apps_by_data[:3]):
            if isinstance(app.get('dataUsage'), dict):
                app['dataUsage']['foreground'] = data_values[i] * 0.8
                app['dataUsage']['background'] = data_values[i] * 0.2

def main():
    # Create timestamp for the test run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results.txt"
    
    print_header("POWERGUARD API TEST SUITE")
    print(f"Starting test run at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results will be saved to {output_file}")
    
    # First, reset the database
    reset_database()
    
    # Open log file
    with open(output_file, "w") as log_file:
        # Write header
        log_file.write("POWERGUARD API TEST RESULTS\n")
        log_file.write("=" * 80 + "\n")
        log_file.write(f"Test Run: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        print(f"\n🧪 Running tests for {len(TEST_PROMPTS)} prompts...")
        
        # Run the main tests
        results = []
        for prompt in TEST_PROMPTS:
            result = run_api_test(prompt, log_file)
            results.append(result)
        
        # Run the battery and data combination tests
        combination_results = test_battery_data_combinations(log_file)
        
        # Format and save summary results
        format_summary_results(results, combination_results, log_file)
        
    print_header("TEST RUN COMPLETE")
    print(f"✅ All test results saved to {output_file}")

if __name__ == "__main__":
    main() 