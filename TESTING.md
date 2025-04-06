# PowerGuard API Testing Tools

This directory contains tools for testing the PowerGuard AI Backend API. These tools allow you to run automated tests, verify API functionality, and test prompt handling capabilities.

## Available Testing Tools

1. **Comprehensive Automated Test Script** (`automated_test.py`)  
   A complete test suite that runs multiple test cases and validates responses.

2. **Individual Test Case Runner** (`test_case_runner.py`)  
   A tool for testing individual endpoints with detailed output for debugging.

3. **API Benchmark Tool** (`benchmark.py`)  
   A utility for measuring API performance under different conditions.

4. **Test Runner** (`run_all_tests.py`)  
   A script that runs all test files in sequence and provides a comprehensive summary.

5. **API Client Example** (`api_client_example.py`)  
   A sample client that demonstrates how to use the API programmatically from your own code.

## Installation

Before running the tests, install the required Python packages:

```bash
pip install requests
```

## Testing Tools Usage

### Test Runner (All Tests)

The test runner script allows you to run multiple test scripts in sequence and see a consolidated summary.

```bash
python run_all_tests.py [options]
```

Options:
- `--tests TESTS`: Comma-separated list of tests to run (options: single, prompt, automated)
- `--verbose`, `-v`: Enable verbose output (shows script output instead of just summary)
- `--url URL`: Base URL for all API tests

Example:
```bash
# Run all tests 
python run_all_tests.py

# Run just the simple test and comprehensive automated test
python run_all_tests.py --tests single,automated

# Run all tests with verbose output
python run_all_tests.py -v

# Run all tests against a different server
python run_all_tests.py --url http://localhost:8000
```

### Automated Test Suite

The automated test script runs a comprehensive set of tests against the API.

```bash
python automated_test.py [options]
```

Options:
- `--verbose`, `-v`: Enable verbose output with detailed request/response data
- `--url URL`: Specify a custom API URL (default: https://powerguardbackend.onrender.com)
- `--tests TESTS`: Run specific tests (comma-separated list of test names)
- `--repeat N`: Repeat each test N times (default: 1)

Example:
```bash
# Run all tests with verbose output
python automated_test.py -v

# Run specific tests
python automated_test.py --tests "Battery optimization,Data optimization"

# Test against local development server
python automated_test.py --url http://localhost:8000

# Run battery optimization test 3 times
python automated_test.py --tests "Battery optimization" --repeat 3
```

### Individual Test Case Runner

The test case runner allows you to test specific scenarios with detailed output.

```bash
python test_case_runner.py [options]
```

Options:
- `--url URL`: Specify a custom API URL (default: https://powerguardbackend.onrender.com)
- `--prompt PROMPT`: Prompt to send with the request
- `--test`: Use test endpoints instead of real analyze endpoint
- `--root`: Test the root endpoint only

Example:
```bash
# Test root endpoint
python test_case_runner.py --root

# Test with battery optimization prompt
python test_case_runner.py --prompt "Optimize my battery life"

# Test with data saving prompt using test endpoint
python test_case_runner.py --prompt "Save network data" --test

# Test against local development server
python test_case_runner.py --url http://localhost:8000 --prompt "Kill battery-draining apps"
```

### Benchmark Tool

The benchmark tool allows you to measure API performance with different payloads and concurrency levels.

```bash
python benchmark.py [options]
```

Options:
- `--prompt PROMPT`: Type of prompt to use (choices: battery, data, combined, specific, none)
- `--requests N`: Number of requests to make (default: 10)
- `--concurrent`: Make requests concurrently
- `--url URL`: Base URL for the API
- `--size SIZE`: Size of payload (choices: small, medium, large)
- `--timeout TIMEOUT`: Request timeout in seconds (default: 30)
- `--test`: Use test endpoints instead of analyze endpoint

Example:
```bash
# Run a basic benchmark
python benchmark.py

# Benchmark with a battery optimization prompt
python benchmark.py --prompt battery

# Run 20 concurrent requests with large payloads
python benchmark.py --requests 20 --concurrent --size large

# Benchmark the test endpoints
python benchmark.py --test

# Test against a local server with timeouts of 10 seconds
python benchmark.py --url http://localhost:8000 --timeout 10
```

### API Client Example

The API client example demonstrates how to use the API in your own code.

```bash
python api_client_example.py
```

This script demonstrates:

1. Creating a client for the PowerGuard API
2. Making requests to various endpoints
3. Working with API responses
4. Handling errors and fallbacks
5. Using the API with different prompts

The `PowerGuardClient` class in this example can be adapted for use in your own applications to integrate with the PowerGuard API. It includes methods for:

- Analyzing device data with the main `/api/analyze` endpoint
- Using the test endpoints for quick testing
- Retrieving stored usage patterns for a device
- Helper functions for working with response data

Example usage in your own code:

```python
from api_client_example import PowerGuardClient, create_sample_device_data

# Create a client
client = PowerGuardClient(base_url="https://powerguardbackend.onrender.com")

# Create sample device data with a prompt
device_data = create_sample_device_data(
    device_id="my_device_001",
    prompt="Optimize battery life"
)

# Send data to the API for analysis
response = client.analyze_device_data(device_data)

# Process the response
actionable_items = response.get("actionable", [])
for item in actionable_items:
    print(f"Recommendation: {item.get('description')}")
```

## Test Cases

The automated test suite includes the following test cases:

1. **No prompt** - Tests API behavior with no user prompt
2. **Battery optimization** - Tests prompts related to saving battery
3. **Data optimization** - Tests prompts related to saving data
4. **Combined optimization** - Tests prompts for both battery and data optimization
5. **Specific action** - Tests prompts requesting specific actions
6. **Negation handling** - Tests prompts with negation (e.g., "optimize battery but not data")
7. **Irrelevant prompt** - Tests system handling of prompts unrelated to optimization
8. **Empty prompt** - Tests behavior with an empty prompt string
9. **Extremely long prompt** - Tests system with very long prompts
10. **Special characters** - Tests prompts with special characters

## Validation

Each test case includes a validation function that checks for the expected response structure and content. The automated test suite will report on:

- Missing required fields
- Expected actionable items based on the prompt
- Expected insights based on the prompt
- Consistency between the prompt and the response

## Endpoints Tested

The tools test the following API endpoints:

- `GET /` - Root endpoint
- `POST /api/analyze` - Main analysis endpoint (with and without prompts)
- `GET /api/test/with-prompt/{prompt}` - Test endpoint with prompt
- `GET /api/test/no-prompt` - Test endpoint without prompt

## Performance Testing

The benchmark tool can help you assess API performance under different conditions:

1. **Response Time**: Measure how long the API takes to respond to requests
2. **Concurrency**: Test how the API handles multiple simultaneous requests
3. **Payload Size**: Evaluate the impact of different payload sizes on performance
4. **Prompt Type**: Compare performance with different types of prompts
5. **Endpoint Comparison**: Compare the performance of real endpoints vs. test endpoints

The tool provides detailed statistics including:
- Minimum, maximum, and mean response times
- Median response time
- 90th and 95th percentile response times
- Success and failure rates

## Tips for Effective Testing

1. Use `run_all_tests.py` for a complete testing suite run with summary
2. Use `automated_test.py` with verbose flag (`-v`) for detailed debugging
3. Use `test_case_runner.py` for testing specific scenarios
4. If experiencing issues with a specific prompt, test it individually with `test_case_runner.py`
5. Use `benchmark.py` to evaluate API performance under different conditions
6. Check that responses include appropriate actionable items based on the prompt
7. Verify that battery-related prompts yield battery-related actions and similarly for data-related prompts 