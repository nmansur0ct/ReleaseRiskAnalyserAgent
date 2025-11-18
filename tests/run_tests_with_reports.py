"""
Enhanced Test Runner with Detailed Reports

Runs tests and generates comprehensive execution reports with:
- Test scenarios
- Test cases
- Expected results
- Actual results
- Execution statistics
"""

import unittest
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_report_generator import EnhancedTestRunner, TestReportGenerator

def run_tests_with_detailed_reports(test_pattern='test_*.py', output_dir='reports', 
                                    report_name='test_execution_report', verbose=True):
    """
    Run tests and generate detailed execution reports
    
    Args:
        test_pattern: Pattern to discover test files
        output_dir: Directory for report output
        report_name: Base name for report files
        verbose: Whether to display detailed output
        
    Returns:
        tuple: (test_result, report_path)
    """
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern=test_pattern)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 100)
    print("ENHANCED TEST EXECUTION WITH DETAILED REPORTING")
    print("=" * 100)
    print(f"Test Discovery Path: {start_dir}")
    print(f"Test Pattern: {test_pattern}")
    print(f"Report Output: {output_dir}")
    print("=" * 100)
    print()
    
    # Run tests with enhanced runner
    runner = EnhancedTestRunner(
        output_dir=output_dir,
        report_name=report_name,
        verbosity=2 if verbose else 1,
        stream=sys.stdout
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 100)
    print("TEST EXECUTION SUMMARY")
    print("=" * 100)
    print(f"Total Tests:       {result.testsRun}")
    print(f"✓ Passed:         {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"✗ Failed:         {len(result.failures)}")
    print(f"⚠ Errors:          {len(result.errors)}")
    print(f"⊘ Skipped:         {len(result.skipped)}")
    print(f"Execution Time:   {end_time - start_time:.2f}s")
    print("=" * 100)
    
    return result

def run_integration_tests_with_reports(verbose=True):
    """Run integration tests with detailed reports"""
    return run_tests_with_detailed_reports(
        test_pattern='test_integration.py',
        output_dir='reports/integration',
        report_name='integration_test_execution',
        verbose=verbose
    )

def run_unit_tests_with_reports(verbose=True):
    """Run unit tests with detailed reports"""
    return run_tests_with_detailed_reports(
        test_pattern='test_*.py',
        output_dir='reports/unit',
        report_name='unit_test_execution',
        verbose=verbose
    )

def run_specific_test_with_report(test_class_name, test_method_name=None, verbose=True):
    """
    Run a specific test class or method with detailed report
    
    Args:
        test_class_name: Name of the test class
        test_method_name: Optional specific test method
        verbose: Whether to display detailed output
    """
    # Import test module
    test_module = __import__(f'tests.{test_class_name.split(".")[0]}', fromlist=[test_class_name])
    
    # Load test
    loader = unittest.TestLoader()
    if test_method_name:
        suite = loader.loadTestsFromName(f'{test_class_name}.{test_method_name}')
    else:
        test_class = getattr(test_module, test_class_name.split('.')[-1])
        suite = loader.loadTestsFromTestCase(test_class)
    
    # Run with enhanced runner
    output_dir = 'reports/specific'
    os.makedirs(output_dir, exist_ok=True)
    
    runner = EnhancedTestRunner(
        output_dir=output_dir,
        report_name=f'{test_class_name}_report',
        verbosity=2 if verbose else 1
    )
    
    result = runner.run(suite)
    return result

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests with detailed execution reports')
    parser.add_argument('--type', choices=['unit', 'integration', 'all'], default='all',
                       help='Type of tests to run')
    parser.add_argument('--pattern', default='test_*.py',
                       help='Test file pattern')
    parser.add_argument('--output', default='reports',
                       help='Output directory for reports')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    if args.type == 'integration':
        result = run_integration_tests_with_reports(verbose)
    elif args.type == 'unit':
        result = run_unit_tests_with_reports(verbose)
    else:
        result = run_tests_with_detailed_reports(args.pattern, args.output, 
                                                 'test_execution_report', verbose)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
