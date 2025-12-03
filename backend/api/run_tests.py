#!/usr/bin/env python3
"""
Backend Test Runner

This script runs all backend unit tests without requiring Docker.
It uses an in-memory SQLite database for testing.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose output
    python run_tests.py -k test_auth # Run specific test
    python run_tests.py --cov        # With coverage report
"""

import sys
import subprocess
import os

def main():
    """Run pytest with appropriate arguments."""
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest is not installed!")
        print("Install test dependencies with:")
        print("  pip install -r requirements-test.txt")
        return 1
    
    # Build pytest command
    pytest_args = ["pytest"]
    
    # Add any command line arguments passed to this script
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    else:
        # Default arguments
        pytest_args.extend([
            "-v",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
        ])
    
    print("=" * 70)
    print("🧪 Running Backend Unit Tests")
    print("=" * 70)
    print(f"Command: {' '.join(pytest_args)}")
    print()
    
    # Run pytest
    result = subprocess.run(pytest_args)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
    print("=" * 70)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
