import argparse
import json
from app.prompt_analyzer import classify_with_llm
from app.utils.strategy_analyzer import determine_strategy
from app.utils.insight_generator import generate_insights
from app.utils.actionable_generator import generate_actionables
from datetime import datetime

def run_test(prompt: str) -> dict:
    """Run a test with the given prompt using direct function calls"""
    print(f"\nTesting prompt: '{prompt}'\n")
    
    # Create sample device data
    device_data = {
        "deviceId": "test-device-001",
        "timestamp": int(datetime.now().timestamp()),
        "battery": {
            "level": 45.0,
            "health": 95.0,
            "temperature": 35.0
        },
        "memory": {
            "total": 8000000000,
            "used": 4000000000,
            "free": 4000000000
        },
        "cpu": {
            "usage": 45.0,
            "temperature": 45.0
        },
        "network": {
            "dataUsed": 100.5,
            "wifiEnabled": True,
            "mobileDataEnabled": False
        },
        "apps": [
            {
                "packageName": "com.whatsapp",
                "batteryUsage": 5.2,
                "dataUsage": 20.1,
                "foregroundTime": 10
            },
            {
                "packageName": "com.google.android.apps.maps",
                "batteryUsage": 18.5,
                "dataUsage": 35.7,
                "foregroundTime": 30
            },
            {
                "packageName": "com.instagram",
                "batteryUsage": 15.4,
                "dataUsage": 45.3,
                "foregroundTime": 25
            }
        ],
        "prompt": prompt
    }
    
    # Analyze prompt
    print("Analyzing prompt...")
    prompt_analysis = classify_with_llm(prompt)
    print(f"Prompt analysis: {json.dumps(prompt_analysis, indent=2)}\n")
    
    # Get strategy
    print("Determining strategy...")
    strategy = determine_strategy(device_data, prompt)
    print(f"Strategy: {json.dumps(strategy, indent=2)}\n")
    
    # Generate insights and actionables
    print("Generating insights and actionables...")
    insights = generate_insights(strategy, device_data, False, prompt)
    actionables = generate_actionables(strategy, device_data)
    
    # Create response
    response = {
        "id": f"test_{int(datetime.now().timestamp())}",
        "success": True,
        "timestamp": int(datetime.now().timestamp()),
        "message": "Test response generated successfully",
        "actionable": actionables,
        "insights": insights,
        "batteryScore": 60.0,
        "dataScore": 80.0,
        "performanceScore": 70.0,
        "estimatedSavings": {
            "batteryMinutes": 30.0,
            "dataMB": 20.0
        }
    }
    
    print(f"Generated response with {len(response['actionable'])} actionable items and {len(response['insights'])} insights\n")
    print("Response:")
    print(json.dumps(response, indent=2))
    return response

def main():
    parser = argparse.ArgumentParser(description='Test PowerGuard with a prompt')
    parser.add_argument('--prompt', type=str, required=True, help='The prompt to test')
    args = parser.parse_args()
    
    run_test(args.prompt)

if __name__ == '__main__':
    main() 