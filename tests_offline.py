import json
import time
from typing import Dict, Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_device_data(prompt: str = "") -> Dict[str, Any]:
    now = int(time.time())
    return {
        "deviceId": "offline-device-1",
        "timestamp": now,
        "battery": {
            "level": 42.5,
            "temperature": 34.0,
            "voltage": 3.9,
            "isCharging": False,
            "chargingType": "none",
            "health": 2,
            "capacity": 4000.0,
            "currentNow": -350.0,
        },
        "memory": {
            "totalRam": 8192.0,
            "availableRam": 3200.0,
            "lowMemory": False,
            "threshold": 1024.0,
        },
        "cpu": {
            "usage": 37.0,
            "temperature": 45.0,
            "frequencies": [1.2, 1.8, 2.4],
        },
        "network": {
            "type": "wifi",
            "strength": 4.0,
            "isRoaming": False,
            "dataUsage": {
                "foreground": 120.5,
                "background": 45.2,
                "rxBytes": 50000000.0,
                "txBytes": 12000000.0,
            },
            "activeConnectionInfo": "wifi-5g",
            "linkSpeed": 433.0,
            "cellularGeneration": "5G",
        },
        "apps": [
            {
                "packageName": "com.example.app",
                "processName": "com.example.app",
                "appName": "Example",
                "isSystemApp": False,
                "lastUsed": now - 3600,
                "foregroundTime": 1800.0,
                "backgroundTime": 5400.0,
                "batteryUsage": 7.5,
                "dataUsage": {
                    "foreground": 40.0,
                    "background": 10.0,
                    "rxBytes": 15000000.0,
                    "txBytes": 4000000.0,
                },
                "memoryUsage": 250.0,
                "cpuUsage": 12.0,
                "notifications": 5,
                "crashes": 0,
                "versionName": "1.2.3",
                "versionCode": 123,
                "targetSdkVersion": 33,
                "installTime": now - 86400 * 30,
                "updatedTime": now - 86400,
            },
            {
                "packageName": "com.instagram",
                "processName": "com.instagram",
                "appName": "Instagram",
                "isSystemApp": False,
                "lastUsed": now - 1200,
                "foregroundTime": 2400.0,
                "backgroundTime": 1200.0,
                "batteryUsage": 12.5,
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
        ],
        "deviceInfo": {
            "manufacturer": "Google",
            "model": "Pixel 7",
            "osVersion": "Android 14",
            "sdkVersion": 34,
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
        # Print a compact preview
        preview = {}
        if isinstance(data, dict):
            for k in [
                "message",
                "status",
                "id",
                "success",
                "batteryScore",
                "dataScore",
                "performanceScore",
                "estimatedSavings",
            ]:
                if k in data:
                    preview[k] = data[k]
            # Special cases
            if "actionable" in data and isinstance(data["actionable"], list):
                preview["actionable_count"] = len(data["actionable"])
            if "insights" in data and isinstance(data["insights"], list):
                preview["insights_count"] = len(data["insights"])
            if "battery_values" in data:
                preview["battery_values_count"] = len(data["battery_values"])
        else:
            # Likely a list (e.g., /api/all-entries)
            preview = {"items": len(data)}
        print(json.dumps(preview, indent=2))
    except Exception:
        text = getattr(resp, "text", "")
        print(text[:500])


def main():
    # 1) Health check
    r = client.get("/")
    print_result("GET /", r)

    # 2) Reset DB
    r = client.post("/api/reset-db")
    print_result("POST /api/reset-db", r)

    # 3) Seed a pattern
    device_id = "offline-device-1"
    seed_payload = {
        "deviceId": device_id,
        "packageName": "com.example.app",
        "pattern": "Moderate battery usage",
        "timestamp": int(time.time()),
    }
    r = client.post("/api/test/seed-pattern", json=seed_payload)
    print_result("POST /api/test/seed-pattern", r)

    # 4) Fetch patterns for device
    r = client.get(f"/api/patterns/{device_id}")
    print_result(f"GET /api/patterns/{device_id}", r)

    # 5) All entries (may 500 due to field name mismatch)
    r = client.get("/api/all-entries")
    print_result("GET /api/all-entries", r)

    # 6) Test sample response without prompt
    r = client.get("/api/test/no-prompt")
    print_result("GET /api/test/no-prompt", r)

    # 7) Test sample response with prompt (rule-based path)
    r = client.get("/api/test/with-prompt/Save%20my%20battery")
    print_result("GET /api/test/with-prompt/{prompt}", r)

    # 8) Debug app values
    payload = make_device_data("")
    r = client.post("/api/debug/app-values", json=payload)
    print_result("POST /api/debug/app-values", r)

    # 9) Analyze with empty prompt (legacy/offline path)
    payload2 = make_device_data("")
    r = client.post("/api/analyze", json=payload2)
    print_result("POST /api/analyze (empty prompt)", r)


if __name__ == "__main__":
    main()
