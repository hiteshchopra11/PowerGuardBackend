import requests
import json
import time
import argparse
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional
import random
import concurrent.futures

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test prompts
TEST_PROMPTS = {
    "battery": "Optimize my battery life",
    "data": "Save network data usage",
    "combined": "Save both battery and data",
    "specific": "Kill battery-draining apps",
    "none": None
}

def generate_test_payload(prompt: Optional[str] = None, payload_size: str = "medium") -> Dict[str, Any]:
    """
    Generate a test payload with the given prompt and size
    
    Parameters:
    - prompt: The prompt to include
    - payload_size: The size of the payload ('small', 'medium', 'large')
    """
    current_time = int(datetime.now().timestamp())
    
    # Base payload
    payload = {
        "deviceId": f"benchmark_device_{random.randint(1000, 9999)}",
        "timestamp": current_time,
        "battery": {
            "level": random.uniform(10.0, 95.0),
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
            "lowMemory": random.choice([True, False]),
            "threshold": 512.0
        },
        "cpu": {
            "usage": random.uniform(10.0, 90.0),
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
    
    # Determine number of apps based on payload size
    num_apps = {
        "small": random.randint(2, 5),
        "medium": random.randint(5, 15),
        "large": random.randint(15, 30)
    }.get(payload_size, 5)
    
    # Generate apps
    for i in range(num_apps):
        app = {
            "packageName": f"com.benchmark.app{i}",
            "processName": f"com.benchmark.app{i}",
            "appName": f"Benchmark App {i}",
            "isSystemApp": random.random() < 0.2,
            "lastUsed": current_time - random.randint(0, 86400),
            "foregroundTime": random.uniform(300.0, 3600.0),
            "backgroundTime": random.uniform(600.0, 7200.0),
            "batteryUsage": random.uniform(0.1, 20.0),
            "dataUsage": {
                "foreground": random.uniform(0.1, 100.0),
                "background": random.uniform(0.1, 50.0),
                "rxBytes": random.uniform(1000.0, 100000.0),
                "txBytes": random.uniform(500.0, 50000.0)
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
    
    # Add prompt if provided
    if prompt is not None:
        payload["prompt"] = prompt
    
    return payload

def measure_response_time(url: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Make an API request and measure the response time
    
    Parameters:
    - url: The URL to request
    - payload: The payload to send
    - timeout: Request timeout in seconds
    
    Returns:
    - Dictionary with response time and status information
    """
    start_time = time.time()
    result = {
        "start_time": start_time,
        "response_time": None,
        "status_code": None,
        "success": False,
        "error": None
    }
    
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        end_time = time.time()
        result["response_time"] = end_time - start_time
        result["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["success"] = True
            if len(response.json().get("actionable", [])) > 0:
                result["has_actionable"] = True
            else:
                result["has_actionable"] = False
        else:
            result["error"] = response.text
    except requests.RequestException as e:
        end_time = time.time()
        result["response_time"] = end_time - start_time
        result["error"] = str(e)
    
    return result

def run_benchmark(prompt_type: str, num_requests: int, concurrent: bool, 
                  payload_size: str, timeout: int, test_endpoint: bool = False) -> List[Dict[str, Any]]:
    """
    Run a benchmark test
    
    Parameters:
    - prompt_type: Type of prompt to use
    - num_requests: Number of requests to make
    - concurrent: Whether to make requests concurrently
    - payload_size: Size of payload to use
    - timeout: Request timeout in seconds
    - test_endpoint: Whether to use test endpoints instead of analyze endpoint
    
    Returns:
    - List of result dictionaries
    """
    prompt = TEST_PROMPTS.get(prompt_type)
    prompt_desc = f"'{prompt}'" if prompt else "None"
    
    if test_endpoint:
        if prompt:
            url = f"{BASE_URL}/api/test/with-prompt/{prompt}"
        else:
            url = f"{BASE_URL}/api/test/no-prompt"
        method = "GET"
    else:
        url = f"{BASE_URL}/api/analyze"
        method = "POST"
    
    print(f"Running benchmark with:")
    print(f"  Prompt type: {prompt_type} ({prompt_desc})")
    print(f"  Endpoint: {url} ({method})")
    print(f"  Payload size: {payload_size}")
    print(f"  Requests: {num_requests}")
    print(f"  Concurrency: {'Enabled' if concurrent else 'Disabled'}")
    print(f"  Timeout: {timeout} seconds")
    print("Starting benchmark...")
    
    results = []
    
    if concurrent:
        # Generate payloads in advance
        payloads = [
            generate_test_payload(prompt, payload_size) for _ in range(num_requests)
        ]
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            if test_endpoint:
                # For test endpoints, we don't need payloads
                futures = [executor.submit(
                    lambda u: measure_response_time(u, {}, timeout),
                    url
                ) for _ in range(num_requests)]
            else:
                futures = [executor.submit(
                    measure_response_time,
                    url, payload, timeout
                ) for payload in payloads]
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  Request {i+1}/{num_requests} completed in {result['response_time']:.2f} seconds")
                except Exception as e:
                    results.append({
                        "start_time": time.time(),
                        "response_time": None,
                        "status_code": None,
                        "success": False,
                        "error": str(e)
                    })
                    print(f"  Request {i+1}/{num_requests} failed: {str(e)}")
    else:
        # Make sequential requests
        for i in range(num_requests):
            if test_endpoint:
                # For test endpoints, we don't need a payload
                result = measure_response_time(url, {}, timeout)
            else:
                payload = generate_test_payload(prompt, payload_size)
                result = measure_response_time(url, payload, timeout)
            
            results.append(result)
            print(f"  Request {i+1}/{num_requests} completed in {result['response_time']:.2f} seconds")
    
    return results

def print_benchmark_results(results: List[Dict[str, Any]]) -> None:
    """Print benchmark results"""
    success_results = [r for r in results if r["success"]]
    failed_results = [r for r in results if not r["success"]]
    
    success_times = [r["response_time"] for r in success_results]
    
    print("\nBenchmark Results:")
    print(f"  Total requests: {len(results)}")
    print(f"  Successful requests: {len(success_results)}")
    print(f"  Failed requests: {len(failed_results)}")
    
    if success_times:
        print(f"\nResponse Time Statistics (seconds):")
        print(f"  Min: {min(success_times):.2f}")
        print(f"  Max: {max(success_times):.2f}")
        print(f"  Mean: {statistics.mean(success_times):.2f}")
        print(f"  Median: {statistics.median(success_times):.2f}")
        try:
            print(f"  90th percentile: {statistics.quantiles(success_times, n=10)[-1]:.2f}")
            print(f"  95th percentile: {statistics.quantiles(success_times, n=20)[-1]:.2f}")
        except statistics.StatisticsError:
            # Not enough data points for percentiles
            pass
    
    if failed_results:
        print("\nError Details:")
        for i, result in enumerate(failed_results):
            print(f"  Error {i+1}: {result.get('error', 'Unknown error')}")

def main():
    parser = argparse.ArgumentParser(description="PowerGuard API Benchmark Tool")
    parser.add_argument("--prompt", choices=list(TEST_PROMPTS.keys()), default="none",
                       help="Type of prompt to use (default: none)")
    parser.add_argument("--requests", type=int, default=10,
                       help="Number of requests to make (default: 10)")
    parser.add_argument("--concurrent", action="store_true",
                       help="Make requests concurrently")
    parser.add_argument("--url", type=str, default=BASE_URL,
                       help="Base URL for the API")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="medium",
                       help="Size of payload (default: medium)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    parser.add_argument("--test", action="store_true",
                       help="Use test endpoints instead of analyze endpoint")
    
    args = parser.parse_args()
    
    # Use custom URL if provided
    api_url = args.url
    
    # Create a wrapper for run_benchmark to use custom URL
    def run_benchmark_with_url(prompt_type, num_requests, concurrent, payload_size, timeout, test_endpoint):
        """Wrapper for run_benchmark to use custom URL"""
        prompt = TEST_PROMPTS.get(prompt_type)
        prompt_desc = f"'{prompt}'" if prompt else "None"
        
        if test_endpoint:
            if prompt:
                url = f"{api_url}/api/test/with-prompt/{prompt}"
            else:
                url = f"{api_url}/api/test/no-prompt"
            method = "GET"
        else:
            url = f"{api_url}/api/analyze"
            method = "POST"
        
        print(f"Running benchmark with:")
        print(f"  Prompt type: {prompt_type} ({prompt_desc})")
        print(f"  Endpoint: {url} ({method})")
        print(f"  Payload size: {payload_size}")
        print(f"  Requests: {num_requests}")
        print(f"  Concurrency: {'Enabled' if concurrent else 'Disabled'}")
        print(f"  Timeout: {timeout} seconds")
        print("Starting benchmark...")
        
        results = []
        
        if concurrent:
            # Generate payloads in advance
            payloads = [
                generate_test_payload(prompt, payload_size) for _ in range(num_requests)
            ]
            
            # Make concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                if test_endpoint:
                    # For test endpoints, we don't need payloads
                    futures = [executor.submit(
                        lambda u: measure_response_time(u, {}, timeout),
                        url
                    ) for _ in range(num_requests)]
                else:
                    futures = [executor.submit(
                        measure_response_time,
                        url, payload, timeout
                    ) for payload in payloads]
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    try:
                        result = future.result()
                        results.append(result)
                        print(f"  Request {i+1}/{num_requests} completed in {result['response_time']:.2f} seconds")
                    except Exception as e:
                        results.append({
                            "start_time": time.time(),
                            "response_time": None,
                            "status_code": None,
                            "success": False,
                            "error": str(e)
                        })
                        print(f"  Request {i+1}/{num_requests} failed: {str(e)}")
        else:
            # Make sequential requests
            for i in range(num_requests):
                if test_endpoint:
                    # For test endpoints, we don't need a payload
                    result = measure_response_time(url, {}, timeout)
                else:
                    payload = generate_test_payload(prompt, payload_size)
                    result = measure_response_time(url, payload, timeout)
                
                results.append(result)
                print(f"  Request {i+1}/{num_requests} completed in {result['response_time']:.2f} seconds")
        
        return results
    
    # Run benchmark with the appropriate function
    run_benchmark_fn = run_benchmark_with_url if api_url != BASE_URL else run_benchmark
    
    # Run benchmark
    start_time = time.time()
    results = run_benchmark_fn(
        args.prompt, args.requests, args.concurrent, 
        args.size, args.timeout, args.test
    )
    total_time = time.time() - start_time
    
    # Print results
    print_benchmark_results(results)
    print(f"\nBenchmark completed in {total_time:.2f} seconds")

if __name__ == "__main__":
    main() 