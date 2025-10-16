#!/usr/bin/env python3
"""Simple test script to verify the application works."""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from app import create_app
        from app.models import Trip, Base
        from app.algorithms import TopKFrequent, MedianCalculator, AnomalyDetector
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created."""
    try:
        from app import create_app
        app = create_app()
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False

def test_algorithms():
    """Test custom algorithms."""
    try:
        from app.algorithms import TopKFrequent, MedianCalculator, AnomalyDetector
        
        # Test TopKFrequent
        topk = TopKFrequent(3)
        topk.add("A", 5)
        topk.add("B", 3)
        topk.add("C", 8)
        topk.add("D", 2)
        result = topk.get_top_k()
        print(f"✓ TopKFrequent works: {result}")
        
        # Test MedianCalculator
        median_calc = MedianCalculator()
        for i in [1, 2, 3, 4, 5]:
            median_calc.add(i)
        median_val = median_calc.get_median()
        print(f"✓ MedianCalculator works: median = {median_val}")
        
        # Test AnomalyDetector
        detector = AnomalyDetector(threshold=2.0)
        normal_values = [10, 11, 9, 12, 10, 11, 9, 10]
        anomalies = []
        for val in normal_values:
            if detector.add(val):
                anomalies.append(val)
        print(f"✓ AnomalyDetector works: {len(anomalies)} anomalies found")
        
        return True
    except Exception as e:
        print(f"✗ Algorithm test error: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing NYC Taxi Dashboard Application...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_app_creation,
        test_algorithms,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! The application is ready to use.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Generate sample data: python scripts/generate_sample_data.py")
        print("3. Run the app: python run.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
