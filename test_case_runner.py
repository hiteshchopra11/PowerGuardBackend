import requests
import json
import argparse
from datetime import datetime
import time
import sys
from typing import Dict, Any, Optional

# Base URL for the API
BASE_URL = "https://powerguardbackend.onrender.com"

def generate_test_payload(prompt: Optional[str] = None) -> Dict[str, Any]:
    """Generate a test payload with fixed data for consistent testing"""
    current_time = int(datetime.now().timestamp())
    
    # Create a payload with predictable values
    payload = {
        "deviceId": "test_device_debug_001",
        "timestamp": current_time,
        "battery": {
            "level": 25.5,  # Low battery level to trigger battery-related actions
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
            # A heavy battery using app
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
            # A heavy data using app
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
            },
            # A normal app
            {
                "packageName": "com.example.normalapp",
                "processName": "com.example.normalapp",
                "appName": "Normal App",
                "isSystemApp": False,
                "lastUsed": current_time - 1200,
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
                "installTime": current_time - 172800,
                "updatedTime": current_time - 86400
            }
        ]
    }
    
    # Add the prompt if provided
    if prompt is not None:
        payload["prompt"] = prompt
    
    return payload

def test_api_endpoint(prompt: Optional[str] = None, analyze: bool = True) -> None:
    """
    Test either the /api/analyze endpoint or the appropriate test endpoint
    
    Parameters:
    - prompt: Optional prompt to include in the request
    - analyze: If True, test the real /api/analyze endpoint, otherwise test the test endpoints
    """
    if analyze:
        # Test the real analyze endpoint
        url = f"{BASE_URL}/api/analyze"
        payload = generate_test_payload(prompt)
        
        print(f"\n{'=' * 80}")
        print(f"Testing /api/analyze endpoint {f'with prompt: \"{prompt}\"' if prompt else 'without prompt'}")
        print(f"{'=' * 80}")
        
        print("\nRequest Payload:")
        print("-" * 40)
        print(json.dumps(payload, indent=2))
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload)
            response_time = time.time() - start_time
            
            print(f"\nResponse (took {response_time:.2f} seconds):")
            print("-" * 40)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\nResponse JSON:")
                print(json.dumps(result, indent=2))
                
                # Analyze the response
                print("\nAnalysis of Response:")
                print("-" * 40)
                
                # Check if required fields are present
                required_fields = ["id", "success", "timestamp", "message", "actionable", 
                                   "insights", "batteryScore", "dataScore", "performanceScore", 
                                   "estimatedSavings"]
                
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    print(f"Missing fields: {', '.join(missing_fields)}")
                else:
                    print("All required fields are present")
                
                # Analyze actionable items
                actionable_items = result.get("actionable", [])
                print(f"\nActionable Items: {len(actionable_items)}")
                for i, action in enumerate(actionable_items):
                    print(f"  {i+1}. Type: {action.get('type')}")
                    print(f"     Package: {action.get('packageName')}")
                    print(f"     Description: {action.get('description')}")
                    print(f"     Reason: {action.get('reason')}")
                
                # Analyze insights
                insights = result.get("insights", [])
                print(f"\nInsights: {len(insights)}")
                for i, insight in enumerate(insights):
                    print(f"  {i+1}. Type: {insight.get('type')}")
                    print(f"     Title: {insight.get('title')}")
                    print(f"     Severity: {insight.get('severity')}")
                
                # Analyze scores
                print(f"\nScores:")
                print(f"  Battery Score: {result.get('batteryScore')}")
                print(f"  Data Score: {result.get('dataScore')}")
                print(f"  Performance Score: {result.get('performanceScore')}")
                
                # Analyze savings
                savings = result.get("estimatedSavings", {})
                print(f"\nEstimated Savings:")
                print(f"  Battery Minutes: {savings.get('batteryMinutes')}")
                print(f"  Data MB: {savings.get('dataMB')}")
                
                # Check if response seems to align with prompt
                if prompt:
                    prompt_lower = prompt.lower()
                    battery_related = any(term in prompt_lower for term in ["battery", "power", "energy"])
                    data_related = any(term in prompt_lower for term in ["data", "network", "internet"])
                    
                    print(f"\nPrompt Analysis:")
                    print(f"  Battery-related prompt: {battery_related}")
                    print(f"  Data-related prompt: {data_related}")
                    
                    battery_actions = any("BATTERY" in action.get("type", "") for action in actionable_items)
                    data_actions = any("DATA" in action.get("type", "") for action in actionable_items)
                    
                    print(f"  Battery-related actions: {battery_actions}")
                    print(f"  Data-related actions: {data_actions}")
                    
                    if battery_related and not battery_actions:
                        print("  WARNING: Prompt mentions battery but no battery actions found")
                    if data_related and not data_actions:
                        print("  WARNING: Prompt mentions data but no data actions found")
            else:
                print(f"Error response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {str(e)}")
    else:
        # Test the test endpoints
        if prompt:
            url = f"{BASE_URL}/api/test/with-prompt/{prompt}"
            print(f"\n{'=' * 80}")
            print(f"Testing /api/test/with-prompt/{prompt} endpoint")
            print(f"{'=' * 80}")
        else:
            url = f"{BASE_URL}/api/test/no-prompt"
            print(f"\n{'=' * 80}")
            print(f"Testing /api/test/no-prompt endpoint")
            print(f"{'=' * 80}")
        
        try:
            start_time = time.time()
            response = requests.get(url)
            response_time = time.time() - start_time
            
            print(f"\nResponse (took {response_time:.2f} seconds):")
            print("-" * 40)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\nResponse JSON:")
                print(json.dumps(result, indent=2))
                
                # Simple analysis
                actionable_items = result.get("actionable", [])
                insights = result.get("insights", [])
                
                print(f"\nActionable Items: {len(actionable_items)}")
                print(f"Insights: {len(insights)}")
                
                if prompt:
                    prompt_lower = prompt.lower()
                    battery_related = any(term in prompt_lower for term in ["battery", "power", "energy"])
                    data_related = any(term in prompt_lower for term in ["data", "network", "internet"])
                    
                    battery_actions = any("BATTERY" in action.get("type", "") for action in actionable_items)
                    data_actions = any("DATA" in action.get("type", "") for action in actionable_items)
                    
                    print(f"\nPrompt '{prompt}' seems to be:")
                    if battery_related:
                        print(f"  Battery-related")
                    if data_related:
                        print(f"  Data-related")
                    
                    print(f"\nFound actions related to:")
                    if battery_actions:
                        print(f"  Battery optimization")
                    if data_actions:
                        print(f"  Data optimization")
            else:
                print(f"Error response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {str(e)}")

def test_root_endpoint() -> None:
    """Test the root endpoint to check if the API is running"""
    url = f"{BASE_URL}/"
    print(f"\n{'=' * 80}")
    print(f"Testing root endpoint: {url}")
    print(f"{'=' * 80}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get("message") == "PowerGuard AI Backend is running":
                print("Root endpoint test: PASSED")
            else:
                print(f"Root endpoint test: FAILED - Unexpected response")
        else:
            print(f"Error response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test runner for PowerGuard API")
    parser.add_argument("--url", type=str, default=BASE_URL, 
                        help=f"Base URL for the API (default: {BASE_URL})")
    parser.add_argument("--prompt", type=str, 
                        help="Prompt to send with the request (optional)")
    parser.add_argument("--test", action="store_true", 
                        help="Use test endpoints instead of real analyze endpoint")
    parser.add_argument("--root", action="store_true", 
                        help="Test the root endpoint only")
    
    args = parser.parse_args()
    
    # Use custom URL if provided
    api_url = args.url
    if args.url != BASE_URL:
        print(f"Using API URL: {api_url}")
    
    # Define patched test functions if using custom URL
    if api_url != BASE_URL:
        def patched_test_root_endpoint():
            """Test the root endpoint to check if the API is running with custom URL"""
            url = f"{api_url}/"
            print(f"\n{'=' * 80}")
            print(f"Testing root endpoint: {url}")
            print(f"{'=' * 80}")
            
            try:
                response = requests.get(url)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
                    if result.get("message") == "PowerGuard AI Backend is running":
                        print("Root endpoint test: PASSED")
                    else:
                        print(f"Root endpoint test: FAILED - Unexpected response")
                else:
                    print(f"Error response: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Error making API request: {str(e)}")
        
        def patched_test_api_endpoint(prompt, analyze):
            """Test either the /api/analyze endpoint or the appropriate test endpoint with custom URL"""
            if analyze:
                # Test the real analyze endpoint
                url = f"{api_url}/api/analyze"
                payload = generate_test_payload(prompt)
                
                print(f"\n{'=' * 80}")
                print(f"Testing /api/analyze endpoint {f'with prompt: \"{prompt}\"' if prompt else 'without prompt'}")
                print(f"{'=' * 80}")
                
                print("\nRequest Payload:")
                print("-" * 40)
                print(json.dumps(payload, indent=2))
                
                try:
                    start_time = time.time()
                    response = requests.post(url, json=payload)
                    response_time = time.time() - start_time
                    
                    print(f"\nResponse (took {response_time:.2f} seconds):")
                    print("-" * 40)
                    print(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("\nResponse JSON:")
                        print(json.dumps(result, indent=2))
                        
                        # Analyze the response
                        print("\nAnalysis of Response:")
                        print("-" * 40)
                        
                        # Check if required fields are present
                        required_fields = ["id", "success", "timestamp", "message", "actionable", 
                                           "insights", "batteryScore", "dataScore", "performanceScore", 
                                           "estimatedSavings"]
                        
                        missing_fields = [field for field in required_fields if field not in result]
                        if missing_fields:
                            print(f"Missing fields: {', '.join(missing_fields)}")
                        else:
                            print("All required fields are present")
                        
                        # Analyze actionable items
                        actionable_items = result.get("actionable", [])
                        print(f"\nActionable Items: {len(actionable_items)}")
                        for i, action in enumerate(actionable_items):
                            print(f"  {i+1}. Type: {action.get('type')}")
                            print(f"     Package: {action.get('packageName')}")
                            print(f"     Description: {action.get('description')}")
                            print(f"     Reason: {action.get('reason')}")
                        
                        # Analyze insights
                        insights = result.get("insights", [])
                        print(f"\nInsights: {len(insights)}")
                        for i, insight in enumerate(insights):
                            print(f"  {i+1}. Type: {insight.get('type')}")
                            print(f"     Title: {insight.get('title')}")
                            print(f"     Severity: {insight.get('severity')}")
                        
                        # Analyze scores
                        print(f"\nScores:")
                        print(f"  Battery Score: {result.get('batteryScore')}")
                        print(f"  Data Score: {result.get('dataScore')}")
                        print(f"  Performance Score: {result.get('performanceScore')}")
                        
                        # Analyze savings
                        savings = result.get("estimatedSavings", {})
                        print(f"\nEstimated Savings:")
                        print(f"  Battery Minutes: {savings.get('batteryMinutes')}")
                        print(f"  Data MB: {savings.get('dataMB')}")
                        
                        # Check if response seems to align with prompt
                        if prompt:
                            prompt_lower = prompt.lower()
                            battery_related = any(term in prompt_lower for term in ["battery", "power", "energy"])
                            data_related = any(term in prompt_lower for term in ["data", "network", "internet"])
                            
                            print(f"\nPrompt Analysis:")
                            print(f"  Battery-related prompt: {battery_related}")
                            print(f"  Data-related prompt: {data_related}")
                            
                            battery_actions = any("BATTERY" in action.get("type", "") for action in actionable_items)
                            data_actions = any("DATA" in action.get("type", "") for action in actionable_items)
                            
                            print(f"  Battery-related actions: {battery_actions}")
                            print(f"  Data-related actions: {data_actions}")
                            
                            if battery_related and not battery_actions:
                                print("  WARNING: Prompt mentions battery but no battery actions found")
                            if data_related and not data_actions:
                                print("  WARNING: Prompt mentions data but no data actions found")
                    else:
                        print(f"Error response: {response.text}")
                except requests.exceptions.RequestException as e:
                    print(f"Error making API request: {str(e)}")
            else:
                # Test the test endpoints
                if prompt:
                    url = f"{api_url}/api/test/with-prompt/{prompt}"
                    print(f"\n{'=' * 80}")
                    print(f"Testing /api/test/with-prompt/{prompt} endpoint")
                    print(f"{'=' * 80}")
                else:
                    url = f"{api_url}/api/test/no-prompt"
                    print(f"\n{'=' * 80}")
                    print(f"Testing /api/test/no-prompt endpoint")
                    print(f"{'=' * 80}")
                
                try:
                    start_time = time.time()
                    response = requests.get(url)
                    response_time = time.time() - start_time
                    
                    print(f"\nResponse (took {response_time:.2f} seconds):")
                    print("-" * 40)
                    print(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("\nResponse JSON:")
                        print(json.dumps(result, indent=2))
                        
                        # Simple analysis
                        actionable_items = result.get("actionable", [])
                        insights = result.get("insights", [])
                        
                        print(f"\nActionable Items: {len(actionable_items)}")
                        print(f"Insights: {len(insights)}")
                        
                        if prompt:
                            prompt_lower = prompt.lower()
                            battery_related = any(term in prompt_lower for term in ["battery", "power", "energy"])
                            data_related = any(term in prompt_lower for term in ["data", "network", "internet"])
                            
                            battery_actions = any("BATTERY" in action.get("type", "") for action in actionable_items)
                            data_actions = any("DATA" in action.get("type", "") for action in actionable_items)
                            
                            print(f"\nPrompt '{prompt}' seems to be:")
                            if battery_related:
                                print(f"  Battery-related")
                            if data_related:
                                print(f"  Data-related")
                            
                            print(f"\nFound actions related to:")
                            if battery_actions:
                                print(f"  Battery optimization")
                            if data_actions:
                                print(f"  Data optimization")
                    else:
                        print(f"Error response: {response.text}")
                except requests.exceptions.RequestException as e:
                    print(f"Error making API request: {str(e)}")
        
        # Use patched versions
        test_root_fn = patched_test_root_endpoint
        test_api_fn = patched_test_api_endpoint
    else:
        # Use the original functions
        test_root_fn = test_root_endpoint
        test_api_fn = test_api_endpoint
    
    # Test root endpoint only if requested
    if args.root:
        test_root_fn()
        return
    
    # Run the test with the specified parameters
    test_api_fn(args.prompt, not args.test)

if __name__ == "__main__":
    main() 