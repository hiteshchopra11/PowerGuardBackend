import os
import json
import time
from typing import Dict, Any

# Load Groq API key from environment variables
# Make sure GROQ_API_KEY is set in your environment or .env file
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY environment variable is required for testing")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_device_data(device_id: str, prompt: str) -> Dict[str, Any]:
    now = int(time.time())
    return {
        "deviceId": device_id,
        "timestamp": now,
        "battery": {
            "level": 25.0 if "3 hours" in prompt else 65.0,
            "temperature": 32.0,
            "voltage": 3.9,
            "isCharging": False,
            "chargingType": "none",
            "health": 2,
            "capacity": 4000.0,
            "currentNow": -350.0,
        },
        "memory": {
            "totalRam": 8192.0,
            "availableRam": 3500.0,
            "lowMemory": False,
            "threshold": 1024.0,
        },
        "cpu": {
            "usage": 37.0,
            "temperature": 45.0,
            "frequencies": [1.2, 1.8, 2.4],
        },
        "network": {
            "type": "cellular" if "data" in prompt.lower() else "wifi",
            "strength": 3.0,
            "isRoaming": False,
            "dataUsage": {
                "foreground": 150.0,
                "background": 75.0,
                "rxBytes": 50000000.0,
                "txBytes": 12000000.0,
            },
            "activeConnectionInfo": "lte",
            "linkSpeed": 100.0,
            "cellularGeneration": "5G",
        },
        "apps": [
            {
                "packageName": "com.instagram",
                "processName": "com.instagram",
                "appName": "Instagram",
                "isSystemApp": False,
                "lastUsed": now - 1200,
                "foregroundTime": 2400.0,
                "backgroundTime": 1200.0,
                "batteryUsage": 18.5 if "3 hours" in prompt else 12.0,
                "dataUsage": {
                    "foreground": 60.0,
                    "background": 20.0,
                    "rxBytes": 25000000.0,
                    "txBytes": 6000000.0,
                },
                "memoryUsage": 320.0,
                "cpuUsage": 18.0,
                "notifications": 8,
                "crashes": 0,
                "versionName": "321.0",
                "versionCode": 321000000,
                "targetSdkVersion": 34,
                "installTime": now - 86400 * 200,
                "updatedTime": now - 3600,
            },
            {
                "packageName": "com.google.android.youtube",
                "processName": "com.google.android.youtube",
                "appName": "YouTube",
                "isSystemApp": False,
                "lastUsed": now - 2400,
                "foregroundTime": 5400.0,
                "backgroundTime": 300.0,
                "batteryUsage": 22.1,
                "dataUsage": {
                    "foreground": 124.7,
                    "background": 2.1,
                    "rxBytes": 45000000.0,
                    "txBytes": 5000000.0,
                },
                "memoryUsage": 450.0,
                "cpuUsage": 25.0,
                "notifications": 2,
                "crashes": 0,
                "versionName": "19.25",
                "versionCode": 192500000,
                "targetSdkVersion": 34,
                "installTime": now - 86400 * 500,
                "updatedTime": now - 7200,
            },
            {
                "packageName": "com.whatsapp",
                "processName": "com.whatsapp",
                "appName": "WhatsApp",
                "isSystemApp": False,
                "lastUsed": now - 600,
                "foregroundTime": 1800.0,
                "backgroundTime": 3600.0,
                "batteryUsage": 8.7,
                "dataUsage": {
                    "foreground": 15.6,
                    "background": 8.2,
                    "rxBytes": 10000000.0,
                    "txBytes": 2000000.0,
                },
                "memoryUsage": 180.0,
                "cpuUsage": 10.0,
                "notifications": 15,
                "crashes": 0,
                "versionName": "2.24",
                "versionCode": 224000000,
                "targetSdkVersion": 34,
                "installTime": now - 86400 * 800,
                "updatedTime": now - 3600,
            },
        ],
        "deviceInfo": {
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "osVersion": "Android 13",
            "sdkVersion": 33,
            "screenOnTime": 7200,
        },
        "settings": {
            "powerSaveMode": False,
            "dataSaver": True,
            "batteryOptimization": True,
            "adaptiveBattery": True,
            "autoSync": True,
        },
        "prompt": prompt,
    }


def print_result(title: str, resp):
    print(f"\n=== {title} ===")
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        preview = {}
        if isinstance(data, dict):
            for k in [
                "message",
                "id",
                "success",
                "batteryScore",
                "dataScore",
                "performanceScore",
                "estimatedSavings",
            ]:
                if k in data:
                    preview[k] = data[k]
            if "actionable" in data and isinstance(data["actionable"], list):
                preview["actionable_count"] = len(data["actionable"])
            if "insights" in data and isinstance(data["insights"], list):
                preview["insights_count"] = len(data["insights"])
        else:
            preview = {"items": len(data)}
        print(json.dumps(preview, indent=2))
    except Exception:
        text = getattr(resp, "text", "")
        print(text[:800])


def main():
    device_id = "groq-device-1"

    # 1) Reset DB
    r = client.post("/api/reset-db")
    print_result("POST /api/reset-db", r)

    # 2) Analyze - Optimization prompt (should store a pattern)
    prompt1 = "Save my battery for the next 3 hours"
    r = client.post("/api/analyze", json=make_device_data(device_id, prompt1))
    print_result("POST /api/analyze (optimization)", r)

    # 3) Analyze - Information prompt
    prompt2 = "Which apps use the most battery?"
    r = client.post("/api/analyze", json=make_device_data(device_id, prompt2))
    print_result("POST /api/analyze (information)", r)

    # 4) Analyze - Data constraint prompt
    prompt3 = "I only have 500MB data left"
    r = client.post("/api/analyze", json=make_device_data(device_id, prompt3))
    print_result("POST /api/analyze (data constraint)", r)

    # 5) Verify patterns for device
    r = client.get(f"/api/patterns/{device_id}")
    print_result(f"GET /api/patterns/{device_id}", r)

    # 6) Verify all entries
    r = client.get("/api/all-entries")
    print_result("GET /api/all-entries", r)


if __name__ == "__main__":
    main()
