"""
Integration Test Runner

Executes all integration tests and generates detailed reports.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_integration_tests(verbose=True):
    """
    Run all integration tests and generate report
    
    Args:
        verbose: Whether to display detailed output
        
    Returns:
        tuple: (test_result, summary_dict)
    """
    # Discover integration tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_integration.py')
    
    # Run tests with custom result handler
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1, stream=sys.stdout)
    
    print("=" * 80)
    print("INTEGRATION TEST SUITE")
    print("=" * 80)
    print(f"Test Discovery Path: {start_dir}")
    print(f"Test Pattern: test_integration.py")
    print("=" * 80)
    print()
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Calculate summary statistics
    total_tests = result.testsRun
    successes = total_tests - len(result.failures) - len(result.errors) - len(result.skipped)
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    execution_time = end_time - start_time
    
    # Generate summary
    summary = {
        'total': total_tests,
        'successes': successes,
        'failures': failures,
        'errors': errors,
        'skipped': skipped,
        'execution_time': execution_time,
        'success_rate': (successes / total_tests * 100) if total_tests > 0 else 0
    }
    
    # Print summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests:       {total_tests}")
    print(f"✓ Passed:         {successes} ({summary['success_rate']:.1f}%)")
    print(f"✗ Failed:         {failures}")
    print(f"⚠ Errors:          {errors}")
    print(f"⊘ Skipped:         {skipped}")
    print(f"Execution Time:   {execution_time:.2f}s")
    print("=" * 80)
    
    # Print failure details
    if failures > 0:
        print("\n" + "=" * 80)
        print("FAILURE DETAILS")
        print("=" * 80)
        for test, traceback in result.failures:
            print(f"\n✗ {test}")
            print("-" * 80)
            print(traceback)
    
    # Print error details
    if errors > 0:
        print("\n" + "=" * 80)
        print("ERROR DETAILS")
        print("=" * 80)
        for test, traceback in result.errors:
            print(f"\n⚠ {test}")
            print("-" * 80)
            print(traceback)
    
    # Overall status
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✓ ALL INTEGRATION TESTS PASSED")
    else:
        print("✗ SOME INTEGRATION TESTS FAILED")
    print("=" * 80)
    
    return result, summary

def run_specific_test_class(test_class_name, verbose=True):
    """
    Run a specific integration test class
    
    Args:
        test_class_name: Name of the test class (e.g., 'TestFullAnalysisWorkflow')
        verbose: Whether to display detailed output
        
    Returns:
        tuple: (test_result, summary_dict)
    """
    from tests.test_integration import (
        TestFullAnalysisWorkflow,
        TestCodeReviewIntegration,
        TestReportGenerationIntegration,
        TestErrorHandlingIntegration,
        TestPerformanceIntegration
    )
    
    test_classes = {
        'TestFullAnalysisWorkflow': TestFullAnalysisWorkflow,
        'TestCodeReviewIntegration': TestCodeReviewIntegration,
        'TestReportGenerationIntegration': TestReportGenerationIntegration,
        'TestErrorHandlingIntegration': TestErrorHandlingIntegration,
        'TestPerformanceIntegration': TestPerformanceIntegration
    }
    
    if test_class_name not in test_classes:
        print(f"Error: Test class '{test_class_name}' not found")
        print(f"Available classes: {', '.join(test_classes.keys())}")
        return None, None
    
    # Load specific test class
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_classes[test_class_name])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    
    print("=" * 80)
    print(f"RUNNING: {test_class_name}")
    print("=" * 80)
    print()
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Calculate summary
    total_tests = result.testsRun
    successes = total_tests - len(result.failures) - len(result.errors)
    
    summary = {
        'total': total_tests,
        'successes': successes,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'execution_time': end_time - start_time
    }
    
    print(f"\n{test_class_name}: {successes}/{total_tests} passed in {summary['execution_time']:.2f}s")
    
    return result, summary

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run integration tests')
    parser.add_argument('--class', dest='test_class', help='Run specific test class')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    if args.test_class:
        result, summary = run_specific_test_class(args.test_class, verbose)
    else:
        result, summary = run_integration_tests(verbose)
    
    # Exit with appropriate code
    sys.exit(0 if result and result.wasSuccessful() else 1)
