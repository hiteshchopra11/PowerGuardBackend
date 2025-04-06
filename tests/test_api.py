from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "PowerGuard AI Backend is running"}

def test_device_data_validation():
    current_time = int(datetime.now().timestamp())
    
    # Base test data
    base_test_data = {
        "deviceId": "test_device_001",
        "timestamp": current_time,
        "battery": {
            "level": 75.5,
            "temperature": 38.2,
            "voltage": 4200.0,
            "isCharging": False,
            "chargingType": "None",
            "health": 95,
            "capacity": 4000.0,
            "currentNow": 450.0
        },
        "memory": {
            "totalRam": 8192.0,
            "availableRam": 2048.0,
            "lowMemory": False,
            "threshold": 512.0
        },
        "cpu": {
            "usage": 35.0,
            "temperature": 40.5,
            "frequencies": [1800.0, 2100.0, 2400.0, 1900.0]
        },
        "network": {
            "type": "WIFI",
            "strength": 85.0,
            "isRoaming": False,
            "dataUsage": {
                "foreground": 75.5,
                "background": 24.5,
                "rxBytes": 128000.0,
                "txBytes": 42000.0
            },
            "activeConnectionInfo": "WiFi-Home",
            "linkSpeed": 120.0,
            "cellularGeneration": "None"
        },
        "apps": [
            {
                "packageName": "com.example.app1",
                "processName": "com.example.app1",
                "appName": "Example App 1",
                "isSystemApp": False,
                "lastUsed": current_time - 300,
                "foregroundTime": 1800.0,
                "backgroundTime": 900.0,
                "batteryUsage": 5.5,
                "dataUsage": {
                    "foreground": 25.5,
                    "background": 4.5,
                    "rxBytes": 28000.0,
                    "txBytes": 12000.0
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
        ]
    }
    
    # Test 1: Without prompt field
    response = client.post("/api/analyze", json=base_test_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "success" in response.json()
    
    # Test 2: With battery optimization prompt
    battery_test_data = base_test_data.copy()
    battery_test_data["prompt"] = "Optimize battery life"
    
    response = client.post("/api/analyze", json=battery_test_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "success" in response.json()
    
    # Test 3: With data optimization prompt
    data_test_data = base_test_data.copy()
    data_test_data["prompt"] = "Save network data"
    
    response = client.post("/api/analyze", json=data_test_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "success" in response.json()
    
    # Test 4: With both optimizations prompt
    combined_test_data = base_test_data.copy() 
    combined_test_data["prompt"] = "Optimize both battery and network data"
    
    response = client.post("/api/analyze", json=combined_test_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "success" in response.json()
    
    # Test 5: With irrelevant prompt
    irrelevant_test_data = base_test_data.copy()
    irrelevant_test_data["prompt"] = "What's the weather like today?"
    
    response = client.post("/api/analyze", json=irrelevant_test_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "success" in response.json() 