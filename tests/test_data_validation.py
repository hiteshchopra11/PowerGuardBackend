import pytest
from app.llm_service import calculate_performance_score, format_apps
from app.prompt_analyzer import format_apps_for_prompt
from app.models import DeviceData

# Test data with missing/null values and sentinel values
test_data = {
    "deviceId": "test-device-001",
    "timestamp": 1717968563,
    "battery": {
        "level": 91,
        "temperature": 31.9,
        "voltage": 4391,
        "isCharging": False,
        "chargingType": "none",
        "health": 2,
        "capacity": 4410,
        "currentNow": -321
    },
    "memory": {
        "totalRam": 5849210880,
        "availableRam": 1589620736,
        "lowMemory": False,
        "threshold": 500000000
    },
    "cpu": {
        # Missing usage value should be handled
        "temperature": -1,  # Sentinel value
        "frequencies": []
    },
    "network": {
        "type": "wifi",
        "strength": -1,  # Sentinel value 
        "isRoaming": False,
        "dataUsage": {
            "foreground": 1200,
            "background": 1500,
            "rxBytes": 15000,
            "txBytes": 5000
        },
        "activeConnectionInfo": "WIFI",
        "linkSpeed": 65,
        "cellularGeneration": "4G"
    },
    "apps": [
        {
            "packageName": "com.example.app1",
            "processName": "com.example.app1",
            "appName": "Example App 1",
            "isSystemApp": False,
            "lastUsed": 1717968500,
            "foregroundTime": 3600,
            "backgroundTime": 1800,
            "batteryUsage": None,  # Missing value
            "dataUsage": {
                "foreground": 500,
                "background": 100,
                "rxBytes": 4000,
                "txBytes": 1000
            },
            "memoryUsage": 128000000,
            "cpuUsage": 12.5,
            "notifications": 5,
            "crashes": 0,
            "versionName": "1.0.0",
            "versionCode": 100,
            "targetSdkVersion": 33,
            "installTime": 1715376563,
            "updatedTime": 1715376563
        },
        {
            "packageName": "com.example.app2",
            "processName": "com.example.app2",
            "appName": "Example App 2",
            "isSystemApp": False,
            "lastUsed": 1717968400,
            "foregroundTime": 1800,
            "backgroundTime": 3600,
            "batteryUsage": -1,  # Sentinel value
            "dataUsage": {
                "foreground": 300,
                "background": 700,
                "rxBytes": 3000,
                "txBytes": 2000
            },
            "memoryUsage": -1,  # Sentinel value
            "cpuUsage": -1,     # Sentinel value
            "notifications": 10,
            "crashes": 1,
            "versionName": "2.0.0",
            "versionCode": 200,
            "targetSdkVersion": 33,
            "installTime": 1715386563,
            "updatedTime": 1715386563
        },
        {
            "packageName": "com.example.app3",
            "processName": "com.example.app3", 
            "appName": "Example App 3",
            "isSystemApp": True,
            "lastUsed": 1717968300,
            "foregroundTime": 900,
            "backgroundTime": 7200,
            # batteryUsage completely missing
            "dataUsage": {
                "foreground": 100,
                "background": 1200,
                "rxBytes": 0,
                "txBytes": 0
            },
            # memoryUsage completely missing
            # cpuUsage completely missing
            "notifications": 2,
            "crashes": 0,
            "versionName": "1.5.0",
            "versionCode": 150,
            "targetSdkVersion": 33,
            "installTime": 1715396563,
            "updatedTime": 1715396563
        }
    ],
    "prompt": "Optimize my battery"
}

# Real-world Android data test case with missing fields
android_test_data = {
    "deviceId": "android-test-device",
    "timestamp": 1717968563,
    "battery": {
        "level": 85,
        "temperature": 35.0,
        "voltage": 4200,
        "isCharging": False,
        "chargingType": "none",
        "health": 2,
        "capacity": 4000,
        "currentNow": -200
    },
    "memory": {
        "totalRam": 6000000000,
        "availableRam": 2000000000,
        "lowMemory": False,
        "threshold": 500000000
    },
    "cpu": {
        # usage missing completely in the JSON
        "temperature": 38.5,
        "frequencies": [1800000, 2000000]
    },
    "network": {
        "type": "cellular",
        "strength": 80,
        "isRoaming": False,
        "dataUsage": {
            "foreground": 5000,
            "background": 2000,
            "rxBytes": 12000,
            "txBytes": 3000
        },
        "activeConnectionInfo": "LTE",
        "linkSpeed": 50,
        "cellularGeneration": "4G"
    },
    "apps": [
        # App with batteryUsage field missing completely
        {
            "packageName": "com.android.chrome",
            "processName": "com.android.chrome",
            "appName": "Chrome",
            "isSystemApp": False,
            "lastUsed": 1717968400,
            "foregroundTime": 5400,
            "backgroundTime": 1200,
            # batteryUsage field missing completely
            "dataUsage": {
                "foreground": 3000,
                "background": 500,
                "rxBytes": 8000,
                "txBytes": 2000
            },
            "memoryUsage": 250000000,
            "cpuUsage": 15.2,
            "notifications": 8,
            "crashes": 0,
            "versionName": "94.0.4606.85",
            "versionCode": 460608500,
            "targetSdkVersion": 30,
            "installTime": 1700000000,
            "updatedTime": 1715000000
        }
    ],
    "prompt": "Check my battery drain"
}

def test_performance_score_with_none_values():
    """Test that performance score calculation handles None/missing values properly"""
    score = calculate_performance_score(test_data)
    assert score >= 0
    assert score <= 100
    
    # Test with Android format data (missing CPU usage)
    android_score = calculate_performance_score(android_test_data)
    assert android_score >= 0
    assert android_score <= 100

def test_format_apps_with_none_values():
    """Test that app formatting handles None/missing values properly"""
    formatted = format_apps_for_prompt(test_data['apps'])
    # Check that we got a string back
    assert isinstance(formatted, str)
    # Should contain the app names
    assert "Example App 1" in formatted
    assert "Example App 2" in formatted
    assert "Example App 3" in formatted
    
    # Test with Android format data
    android_formatted = format_apps_for_prompt(android_test_data['apps'])
    assert isinstance(android_formatted, str)
    assert "Chrome" in android_formatted

def test_llm_service_format_apps_with_none_values():
    """Test that llm_service.format_apps handles None/missing values properly"""
    formatted = format_apps(test_data['apps'])
    # Check that we got a string back
    assert isinstance(formatted, str)
    # Should contain the app names
    assert "Example App 1" in formatted
    assert "Example App 2" in formatted
    assert "Example App 3" in formatted
    
    # Test with Android format data
    android_formatted = format_apps(android_test_data['apps'])
    assert isinstance(android_formatted, str)
    assert "Chrome" in android_formatted

def test_device_data_validation_with_none_values():
    """Test that the Pydantic model validation handles None/sentinel values properly"""
    device_data = DeviceData.model_validate(test_data)
    assert device_data is not None
    assert len(device_data.apps) > 0
    
    # Check that sentinels were converted to None
    for app in device_data.apps:
        if app.packageName == "com.example.app2":
            assert app.batteryUsage is None
            assert app.memoryUsage is None
            assert app.cpuUsage is None
    
    # Test with Android format data
    android_device_data = DeviceData.model_validate(android_test_data)
    assert android_device_data is not None
    assert len(android_device_data.apps) > 0
    
    # Check that missing cpu.usage was properly handled
    assert android_device_data.cpu.usage is None
    
def test_none_comparison_prevention():
    """Test specific None > int comparison prevention patterns"""
    
    def potential_error_function(value):
        # This would fail if we don't check for None
        if value is not None and value > 50:
            return "High value"
        else:
            return "Low or No value"
    
    # Test with None value + default
    none_value = None
    none_with_default = {"key": none_value}.get("key", 0)
    result1 = potential_error_function(none_with_default)
    assert result1 == "Low or No value"
    
    # Test with sentinel value (-1) conversion
    sentinel_value = -1
    sentinel_converted = None if sentinel_value == -1 else sentinel_value
    sentinel_with_default = 0 if sentinel_converted is None else sentinel_converted
    result2 = potential_error_function(sentinel_with_default)
    assert result2 == "Low or No value"
    
    # Test with or-operator pattern
    none_with_or = none_value or 0
    result3 = potential_error_function(none_with_or)
    assert result3 == "Low or No value"
    
    # Test with a value that should pass the comparison
    result4 = potential_error_function(75)
    assert result4 == "High value" 