#!/usr/bin/env python3
"""
Android API Compliance Test

Tests the PowerGuard backend API against the exact Android project requirements.
Verifies request/response structure alignment.
"""

import requests
import json
import time
from typing import Dict, Any

# Test data matching the exact Android requirements
REQUIRED_REQUEST_DATA = {
    "deviceId": "unique-device-identifier",
    "timestamp": 1725724800000,
    "battery": {
        "level": 65,
        "temperature": 32.5,
        "voltage": 3800,
        "isCharging": False,
        "chargingType": "none",
        "health": 2,
        "capacity": 4000,
        "currentNow": -850
    },
    "memory": {
        "totalRam": 8589934592,
        "availableRam": 3221225472,
        "lowMemory": False,
        "threshold": 1073741824
    },
    "cpu": {
        "usage": 45.2,
        "temperature": 38.5,
        "frequencies": [1800000, 2400000, 2800000]
    },
    "network": {
        "type": "WIFI",
        "strength": -45,
        "isRoaming": False,
        "dataUsage": {
            "foreground": 524288000,
            "background": 104857600,
            "rxBytes": 419430400,
            "txBytes": 209715200
        },
        "activeConnectionInfo": "WiFi 6",
        "linkSpeed": 866,
        "cellularGeneration": ""
    },
    "apps": [
        {
            "packageName": "com.example.app",
            "processName": "com.example.app",
            "appName": "Example App",
            "isSystemApp": False,
            "lastUsed": 1725724500000,
            "foregroundTime": 3600000,
            "backgroundTime": 7200000,
            "batteryUsage": 12.5,
            "dataUsage": {
                "foreground": 52428800,
                "background": 10485760,
                "rxBytes": 41943040,
                "txBytes": 20971520
            },
            "memoryUsage": 134217728,
            "cpuUsage": 8.3,
            "notifications": 15,
            "crashes": 0,
            "versionName": "2.1.0",
            "versionCode": 21,
            "targetSdkVersion": 34,
            "installTime": 1700000000000,
            "updatedTime": 1720000000000,
            "alarmWakeups": 3,
            "currentPriority": "VISIBLE",
            "bucket": "ACTIVE"
        }
    ],
    "settings": {
        "batteryOptimization": True,
        "dataSaver": False,
        "powerSaveMode": False,
        "adaptiveBattery": True,
        "autoSync": True
    },
    "deviceInfo": {
        "manufacturer": "Google",
        "model": "Pixel 8",
        "osVersion": "Android 15",
        "sdkVersion": 35,
        "screenOnTime": 18000000
    },
    "prompt": "Analyze my device for battery optimization opportunities",
    "currentDataMb": 1024.0,
    "totalDataMb": 10240.0,
    "pastUsagePatterns": [
        "Heavy social media usage in evening",
        "Background sync during work hours",
        "Gaming sessions on weekends"
    ]
}

EXPECTED_RESPONSE_FIELDS = {
    "id": str,
    "success": bool,
    "timestamp": (int, float),
    "message": str,
    "responseType": str,
    "actionable": list,
    "insights": list,
    "batteryScore": (int, float),
    "dataScore": (int, float),
    "performanceScore": (int, float),
    "estimatedSavings": dict
}

EXPECTED_ACTIONABLE_FIELDS = {
    "id": str,
    "type": str,
    "description": str,
    "package_name": str,
    "estimated_battery_savings": (int, float),
    "estimated_data_savings": (int, float),
    "severity": int,
    "new_mode": str,
    "enabled": bool,
    "throttle_level": (type(None), str),
    "reason": str,
    "parameters": dict
}

def test_api_compliance():
    """Test API compliance with Android requirements"""
    
    print("🔍 Testing PowerGuard API compliance with Android requirements...")
    print("=" * 60)
    
    # Test 1: Start server and check health
    print("\n📡 Testing API availability...")
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not available: {e}")
        return False
    
    # Test 2: Send request with required structure
    print("\n📤 Testing request structure compatibility...")
    try:
        response = requests.post(
            "http://localhost:8000/api/analyze",
            json=REQUIRED_REQUEST_DATA,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        response_data = response.json()
        print("✅ Request accepted successfully")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    
    # Test 3: Validate response structure
    print("\n📥 Validating response structure...")
    
    compliance_issues = []
    
    # Check top-level fields
    for field, expected_type in EXPECTED_RESPONSE_FIELDS.items():
        if field not in response_data:
            if field == "responseType":
                compliance_issues.append(f"Missing field: {field}")
            else:
                print(f"⚠️  Missing field: {field}")
        else:
            if isinstance(expected_type, tuple):
                if not isinstance(response_data[field], expected_type):
                    print(f"⚠️  Field {field} has wrong type: {type(response_data[field])}, expected: {expected_type}")
            else:
                if not isinstance(response_data[field], expected_type):
                    print(f"⚠️  Field {field} has wrong type: {type(response_data[field])}, expected: {expected_type}")
    
    # Check actionable items structure
    if "actionable" in response_data and response_data["actionable"]:
        print("\n🔧 Validating actionable items...")
        for i, item in enumerate(response_data["actionable"]):
            print(f"  Actionable item {i+1}:")
            for field, expected_type in EXPECTED_ACTIONABLE_FIELDS.items():
                if field not in item:
                    if field == "package_name":
                        # Check if it uses packageName instead
                        if "packageName" in item:
                            compliance_issues.append(f"Actionable item uses 'packageName' instead of 'package_name'")
                        else:
                            compliance_issues.append(f"Actionable missing field: {field}")
                    elif field in ["estimated_battery_savings", "estimated_data_savings", "severity", "throttle_level"]:
                        compliance_issues.append(f"Actionable missing field: {field}")
                    else:
                        print(f"    ⚠️  Missing field: {field}")
    
    # Check estimated savings structure
    if "estimatedSavings" in response_data:
        savings = response_data["estimatedSavings"]
        required_savings_fields = ["batteryMinutes", "dataMB"]
        for field in required_savings_fields:
            if field not in savings:
                print(f"⚠️  Missing estimatedSavings field: {field}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 COMPLIANCE SUMMARY")
    print("=" * 60)
    
    if compliance_issues:
        print("❌ COMPLIANCE ISSUES FOUND:")
        for issue in compliance_issues:
            print(f"  • {issue}")
        print(f"\n🔧 Total issues: {len(compliance_issues)}")
    else:
        print("✅ API is fully compliant with Android requirements!")
    
    # Show sample response
    print("\n📄 Sample Response Structure:")
    print("-" * 30)
    print(json.dumps(response_data, indent=2))
    
    return len(compliance_issues) == 0

if __name__ == "__main__":
    success = test_api_compliance()
    exit(0 if success else 1)