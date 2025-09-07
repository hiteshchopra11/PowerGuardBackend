#!/usr/bin/env python3
import subprocess
import sys
import time
import argparse
from datetime import datetime

# Available tests to run
TEST_SCRIPTS = {
    "automated": {
        "script": "automated_test.py",
        "description": "Comprehensive automated test suite"
    }
}

def run_script(script_path, verbose=False, url=None):
    """Run a test script and return result"""
    start_time = time.time()
    cmd = [sys.executable, script_path]
    
    if url:
        if script_path == "automated_test.py":
            cmd.extend(["--url", url])
        else:
            # Add URL argument for other scripts if supported
            cmd.extend(["--url", url])
    
    if verbose and script_path == "automated_test.py":
        cmd.append("-v")
    
    print(f"\n{'=' * 80}")
    print(f"Running {script_path}...")
    print(f"{'=' * 80}")
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=not verbose)
        success = result.returncode == 0
        end_time = time.time()
        execution_time = end_time - start_time
        
        if not verbose:
            if success:
                print(f"✅ {script_path} completed successfully in {execution_time:.2f} seconds")
            else:
                print(f"❌ {script_path} failed with return code {result.returncode} in {execution_time:.2f} seconds")
                print("\nError output:")
                print(result.stderr.decode('utf-8'))
        else:
            print(f"\nExecution time: {execution_time:.2f} seconds")
            print(f"Return code: {result.returncode}")
            
        return {
            "script": script_path,
            "success": success,
            "execution_time": execution_time,
            "return_code": result.returncode
        }
    except Exception as e:
        print(f"Error running {script_path}: {str(e)}")
        return {
            "script": script_path,
            "success": False,
            "execution_time": time.time() - start_time,
            "error": str(e)
        }

def run_tests(tests, verbose=False, url=None):
    """Run selected tests and return results"""
    results = []
    
    print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using URL: {url if url else 'Default URLs in scripts'}")
    print(f"Verbose mode: {'Enabled' if verbose else 'Disabled'}")
    
    start_time = time.time()
    
    for test_key in tests:
        if test_key in TEST_SCRIPTS:
            script_info = TEST_SCRIPTS[test_key]
            print(f"\nRunning {test_key} test: {script_info['description']}")
            result = run_script(script_info["script"], verbose, url)
            results.append(result)
        else:
            print(f"Unknown test: {test_key}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return results, total_time

def print_summary(results, total_time):
    """Print a summary of test results"""
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests run: {len(results)}")
    print(f"Successful tests: {success_count}")
    print(f"Failed tests: {failed_count}")
    print(f"Total execution time: {total_time:.2f} seconds")
    
    if results:
        print("\nTest details:")
        for result in results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"  {result['script']}: {status} ({result['execution_time']:.2f}s)")

def main():
    parser = argparse.ArgumentParser(description="PowerGuard API Test Runner")
    parser.add_argument("--tests", type=str,
                      help="Comma-separated list of tests to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Show verbose output")
    parser.add_argument("--url", type=str,
                      help="Base URL for the API")
    
    args = parser.parse_args()
    
    # Determine which tests to run
    if args.tests:
        tests_to_run = [t.strip() for t in args.tests.split(",")]
    else:
        tests_to_run = list(TEST_SCRIPTS.keys())
    
    # Run the tests
    results, total_time = run_tests(tests_to_run, args.verbose, args.url)
    
    # Print summary
    print_summary(results, total_time)
    
    # Return exit code
    if any(not r["success"] for r in results):
        sys.exit(1)

if __name__ == "__main__":
    main() 