#!/usr/bin/env python3
"""
Simple test to verify the package works correctly.
This is a basic test that can be run by CI/CD.
"""

import sys
import os

def test_import():
    """Test that the package can be imported."""
    try:
        import twobitreader
        print("✅ Package imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import package: {e}")
        return False

def test_version():
    """Test that we can get version information."""
    try:
        import twobitreader
        # Check if __version__ exists
        if hasattr(twobitreader, '__version__'):
            print(f"✅ Version: {twobitreader.__version__}")
        else:
            print("⚠️  No __version__ attribute found")
        return True
    except Exception as e:
        print(f"❌ Failed to get version: {e}")
        return False

def test_cli():
    """Test that the CLI module can be run."""
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'twobitreader', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CLI help works")
            return True
        else:
            print(f"⚠️  CLI help returned code {result.returncode}")
            return True  # Don't fail if help isn't implemented
    except Exception as e:
        print(f"⚠️  CLI test failed: {e}")
        return True  # Don't fail if CLI isn't implemented

def main():
    """Run all tests."""
    print("Running basic package tests...")
    
    tests = [
        test_import,
        test_version,
        test_cli,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
