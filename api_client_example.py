"""
PowerGuard API Client Example

This script demonstrates how to use the PowerGuard AI Backend API from your own code.
It provides examples of making API requests with and without prompts,
handling responses, and extracting useful information.
"""

import requests
import json
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('powerguard_client')

class PowerGuardClient:
    """Client for interacting with the PowerGuard AI Backend API"""
    
    def __init__(self, base_url: str = "https://powerguardbackend.onrender.com"):
        """
        Initialize the PowerGuard API client
        
        Parameters:
        - base_url: The base URL for the API
        """
        self.base_url = base_url
        self.session = requests.Session()
        
        # Verify that the API is running
        self._verify_api_available()
    
    def _verify_api_available(self) -> bool:
        """Verify that the API is available"""
        try:
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            
            if response.json().get("message") == "PowerGuard AI Backend is running":
                logger.info("Successfully connected to PowerGuard API")
                return True
            else:
                logger.warning("API responded with unexpected message")
                return False
        except requests.RequestException as e:
            logger.error(f"Failed to connect to PowerGuard API: {e}")
            return False
    
    def analyze_device_data(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze device data using the API
        
        Parameters:
        - device_data: Dictionary containing device data
        
        Returns:
        - Dictionary containing the analysis response
        """
        url = f"{self.base_url}/api/analyze"
        logger.info(f"Sending analysis request for device: {device_data.get('deviceId')}")
        
        try:
            response = self.session.post(url, json=device_data)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Analysis complete - received {len(result.get('actionable', []))} actionable items")
            return result
        except requests.RequestException as e:
            logger.error(f"Error analyzing device data: {e}")
            raise
    
    def get_device_patterns(self, device_id: str) -> Dict[str, str]:
        """
        Get usage patterns for a specific device
        
        Parameters:
        - device_id: The device ID to get patterns for
        
        Returns:
        - Dictionary of package names and patterns
        """
        url = f"{self.base_url}/api/patterns/{device_id}"
        logger.info(f"Retrieving usage patterns for device: {device_id}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Retrieved {len(result)} usage patterns")
            return result
        except requests.RequestException as e:
            logger.error(f"Error retrieving usage patterns: {e}")
            raise
    
    def test_with_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Test the API with a prompt using the test endpoint
        
        Parameters:
        - prompt: The prompt to test with
        
        Returns:
        - Dictionary containing the test response
        """
        url = f"{self.base_url}/api/test/with-prompt/{prompt}"
        logger.info(f"Testing API with prompt: {prompt}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Test complete - received {len(result.get('actionable', []))} actionable items")
            return result
        except requests.RequestException as e:
            logger.error(f"Error testing with prompt: {e}")
            raise
    
    def test_without_prompt(self) -> Dict[str, Any]:
        """
        Test the API without a prompt using the test endpoint
        
        Returns:
        - Dictionary containing the test response
        """
        url = f"{self.base_url}/api/test/no-prompt"
        logger.info("Testing API without prompt")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Test complete - received {len(result.get('actionable', []))} actionable items")
            return result
        except requests.RequestException as e:
            logger.error(f"Error testing without prompt: {e}")
            raise

def create_sample_device_data(device_id: str, prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a sample device data payload for testing
    
    Parameters:
    - device_id: The device ID to use
    - prompt: Optional prompt to include
    
    Returns:
    - Dictionary containing sample device data
    """
    current_time = int(datetime.now().timestamp())
    
    # Create a sample payload
    payload = {
        "deviceId": device_id,
        "timestamp": current_time,
        "battery": {
            "level": 25.5,
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
            "availableRam": 1024.0,
            "lowMemory": True,
            "threshold": 512.0
        },
        "cpu": {
            "usage": 75.0,
            "temperature": 45.5,
            "frequencies": [1800.0, 2100.0, 2400.0, 1900.0]
        },
        "network": {
            "type": "MOBILE",
            "strength": 65.0,
            "isRoaming": True,
            "dataUsage": {
                "foreground": 175.5,
                "background": 124.5,
                "rxBytes": 328000.0,
                "txBytes": 142000.0
            },
            "activeConnectionInfo": "Mobile-4G",
            "linkSpeed": 40.0,
            "cellularGeneration": "4G"
        },
        "apps": [
            {
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
            },
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
        ]
    }
    
    # Add prompt if provided
    if prompt is not None:
        payload["prompt"] = prompt
    
    return payload

def extract_actionable_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract actionable items from a response
    
    Parameters:
    - response: The API response
    
    Returns:
    - List of actionable items
    """
    return response.get("actionable", [])

def extract_insights(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract insights from a response
    
    Parameters:
    - response: The API response
    
    Returns:
    - List of insights
    """
    return response.get("insights", [])

def get_estimated_savings(response: Dict[str, Any]) -> Dict[str, float]:
    """
    Get estimated savings from a response
    
    Parameters:
    - response: The API response
    
    Returns:
    - Dictionary containing estimated savings
    """
    return response.get("estimatedSavings", {"batteryMinutes": 0.0, "dataMB": 0.0})

def print_optimization_summary(response: Dict[str, Any]) -> None:
    """
    Print a summary of optimization recommendations
    
    Parameters:
    - response: The API response
    """
    print("\nOptimization Summary")
    print("=" * 50)
    print(f"Message: {response.get('message')}")
    print(f"Time: {datetime.fromtimestamp(response.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print scores
    print("\nScores:")
    print(f"  Battery: {response.get('batteryScore'):.1f}/100")
    print(f"  Data: {response.get('dataScore'):.1f}/100")
    print(f"  Performance: {response.get('performanceScore'):.1f}/100")
    
    # Print estimated savings
    savings = response.get("estimatedSavings", {})
    print("\nEstimated Savings:")
    print(f"  Battery: {savings.get('batteryMinutes', 0):.1f} minutes")
    print(f"  Data: {savings.get('dataMB', 0):.1f} MB")
    
    # Print actionable items
    actionable = response.get("actionable", [])
    print(f"\nActionable Items ({len(actionable)}):")
    for i, action in enumerate(actionable):
        print(f"  {i+1}. {action.get('description')}")
        print(f"     App: {action.get('packageName')}")
        print(f"     Type: {action.get('type')}")
        print(f"     Reason: {action.get('reason')}")
    
    # Print insights
    insights = response.get("insights", [])
    print(f"\nInsights ({len(insights)}):")
    for i, insight in enumerate(insights):
        print(f"  {i+1}. {insight.get('title')}")
        print(f"     Type: {insight.get('type')}")
        print(f"     Severity: {insight.get('severity')}")
        if "description" in insight:
            print(f"     Details: {insight.get('description')}")

def main():
    # Initialize the client
    client = PowerGuardClient()
    
    # Example 1: Use the test endpoint without a prompt
    print("\n=== Example 1: Test Endpoint (No Prompt) ===")
    response_no_prompt = client.test_without_prompt()
    print_optimization_summary(response_no_prompt)
    
    # Example 2: Use the test endpoint with a battery optimization prompt
    print("\n=== Example 2: Test Endpoint (Battery Prompt) ===")
    response_battery = client.test_with_prompt("Optimize my battery life")
    print_optimization_summary(response_battery)
    
    # Example 3: Use the test endpoint with a data optimization prompt
    print("\n=== Example 3: Test Endpoint (Data Prompt) ===")
    response_data = client.test_with_prompt("Save my network data")
    print_optimization_summary(response_data)
    
    # Example 4: Analyze device data with the real endpoint
    print("\n=== Example 4: Real Analysis Endpoint ===")
    device_data = create_sample_device_data("example_device_001", "Optimize both battery and data")
    
    try:
        response_analyze = client.analyze_device_data(device_data)
        print_optimization_summary(response_analyze)
    except requests.RequestException as e:
        print(f"Failed to analyze device data: {e}")
        print("Using test endpoint as fallback...")
        response_analyze = client.test_with_prompt("Optimize both battery and data")
        print_optimization_summary(response_analyze)
    
    # Example 5: Get device patterns
    print("\n=== Example 5: Get Device Patterns ===")
    try:
        patterns = client.get_device_patterns("example_device_001")
        print(f"Found {len(patterns)} patterns for device")
        for package, pattern in patterns.items():
            print(f"  {package}: {pattern}")
    except requests.RequestException as e:
        print(f"Failed to get device patterns: {e}")

if __name__ == "__main__":
    main() 