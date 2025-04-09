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

def test_scenario(prompt, battery_level, data_remaining):
    """Test a scenario with the specified prompt, battery level, and data remaining."""
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
    
    result = {
        "prompt": prompt,
        "battery_level": battery_level,
        "data_remaining": data_remaining,
        "scenario": get_scenario_name(battery_level, data_remaining),
        "success": False
    }
    
    try:
        # Call the API
        print("Calling API...")
        response = requests.post(
            "http://localhost:8000/api/analyze",
            json=device_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            result["success"] = True
            result["response"] = data
            
            # Extract key information
            insights = data.get("insights", [])
            actionables = data.get("actionable", [])
            
            # Check focus based on battery and data levels
            battery_actionables = [a for a in actionables if "BATTERY" in a.get("type", "") or a.get("type") == "OPTIMIZE_BATTERY"]
            data_actionables = [a for a in actionables if "DATA" in a.get("type", "") or a.get("type") == "ENABLE_DATA_SAVER"]
            
            result["battery_action_count"] = len(battery_actionables)
            result["data_action_count"] = len(data_actionables)
            
            # Determine if the focus is correct based on the scenario
            battery_critical = battery_level <= 20
            data_critical = data_remaining <= 100
            
            if battery_critical and data_critical:
                # Both low - should have both types of actions
                result["expected_focus"] = "both"
                result["correct_focus"] = len(battery_actionables) > 0 and len(data_actionables) > 0
            elif battery_critical:
                # Low battery, high data - should focus on battery
                result["expected_focus"] = "battery"
                result["correct_focus"] = len(battery_actionables) > len(data_actionables)
            elif data_critical:
                # High battery, low data - should focus on data
                result["expected_focus"] = "data"
                result["correct_focus"] = len(data_actionables) > len(battery_actionables)
            else:
                # Both high - general optimization
                result["expected_focus"] = "balanced"
                result["correct_focus"] = True
            
            print(f"Focus correct: {result['correct_focus']} (Battery actions: {len(battery_actionables)}, Data actions: {len(data_actionables)})")
            
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
            result["error"] = f"API returned status code {response.status_code}"
        else:
            print(f"API Error: {response.status_code}")
            result["error"] = f"API returned status code {response.status_code}"
    except Exception as e:
        print(f"Request Error: {str(e)}")
        result["error"] = f"Request failed: {str(e)}"
    
    return result

def get_scenario_name(battery_level, data_remaining):
    """Get a descriptive name for the scenario."""
    battery_status = "Low Battery" if battery_level <= 20 else "High Battery"
    data_status = "Low Data" if data_remaining <= 100 else "High Data"
    return f"{battery_status}, {data_status}"

def test_all_scenarios(prompt):
    """Test all four battery/data combinations for a single prompt."""
    # Combinations of battery and data states
    scenarios = [
        {"battery_level": 15, "data_remaining": 50},    # Low Battery, Low Data
        {"battery_level": 15, "data_remaining": 2000},  # Low Battery, High Data
        {"battery_level": 85, "data_remaining": 50},    # High Battery, Low Data
        {"battery_level": 85, "data_remaining": 2000}   # High Battery, High Data
    ]
    
    results = []
    
    for scenario in scenarios:
        battery_level = scenario["battery_level"]
        data_remaining = scenario["data_remaining"]
        
        # Run the test
        result = test_scenario(prompt, battery_level, data_remaining)
        results.append(result)
        
        # Wait a full minute before next API call to avoid rate limits
        if scenario != scenarios[-1]:  # Don't wait after the last scenario
            print(f"\nWaiting 60 seconds before next API call to avoid rate limits...")
            time.sleep(60)
    
    return results

def format_results(results):
    """Format the results as a summary."""
    output = []
    output.append("\nRESULTS SUMMARY")
    output.append("=" * 80)
    
    # Count successful and correct tests
    successful_tests = sum(1 for r in results if r.get("success", False))
    correct_focus_tests = sum(1 for r in results if r.get("success", False) and r.get("correct_focus", False))
    
    output.append(f"Prompt tested: {results[0]['prompt']}")
    output.append(f"Successful tests: {successful_tests}/4")
    
    if successful_tests > 0:
        accuracy = (correct_focus_tests / successful_tests) * 100
        output.append(f"Correct focus predictions: {correct_focus_tests}/{successful_tests} ({accuracy:.1f}%)")
    
    output.append("\nSCENARIO SUMMARY:")
    output.append("-" * 80)
    output.append(f"{'SCENARIO':<20} | {'SUCCESS':<8} | {'EXPECTED FOCUS':<15} | {'BATTERY ACTIONS':<15} | {'DATA ACTIONS':<12} | {'CORRECT':<7}")
    output.append("-" * 80)
    
    for result in results:
        scenario = result.get("scenario", "Unknown")
        success = "✓" if result.get("success", False) else "✗"
        expected = result.get("expected_focus", "N/A")
        battery_count = result.get("battery_action_count", 0)
        data_count = result.get("data_action_count", 0)
        correct = "✓" if result.get("correct_focus", False) else "✗"
        
        output.append(f"{scenario:<20} | {success:<8} | {expected:<15} | {battery_count:<15} | {data_count:<12} | {correct:<7}")
    
    output.append("-" * 80)
    
    # Show details for each successful test
    for result in results:
        if result.get("success", False):
            scenario = result.get("scenario", "Unknown")
            output.append("")
            output.append("=" * 80)
            output.append(f"SCENARIO: {scenario}")
            output.append(f"Expected Focus: {result.get('expected_focus', 'N/A')}")
            output.append(f"Correct Focus: {result.get('correct_focus', 'N/A')}")
            output.append("")
            
            if "response" in result:
                resp = result["response"]
                
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

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python single_test.py \"<prompt>\"")
        print("Example: python single_test.py \"Optimize my device for longer usage time\"")
        return
    
    # Parse command line argument
    prompt = sys.argv[1]
    
    print(f"Testing all scenarios for prompt: '{prompt}'")
    print("This will test 4 combinations of battery and data levels with 60-second delays between tests.")
    print("The entire test will take about 3 minutes to complete.")
    print("\nStarting tests...")
    
    # Run tests for all scenarios
    results = test_all_scenarios(prompt)
    
    # Format and display results
    formatted_results = format_results(results)
    print(formatted_results)
    
    # Save results to files
    timestamp = int(time.time())
    
    # Save detailed results
    detailed_file = f"detailed_results_{timestamp}.json"
    with open(detailed_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save summary
    summary_file = f"summary_results_{timestamp}.txt"
    with open(summary_file, "w") as f:
        f.write(formatted_results)
    
    print(f"\nDetailed results saved to {detailed_file}")
    print(f"Summary saved to {summary_file}")

if __name__ == "__main__":
    main() 