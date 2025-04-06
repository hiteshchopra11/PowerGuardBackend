import requests
import json
import argparse
from datetime import datetime
import time
import sys
from typing import Dict, Any, List, Optional, Tuple
import random

# Base URL for the deployed API
BASE_URL = "https://powerguardbackend.onrender.com"

# Global variable for verbose output
VERBOSE = True

# Test cases - each test case has a name, prompt, and expected output validation function
TEST_CASES = [
    {
        "name": "No prompt",
        "prompt": None,
        "validation_fn": lambda response: (
            len(response.get("actionable", [])) > 0 and
            len(response.get("insights", [])) > 0
        )
    },
    {
        "name": "Battery optimization",
        "prompt": "Optimize my battery life",
        "validation_fn": lambda response: (
            any("BATTERY" in action.get("type", "") for action in response.get("actionable", []))
        )
    },
    {
        "name": "Data optimization",
        "prompt": "Save my network data",
        "validation_fn": lambda response: (
            any("DATA" in action.get("type", "") for action in response.get("actionable", []))
        )
    },
    {
        "name": "Combined optimization",
        "prompt": "Save both battery and network data",
        "validation_fn": lambda response: (
            any("BATTERY" in action.get("type", "") for action in response.get("actionable", [])) and
            any("DATA" in action.get("type", "") for action in response.get("actionable", []))
        )
    },
    {
        "name": "Specific action",
        "prompt": "Kill battery-draining apps",
        "validation_fn": lambda response: (
            any("KILL" in action.get("type", "") for action in response.get("actionable", []))
        )
    },
    {
        "name": "Negation handling",
        "prompt": "Optimize battery but not data",
        "validation_fn": lambda response: (
            any("BATTERY" in action.get("type", "") for action in response.get("actionable", [])) and
            not any("DATA" in action.get("type", "") for action in response.get("actionable", []))
        )
    },
    {
        "name": "Irrelevant prompt",
        "prompt": "What's the weather like today?",
        "validation_fn": lambda response: (
            len(response.get("actionable", [])) > 0  # Should still generate some actions
        )
    },
    {
        "name": "Empty prompt",
        "prompt": "",
        "validation_fn": lambda response: (
            len(response.get("actionable", [])) > 0  # Should work like no prompt
        )
    },
    {
        "name": "Extremely long prompt",
        "prompt": "I need to save battery life " * 20,  # Repeat to make it long
        "validation_fn": lambda response: (
            response.get("success") is True  # Should still succeed
        )
    },
    {
        "name": "Special characters",
        "prompt": "Save battery life! (urgent) @ #$%^",
        "validation_fn": lambda response: (
            any("BATTERY" in action.get("type", "") for action in response.get("actionable", []))
        )
    },
]

# Test endpoints
ENDPOINTS = {
    "root": "/",
    "analyze": "/api/analyze",
    "test_with_prompt": "/api/test/with-prompt/{prompt}",
    "test_no_prompt": "/api/test/no-prompt"
}

def log(message: str, level: str = "INFO") -> None:
    """Custom logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")

def log_verbose(message: str, level: str = "DEBUG") -> None:
    """Log only in verbose mode"""
    if VERBOSE:
        log(message, level)

def generate_test_payload(prompt: Optional[str] = None) -> Dict[str, Any]:
    """Generate a test payload with realistic but randomized device data"""
    current_time = int(datetime.now().timestamp())
    
    # Generate random battery level between 10% and 95%
    battery_level = random.uniform(10.0, 95.0)
    
    # Generate random CPU usage between 10% and 90%
    cpu_usage = random.uniform(10.0, 90.0)
    
    # Base payload
    payload = {
        "deviceId": f"test_device_{random.randint(1000, 9999)}",
        "timestamp": current_time,
        "battery": {
            "level": battery_level,
            "temperature": random.uniform(30.0, 45.0),
            "voltage": random.uniform(3500.0, 4200.0),
            "isCharging": random.choice([True, False]),
            "chargingType": random.choice(["None", "AC", "USB", "Wireless"]),
            "health": random.randint(70, 100),
            "capacity": random.uniform(3000.0, 5000.0),
            "currentNow": random.uniform(200.0, 600.0)
        },
        "memory": {
            "totalRam": 8192.0,
            "availableRam": random.uniform(512.0, 4096.0),
            "lowMemory": battery_level < 30.0,  # Low memory if battery is low
            "threshold": 512.0
        },
        "cpu": {
            "usage": cpu_usage,
            "temperature": random.uniform(35.0, 50.0),
            "frequencies": [
                random.uniform(1500.0, 2500.0) for _ in range(4)
            ]
        },
        "network": {
            "type": random.choice(["WIFI", "MOBILE", "NONE"]),
            "strength": random.uniform(30.0, 95.0),
            "isRoaming": random.choice([True, False]),
            "dataUsage": {
                "foreground": random.uniform(50.0, 200.0),
                "background": random.uniform(20.0, 150.0),
                "rxBytes": random.uniform(50000.0, 500000.0),
                "txBytes": random.uniform(20000.0, 200000.0)
            },
            "activeConnectionInfo": random.choice(["WiFi-Home", "Mobile-4G", "Mobile-5G"]),
            "linkSpeed": random.uniform(20.0, 150.0),
            "cellularGeneration": random.choice(["None", "3G", "4G", "5G"])
        },
        "apps": []
    }
    
    # Generate between 3 and 10 apps
    for i in range(random.randint(3, 10)):
        is_battery_heavy = random.random() < 0.3
        is_data_heavy = random.random() < 0.3
        
        app = {
            "packageName": f"com.example.app{i}",
            "processName": f"com.example.app{i}",
            "appName": f"App {i}",
            "isSystemApp": random.random() < 0.2,
            "lastUsed": current_time - random.randint(0, 86400),
            "foregroundTime": random.uniform(300.0, 3600.0),
            "backgroundTime": random.uniform(600.0, 7200.0),
            "batteryUsage": random.uniform(1.0, 20.0) if is_battery_heavy else random.uniform(0.1, 5.0),
            "dataUsage": {
                "foreground": random.uniform(10.0, 100.0) if is_data_heavy else random.uniform(0.1, 10.0),
                "background": random.uniform(5.0, 50.0) if is_data_heavy else random.uniform(0.1, 5.0),
                "rxBytes": random.uniform(10000.0, 100000.0) if is_data_heavy else random.uniform(1000.0, 10000.0),
                "txBytes": random.uniform(5000.0, 50000.0) if is_data_heavy else random.uniform(500.0, 5000.0)
            },
            "memoryUsage": random.uniform(50.0, 500.0),
            "cpuUsage": random.uniform(1.0, 25.0),
            "notifications": random.randint(0, 50),
            "crashes": random.randint(0, 5),
            "versionName": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "versionCode": random.randint(100, 500),
            "targetSdkVersion": random.randint(26, 33),
            "installTime": current_time - random.randint(86400, 2592000),
            "updatedTime": current_time - random.randint(0, 86400)
        }
        payload["apps"].append(app)
    
    # Add at least one heavy battery app and one heavy data app
    heavy_battery_app = {
        "packageName": "com.example.heavybattery",
        "processName": "com.example.heavybattery",
        "appName": "Heavy Battery App",
        "isSystemApp": False,
        "lastUsed": current_time - 300,
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
        "installTime": current_time - 86400,
        "updatedTime": current_time - 3600
    }
    
    heavy_data_app = {
        "packageName": "com.example.heavydata",
        "processName": "com.example.heavydata",
        "appName": "Heavy Data App",
        "isSystemApp": False,
        "lastUsed": current_time - 600,
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
        "installTime": current_time - 172800,
        "updatedTime": current_time - 7200
    }
    
    payload["apps"].append(heavy_battery_app)
    payload["apps"].append(heavy_data_app)
    
    # Add prompt if provided
    if prompt is not None:
        payload["prompt"] = prompt
    
    return payload

def test_root_endpoint() -> bool:
    """Test if the API is running by calling the root endpoint"""
    url = f"{BASE_URL}/"
    log(f"Testing root endpoint: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        if VERBOSE:
            log_verbose(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("message") == "PowerGuard AI Backend is running":
            log("Root endpoint test: PASSED", "SUCCESS")
            return True
        else:
            log(f"Root endpoint test: FAILED - Unexpected response: {result}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"Error making API request to root endpoint: {str(e)}", "ERROR")
        return False

def test_analyze_endpoint(test_case: Dict[str, Any]) -> bool:
    """Test the /api/analyze endpoint with the given test case"""
    name = test_case["name"]
    prompt = test_case["prompt"]
    validation_fn = test_case["validation_fn"]
    
    # Create test payload
    payload = generate_test_payload(prompt)
    
    url = f"{BASE_URL}/api/analyze"
    log(f"Testing analyze endpoint with test case: {name}")
    log_verbose(f"URL: {url}")
    log_verbose(f"Prompt: {prompt}")
    
    if VERBOSE:
        log_verbose(f"Request payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if VERBOSE:
            log_verbose(f"Response: {json.dumps(result, indent=2)}")
        
        # Validate the response format
        required_fields = ["id", "success", "timestamp", "message", "actionable", 
                          "insights", "batteryScore", "dataScore", "performanceScore", 
                          "estimatedSavings"]
        
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            log(f"Missing fields in response: {', '.join(missing_fields)}", "ERROR")
            return False
        
        # Validate the response content using the test case validation function
        if validation_fn(result):
            log(f"Test case '{name}': PASSED", "SUCCESS")
            return True
        else:
            log(f"Test case '{name}': FAILED - Response did not meet validation criteria", "ERROR")
            if VERBOSE:
                log_verbose(f"Response that failed validation: {json.dumps(result, indent=2)}")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"Error making API request for test case '{name}': {str(e)}", "ERROR")
        return False

def test_test_endpoints() -> Tuple[bool, bool]:
    """Test the test endpoints that don't require an LLM call"""
    log("Testing /api/test/no-prompt endpoint")
    no_prompt_url = f"{BASE_URL}/api/test/no-prompt"
    
    try:
        no_prompt_response = requests.get(no_prompt_url)
        no_prompt_response.raise_for_status()
        no_prompt_result = no_prompt_response.json()
        
        if VERBOSE:
            log_verbose(f"No-prompt response: {json.dumps(no_prompt_result, indent=2)}")
        
        no_prompt_success = (
            isinstance(no_prompt_result.get("actionable"), list) and 
            len(no_prompt_result.get("actionable", [])) > 0 and
            isinstance(no_prompt_result.get("insights"), list) and
            len(no_prompt_result.get("insights", [])) > 0
        )
        
        if no_prompt_success:
            log("Test endpoint (no-prompt): PASSED", "SUCCESS")
        else:
            log("Test endpoint (no-prompt): FAILED", "ERROR")
        
        # Test with a prompt
        prompt = "save battery"
        log(f"Testing /api/test/with-prompt/{prompt} endpoint")
        with_prompt_url = f"{BASE_URL}/api/test/with-prompt/{prompt}"
        
        with_prompt_response = requests.get(with_prompt_url)
        with_prompt_response.raise_for_status()
        with_prompt_result = with_prompt_response.json()
        
        if VERBOSE:
            log_verbose(f"With-prompt response: {json.dumps(with_prompt_result, indent=2)}")
        
        with_prompt_success = (
            isinstance(with_prompt_result.get("actionable"), list) and 
            len(with_prompt_result.get("actionable", [])) > 0 and
            any("BATTERY" in action.get("type", "") for action in with_prompt_result.get("actionable", []))
        )
        
        if with_prompt_success:
            log("Test endpoint (with-prompt): PASSED", "SUCCESS")
        else:
            log("Test endpoint (with-prompt): FAILED", "ERROR")
            
        return (no_prompt_success, with_prompt_success)
            
    except requests.exceptions.RequestException as e:
        log(f"Error making API request to test endpoints: {str(e)}", "ERROR")
        return (False, False)

def main():
    # Define globals used within this function
    global VERBOSE
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Automated testing for PowerGuard AI Backend API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--url", type=str, default=BASE_URL, help=f"Base URL for the API (default: {BASE_URL})")
    parser.add_argument("--tests", type=str, help="Comma-separated list of test names to run (default: run all)")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to repeat each test (default: 1)")
    
    args = parser.parse_args()
    
    # Set global verbose flag
    VERBOSE = args.verbose
    
    # Use custom URL if provided (using a function-scoped variable for BASE_URL)
    api_url = args.url if args.url else BASE_URL
    if args.url:
        log(f"Using custom API URL: {api_url}")
        
        # Update functions to use this URL instead of BASE_URL
        def patched_test_root_endpoint():
            """Patched version of test_root_endpoint using the custom URL"""
            url = f"{api_url}/"
            log(f"Testing root endpoint: {url}")
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                result = response.json()
                
                if VERBOSE:
                    log_verbose(f"Response: {json.dumps(result, indent=2)}")
                
                if result.get("message") == "PowerGuard AI Backend is running":
                    log("Root endpoint test: PASSED", "SUCCESS")
                    return True
                else:
                    log(f"Root endpoint test: FAILED - Unexpected response: {result}", "ERROR")
                    return False
                    
            except requests.exceptions.RequestException as e:
                log(f"Error making API request to root endpoint: {str(e)}", "ERROR")
                return False
        
        def patched_test_analyze_endpoint(test_case):
            """Patched version of test_analyze_endpoint using the custom URL"""
            name = test_case["name"]
            prompt = test_case["prompt"]
            validation_fn = test_case["validation_fn"]
            
            # Create test payload
            payload = generate_test_payload(prompt)
            
            url = f"{api_url}/api/analyze"
            log(f"Testing analyze endpoint with test case: {name}")
            log_verbose(f"URL: {url}")
            log_verbose(f"Prompt: {prompt}")
            
            if VERBOSE:
                log_verbose(f"Request payload: {json.dumps(payload, indent=2)}")
            
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if VERBOSE:
                    log_verbose(f"Response: {json.dumps(result, indent=2)}")
                
                # Validate the response format
                required_fields = ["id", "success", "timestamp", "message", "actionable", 
                                "insights", "batteryScore", "dataScore", "performanceScore", 
                                "estimatedSavings"]
                
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    log(f"Missing fields in response: {', '.join(missing_fields)}", "ERROR")
                    return False
                
                # Validate the response content using the test case validation function
                if validation_fn(result):
                    log(f"Test case '{name}': PASSED", "SUCCESS")
                    return True
                else:
                    log(f"Test case '{name}': FAILED - Response did not meet validation criteria", "ERROR")
                    if VERBOSE:
                        log_verbose(f"Response that failed validation: {json.dumps(result, indent=2)}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                log(f"Error making API request for test case '{name}': {str(e)}", "ERROR")
                return False
        
        def patched_test_test_endpoints():
            """Patched version of test_test_endpoints using the custom URL"""
            log("Testing /api/test/no-prompt endpoint")
            no_prompt_url = f"{api_url}/api/test/no-prompt"
            
            try:
                no_prompt_response = requests.get(no_prompt_url)
                no_prompt_response.raise_for_status()
                no_prompt_result = no_prompt_response.json()
                
                if VERBOSE:
                    log_verbose(f"No-prompt response: {json.dumps(no_prompt_result, indent=2)}")
                
                no_prompt_success = (
                    isinstance(no_prompt_result.get("actionable"), list) and 
                    len(no_prompt_result.get("actionable", [])) > 0 and
                    isinstance(no_prompt_result.get("insights"), list) and
                    len(no_prompt_result.get("insights", [])) > 0
                )
                
                if no_prompt_success:
                    log("Test endpoint (no-prompt): PASSED", "SUCCESS")
                else:
                    log("Test endpoint (no-prompt): FAILED", "ERROR")
                
                # Test with a prompt
                prompt = "save battery"
                log(f"Testing /api/test/with-prompt/{prompt} endpoint")
                with_prompt_url = f"{api_url}/api/test/with-prompt/{prompt}"
                
                with_prompt_response = requests.get(with_prompt_url)
                with_prompt_response.raise_for_status()
                with_prompt_result = with_prompt_response.json()
                
                if VERBOSE:
                    log_verbose(f"With-prompt response: {json.dumps(with_prompt_result, indent=2)}")
                
                with_prompt_success = (
                    isinstance(with_prompt_result.get("actionable"), list) and 
                    len(with_prompt_result.get("actionable", [])) > 0 and
                    any("BATTERY" in action.get("type", "") for action in with_prompt_result.get("actionable", []))
                )
                
                if with_prompt_success:
                    log("Test endpoint (with-prompt): PASSED", "SUCCESS")
                else:
                    log("Test endpoint (with-prompt): FAILED", "ERROR")
                    
                return (no_prompt_success, with_prompt_success)
                    
            except requests.exceptions.RequestException as e:
                log(f"Error making API request to test endpoints: {str(e)}", "ERROR")
                return (False, False)
            
        # Use patched functions
        test_root_endpoint_fn = patched_test_root_endpoint
        test_analyze_endpoint_fn = patched_test_analyze_endpoint
        test_test_endpoints_fn = patched_test_test_endpoints
    else:
        # Use original functions
        test_root_endpoint_fn = test_root_endpoint
        test_analyze_endpoint_fn = test_analyze_endpoint
        test_test_endpoints_fn = test_test_endpoints
    
    # Parse specific tests to run if provided
    specific_tests = None
    if args.tests:
        specific_tests = [test.strip() for test in args.tests.split(",")]
        log(f"Running specific tests: {', '.join(specific_tests)}")
    
    # Run all tests or specific tests
    if specific_tests:
        # Filter test cases
        filtered_test_cases = [tc for tc in TEST_CASES if tc["name"] in specific_tests]
        if not filtered_test_cases:
            log(f"No matching test cases found for: {', '.join(specific_tests)}", "ERROR")
            sys.exit(1)
        
        # Run filtered tests
        for i in range(args.repeat):
            if args.repeat > 1:
                log(f"\n=== Running test iteration {i+1}/{args.repeat} ===")
            
            # Test root endpoint
            test_root_endpoint_fn()
            
            # Run filtered test cases
            for test_case in filtered_test_cases:
                test_analyze_endpoint_fn(test_case)
    else:
        # Run all tests
        for i in range(args.repeat):
            if args.repeat > 1:
                log(f"\n=== Running test iteration {i+1}/{args.repeat} ===")
                
            # Run tests with custom run_all_tests 
            start_time = time.time()
            log("Starting PowerGuard API automated testing...")
            
            results = {
                "root_endpoint": False,
                "test_endpoints": {
                    "no_prompt": False,
                    "with_prompt": False
                },
                "analyze_tests": {},
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "execution_time": 0
            }
            
            # Test if API is running
            root_result = test_root_endpoint_fn()
            results["root_endpoint"] = root_result
            results["total_tests"] += 1
            if root_result:
                results["passed_tests"] += 1
            else:
                results["failed_tests"] += 1
            
            # Test the test endpoints
            no_prompt_success, with_prompt_success = test_test_endpoints_fn()
            results["test_endpoints"]["no_prompt"] = no_prompt_success
            results["test_endpoints"]["with_prompt"] = with_prompt_success
            results["total_tests"] += 2
            results["passed_tests"] += (1 if no_prompt_success else 0) + (1 if with_prompt_success else 0)
            results["failed_tests"] += (0 if no_prompt_success else 1) + (0 if with_prompt_success else 1)
            
            # Run all test cases
            for test_case in TEST_CASES:
                name = test_case["name"]
                test_result = test_analyze_endpoint_fn(test_case)
                results["analyze_tests"][name] = test_result
                results["total_tests"] += 1
                if test_result:
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            results["execution_time"] = execution_time
            
            # Print summary
            log("\n=== Test Summary ===")
            log(f"Total tests: {results['total_tests']}")
            log(f"Passed tests: {results['passed_tests']}")
            log(f"Failed tests: {results['failed_tests']}")
            log(f"Success rate: {(results['passed_tests'] / results['total_tests']) * 100:.2f}%")
            log(f"Execution time: {execution_time:.2f} seconds")
            
            # Print detailed results if verbose
            if VERBOSE:
                log_verbose("\nDetailed Test Results:")
                log_verbose(f"Root endpoint: {'PASSED' if results['root_endpoint'] else 'FAILED'}")
                log_verbose(f"Test endpoint (no-prompt): {'PASSED' if results['test_endpoints']['no_prompt'] else 'FAILED'}")
                log_verbose(f"Test endpoint (with-prompt): {'PASSED' if results['test_endpoints']['with_prompt'] else 'FAILED'}")
                
                log_verbose("\nAnalyze Endpoint Tests:")
                for name, result in results["analyze_tests"].items():
                    log_verbose(f"{name}: {'PASSED' if result else 'FAILED'}")

if __name__ == "__main__":
    main() 