import json
import time
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

def test_battery_data_combinations():
    """Test combinations of battery and data conditions with 5 specific prompts."""
    print("\n======= TESTING BATTERY AND DATA COMBINATIONS =======")
    
    # 5 prompts to test
    test_prompts = [
        "Optimize my device for longer usage time",
        "I need my phone to last all day while traveling",
        "Make sure I can use navigation and music during my trip",
        "Help me use less resources overall",
        "Make my device more efficient"
    ]
    
    # Combinations of battery and data states
    scenarios = [
        {"name": "Low Battery, Low Data", "battery_level": 15, "data_remaining": 50},
        {"name": "Low Battery, High Data", "battery_level": 15, "data_remaining": 2000},
        {"name": "High Battery, Low Data", "battery_level": 85, "data_remaining": 50},
        {"name": "High Battery, High Data", "battery_level": 85, "data_remaining": 2000}
    ]
    
    all_results = []
    
    for prompt in test_prompts:
        prompt_results = []
        
        for scenario in scenarios:
            print(f"\nTesting: '{prompt}' with {scenario['name']}")
            
            # Create device data with specific battery and data values
            device_data = json.loads(json.dumps(BASE_DEVICE_DATA))  # Deep copy
            device_data["prompt"] = prompt
            device_data["battery"]["level"] = scenario["battery_level"]
            
            # Set data usage to simulate remaining data
            total_data = 3000  # Assume 3GB total monthly data
            used_data = total_data - scenario["data_remaining"]
            device_data["network"]["dataUsage"]["foreground"] = used_data * 0.7  # 70% used in foreground
            device_data["network"]["dataUsage"]["background"] = used_data * 0.3  # 30% used in background
            device_data["network"]["dataUsage"]["rxBytes"] = int(device_data["network"]["dataUsage"]["foreground"] * 1000000)
            device_data["network"]["dataUsage"]["txBytes"] = int(device_data["network"]["dataUsage"]["background"] * 500000)
            
            test_result = {
                "prompt": prompt,
                "scenario": scenario["name"],
                "device_data": device_data,
                "success": False
            }
            
            # Add a much longer delay between requests to avoid rate limiting
            print(f"Waiting 10 seconds before API call...")
            time.sleep(10)
            
            try:
                # Call the API
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
                    if scenario["battery_level"] <= 20 and scenario["data_remaining"] <= 100:
                        # Both low - should have both types of actions
                        test_result["expected_focus"] = "both"
                        test_result["correct_focus"] = len(battery_actionables) > 0 and len(data_actionables) > 0
                    elif scenario["battery_level"] <= 20:
                        # Low battery, high data - should focus on battery
                        test_result["expected_focus"] = "battery"
                        test_result["correct_focus"] = len(battery_actionables) > len(data_actionables)
                    elif scenario["data_remaining"] <= 100:
                        # High battery, low data - should focus on data
                        test_result["expected_focus"] = "data"
                        test_result["correct_focus"] = len(data_actionables) > len(battery_actionables)
                    else:
                        # Both high - general optimization
                        test_result["expected_focus"] = "balanced"
                        test_result["correct_focus"] = True
                    
                    print(f"Focus correct: {test_result['correct_focus']} (Battery actions: {len(battery_actionables)}, Data actions: {len(data_actionables)})")
                elif response.status_code == 429:
                    print(f"Rate limit exceeded. Waiting for 30 seconds...")
                    time.sleep(30)  # Wait much longer if rate limited
                    
                    # Try again with a longer delay pattern
                    print("Retrying API call...")
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
                        
                        # Extract key information (same as above)
                        insights = data.get("insights", [])
                        actionables = data.get("actionable", [])
                        
                        battery_actionables = [a for a in actionables if "BATTERY" in a.get("type", "") or a.get("type") == "OPTIMIZE_BATTERY"]
                        data_actionables = [a for a in actionables if "DATA" in a.get("type", "") or a.get("type") == "ENABLE_DATA_SAVER"]
                        
                        test_result["battery_action_count"] = len(battery_actionables)
                        test_result["data_action_count"] = len(data_actionables)
                        
                        # Same determination logic as above
                        if scenario["battery_level"] <= 20 and scenario["data_remaining"] <= 100:
                            test_result["expected_focus"] = "both"
                            test_result["correct_focus"] = len(battery_actionables) > 0 and len(data_actionables) > 0
                        elif scenario["battery_level"] <= 20:
                            test_result["expected_focus"] = "battery"
                            test_result["correct_focus"] = len(battery_actionables) > len(data_actionables)
                        elif scenario["data_remaining"] <= 100:
                            test_result["expected_focus"] = "data"
                            test_result["correct_focus"] = len(data_actionables) > len(battery_actionables)
                        else:
                            test_result["expected_focus"] = "balanced"
                            test_result["correct_focus"] = True
                        
                        print(f"Retried - Focus correct: {test_result['correct_focus']} (Battery actions: {len(battery_actionables)}, Data actions: {len(data_actionables)})")
                    else:
                        print(f"API Error after retry: {response.status_code}")
                        test_result["error"] = f"API returned status code {response.status_code} after retry"
                else:
                    print(f"API Error: {response.status_code}")
                    test_result["error"] = f"API returned status code {response.status_code}"
            except Exception as e:
                print(f"Request Error: {str(e)}")
                test_result["error"] = f"Request failed: {str(e)}"
            
            prompt_results.append(test_result)
        
        all_results.append({
            "prompt": prompt,
            "results": prompt_results
        })
    
    print("\n======= BATTERY AND DATA COMBINATIONS TESTING COMPLETE =======")
    return all_results

def format_battery_data_results(combination_results):
    """Format battery and data combination test results as text"""
    output = []
    output.append("\n\n")
    output.append("BATTERY AND DATA COMBINATION TEST RESULTS")
    output.append("=" * 80)
    
    total_tests = sum(len(prompt_data["results"]) for prompt_data in combination_results)
    correct_focus_count = 0
    
    for prompt_data in combination_results:
        for result in prompt_data["results"]:
            if result.get("success", False) and result.get("correct_focus", False):
                correct_focus_count += 1
    
    accuracy = (correct_focus_count / total_tests) * 100 if total_tests > 0 else 0
    
    output.append(f"Total combinations tested: {total_tests}")
    output.append(f"Correct focus predictions: {correct_focus_count}/{total_tests} ({accuracy:.1f}%)")
    output.append("")
    
    # Generate summary table
    output.append("COMBINATION SUMMARY TABLE:")
    output.append("-" * 120)
    output.append(f"{'PROMPT':<35} | {'SCENARIO':<20} | {'SUCCESS':<8} | {'EXPECTED FOCUS':<15} | {'BATTERY ACTIONS':<15} | {'DATA ACTIONS':<12} | {'CORRECT':<7}")
    output.append("-" * 120)
    
    for prompt_data in combination_results:
        prompt = prompt_data["prompt"]
        if len(prompt) > 32:
            prompt_display = prompt[:32] + "..."
        else:
            prompt_display = prompt
            
        for result in prompt_data["results"]:
            scenario = result["scenario"]
            success = "✓" if result.get("success", False) else "✗"
            expected = result.get("expected_focus", "N/A")
            battery_count = result.get("battery_action_count", 0)
            data_count = result.get("data_action_count", 0)
            correct = "✓" if result.get("correct_focus", False) else "✗"
            
            output.append(f"{prompt_display:<35} | {scenario:<20} | {success:<8} | {expected:<15} | {battery_count:<15} | {data_count:<12} | {correct:<7}")
    
    output.append("-" * 120)
    
    # Add detailed results for one sample from each prompt
    for prompt_data in combination_results:
        prompt = prompt_data["prompt"]
        output.append("")
        output.append("=" * 80)
        output.append(f"PROMPT: \"{prompt}\"")
        
        # Just show details for the "Low Battery, Low Data" scenario as an example
        low_both_result = next((r for r in prompt_data["results"] if r["scenario"] == "Low Battery, Low Data" and r.get("success", False)), None)
        
        if low_both_result:
            output.append(f"SCENARIO: Low Battery, Low Data")
            output.append(f"Expected Focus: {low_both_result.get('expected_focus', 'N/A')}")
            output.append(f"Correct Focus: {low_both_result.get('correct_focus', 'N/A')}")
            output.append("")
            
            if "response" in low_both_result:
                resp = low_both_result["response"]
                
                # Show battery score and data score
                output.append(f"Battery Score: {resp.get('batteryScore', 'N/A')}")
                output.append(f"Data Score: {resp.get('dataScore', 'N/A')}")
                output.append("")
                
                # Show strategy insight if available
                strategy_insights = [i for i in resp.get("insights", []) if i.get("type") == "Strategy"]
                if strategy_insights:
                    output.append(f"Strategy: {strategy_insights[0].get('title', 'N/A')}")
                    output.append(f"{strategy_insights[0].get('description', 'N/A')}")
                    output.append("")
        
    return "\n".join(output)

def check_api_health():
    """Check if the API is available and responsive"""
    try:
        # Try to reach the API using the simplest endpoint
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("API service is available")
            return True
        else:
            print(f"Root API endpoint returned status code {response.status_code}")
            
            # Try another endpoint
            try:
                response = requests.get("http://localhost:8000/api/analyze")
                print(f"Analyze endpoint returned status code {response.status_code}")
                # Even if we get 405 Method Not Allowed, that means the endpoint exists
                if response.status_code in [200, 405]:
                    return True
            except Exception:
                pass
                
            return False
    except Exception as e:
        print(f"API service is not available: {str(e)}")
        return False

def main():
    # Check if API is available
    if not check_api_health():
        print("API is not available. Please start the API service and try again.")
        return
    
    # First, reset the database
    reset_database()
    
    # Run the battery and data combination tests
    combination_results = test_battery_data_combinations()
    
    # Format and save results to a file
    combination_formatted = format_battery_data_results(combination_results)
    
    with open("battery_data_combination_results.txt", "w") as f:
        f.write(combination_formatted)
    
    print("All test results saved to battery_data_combination_results.txt")

if __name__ == "__main__":
    main() 