import subprocess
import json
import os
import time

# List of test prompts covering different scenarios
TEST_PROMPTS = [
    # Battery optimization prompts
    "My battery is at 5% and I need it to last for 2 more hours",
    "Save my battery, it's critically low",
    "I'm traveling for 3 hours with 15% battery left",
    "Optimize battery but keep WhatsApp working",
    
    # Data optimization prompts
    "I only have 50MB data left until tomorrow",
    "How can I reduce my data usage?",
    "Save data but ensure my email still works",
    "Traveling abroad with limited data plan",
    
    # Information requests
    "Which apps are draining my battery?",
    "What's using all my data?",
    "Show me my battery usage for the past day",
    
    # Complex/combined prompts
    "Low battery and almost out of data, help!",
    "Need Maps and WhatsApp for 4 hours but battery at 20%",
    "Can I stream Netflix for 2 hours with 30% battery?",
    "I need to make an important call in 1 hour but battery is at 10%"
]

# Function to run a test and return the results
def run_test(prompt):
    encoded_prompt = prompt.replace(' ', '%20')
    curl_command = f'curl -X GET "http://localhost:8000/api/test/with-prompt/{encoded_prompt}"'
    
    # Execute the curl command and capture output
    result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
    
    try:
        # Parse the JSON response
        response_data = json.loads(result.stdout)
        return {
            "prompt": prompt,
            "curl_command": curl_command,
            "response": response_data,
            "actionables": response_data.get("actionable", []),
            "insights": response_data.get("insights", []),
            "estimated_savings": response_data.get("estimatedSavings", {})
        }
    except json.JSONDecodeError:
        return {
            "prompt": prompt,
            "curl_command": curl_command,
            "error": "Failed to parse JSON response",
            "raw_response": result.stdout
        }

# Function to format results for output
def format_result(result):
    output = []
    output.append("=" * 80)
    output.append(f"PROMPT: \"{result['prompt']}\"")
    output.append("-" * 80)
    output.append(f"CURL COMMAND: {result['curl_command']}")
    output.append("-" * 80)
    
    if "error" in result:
        output.append(f"ERROR: {result['error']}")
        output.append(f"RAW RESPONSE: {result['raw_response']}")
        return "\n".join(output)
    
    # Format actionables
    output.append("ACTIONABLES:")
    if result["actionables"]:
        for a in result["actionables"]:
            output.append(f"  - Type: {a.get('type')}")
            output.append(f"    Package: {a.get('packageName')}")
            output.append(f"    Description: {a.get('description')}")
            output.append(f"    Mode: {a.get('newMode')}")
            output.append("")
    else:
        output.append("  No actionables generated")
    
    # Format insights
    output.append("INSIGHTS:")
    if result["insights"]:
        for i in result["insights"]:
            output.append(f"  - Title: {i.get('title')}")
            output.append(f"    Description: {i.get('description')}")
            output.append(f"    Severity: {i.get('severity', 'N/A')}")
            output.append("")
    else:
        output.append("  No insights generated")
    
    # Format savings
    savings = result["estimated_savings"]
    output.append("ESTIMATED SAVINGS:")
    output.append(f"  Battery: {savings.get('batteryMinutes', 0)} minutes")
    output.append(f"  Data: {savings.get('dataMB', 0)} MB")
    
    # Include the raw JSON for reference
    output.append("-" * 80)
    output.append("RAW JSON RESPONSE:")
    output.append(json.dumps(result["response"], indent=2))
    
    return "\n".join(output)

# Main function to run all tests and save results
def run_all_tests():
    print(f"Running tests for {len(TEST_PROMPTS)} prompts...")
    results = []
    
    # Run each test
    for prompt in TEST_PROMPTS:
        print(f"Testing prompt: \"{prompt}\"")
        result = run_test(prompt)
        results.append(result)
        time.sleep(1)  # Small delay to prevent overwhelming the server
    
    # Format and save all results
    output = []
    output.append("POWERGUARD AI BACKEND - TEST RESULTS")
    output.append("=" * 80)
    output.append(f"Total prompts tested: {len(results)}")
    output.append("")
    
    # Add a summary table
    output.append("SUMMARY TABLE:")
    output.append("-" * 80)
    output.append(f"{'PROMPT':<50} | {'ACTIONABLES':<12} | {'INSIGHTS':<10} | {'BATTERY SAVED':<15} | {'DATA SAVED':<10}")
    output.append("-" * 80)
    
    for r in results:
        if "error" in r:
            continue
        
        num_actionables = len(r["actionables"])
        num_insights = len(r["insights"])
        battery_saved = r["estimated_savings"].get("batteryMinutes", 0)
        data_saved = r["estimated_savings"].get("dataMB", 0)
        
        truncated_prompt = r["prompt"][:47] + "..." if len(r["prompt"]) > 50 else r["prompt"].ljust(50)
        output.append(f"{truncated_prompt} | {num_actionables:<12} | {num_insights:<10} | {battery_saved:<15} | {data_saved:<10}")
    
    output.append("")
    
    # Add detailed results for each prompt
    for r in results:
        output.append(format_result(r))
        output.append("")
    
    # Save to file
    with open("test_results.txt", "w") as f:
        f.write("\n".join(output))
    
    print(f"All test results saved to test_results.txt")

if __name__ == "__main__":
    run_all_tests() 