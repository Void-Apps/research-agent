#!/usr/bin/env python3
"""
Test runner script for comprehensive testing
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True

def main():
    """Main test runner"""
    print("🧪 Starting comprehensive test suite...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Test commands to run
    test_commands = [
        ("python -m pytest tests/ -v --tb=short", "Unit Tests"),
        ("python -m pytest tests/ -v --cov=. --cov-report=term-missing", "Coverage Report"),
        ("python -m pytest tests/ -v --cov=. --cov-report=html", "HTML Coverage Report"),
        ("python -m pytest tests/test_integration_workflow.py -v", "Integration Tests"),
        ("python -m pytest tests/ -m 'not slow' -v", "Fast Tests Only"),
    ]
    
    results = []
    
    for command, description in test_commands:
        success = run_command(command, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()