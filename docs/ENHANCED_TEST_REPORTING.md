# Enhanced Test Reporting System

## Overview

The enhanced test reporting system generates comprehensive test execution reports with detailed information about test scenarios, test cases, expected results, and actual results in multiple formats (Text, JSON, HTML).

## Features

✅ **Detailed Test Scenarios**: Group related tests into logical scenarios  
✅ **Test Case Metadata**: Rich descriptions, expected results, and actual outcomes  
✅ **Multiple Report Formats**: Text, JSON, and HTML reports  
✅ **Execution Statistics**: Pass rates, timing, error tracking  
✅ **Performance Testing**: Built-in performance assertions  
✅ **Integration Test Markers**: Tag tests requiring external services  
✅ **Critical Test Identification**: Mark high-priority tests  

## Quick Start

### 1. Basic Usage

```bash
# Run tests with enhanced reporting
python tests/run_tests_with_reports.py

# Run specific test type
python tests/run_tests_with_reports.py --type unit
python tests/run_tests_with_reports.py --type integration

# Specify output directory
python tests/run_tests_with_reports.py --output my_reports
```

### 2. Using Decorators

```python
from tests.test_decorators import test_scenario, test_case, performance_test

@test_scenario(
    scenario_name="User Authentication",
    description="Tests user login and logout functionality",
    category="Integration Tests"
)
class TestUserAuth(unittest.TestCase):
    
    @test_case(
        name="Valid User Login",
        description="User provides correct username and password",
        expected_result="User is authenticated and redirected to dashboard"
    )
    def test_valid_login(self):
        # Test implementation
        result = login("user", "pass")
        self.assertTrue(result.success)
```

## Decorators Reference

### @test_scenario

Groups tests into logical scenarios for better organization.

```python
@test_scenario(
    scenario_name="Payment Processing",
    description="Tests for payment gateway integration",
    category="Integration Tests"
)
class TestPayments(unittest.TestCase):
    pass
```

**Parameters**:
- `scenario_name` (str): Name of the test scenario
- `description` (str): Detailed description
- `category` (str): Category (e.g., "Unit Tests", "Integration Tests")

### @test_case

Adds detailed metadata to individual test methods.

```python
@test_case(
    name="Process Credit Card Payment",
    description="Submit valid credit card information for payment",
    expected_result="Payment processed successfully, transaction ID returned"
)
def test_credit_card_payment(self):
    pass
```

**Parameters**:
- `name` (str): Friendly name for the test
- `description` (str): What is being tested
- `expected_result` (str): Expected outcome

### @performance_test

Ensures test completes within specified time.

```python
@performance_test(max_execution_time_ms=500)
def test_fast_query(self):
    # Must complete in under 500ms
    result = database.query()
```

**Parameters**:
- `max_execution_time_ms` (int): Maximum execution time in milliseconds

### @integration_test

Marks tests requiring external dependencies.

```python
@integration_test(
    dependencies=["Database", "Payment Gateway"],
    requires_external_service=True
)
def test_payment_flow(self):
    pass
```

**Parameters**:
- `dependencies` (list): List of required systems
- `requires_external_service` (bool): Whether external services are needed

### @critical_test

Identifies high-priority tests.

```python
@critical_test(severity="HIGH")
def test_data_integrity(self):
    pass
```

**Parameters**:
- `severity` (str): "HIGH", "MEDIUM", or "LOW"

## Report Formats

### Text Report

Human-readable format with all test details:

```
====================================================================================================
TEST EXECUTION REPORT
====================================================================================================

SUMMARY
----------------------------------------------------------------------------------------------------
Generated: 2025-11-18 19:23:32
Total Scenarios: 2
Total Test Cases: 7
✓ Passed: 7 (100.0%)
✗ Failed: 0
⚠ Errors: 0
⊘ Skipped: 0

====================================================================================================
SCENARIO: Code Review Report Generation
====================================================================================================
Scenario ID: SCN-001
Category: Unit Tests - Reporting
Description: Tests the comprehensive reporter's ability to generate various report formats

----------------------------------------------------------------------------------------------------
TEST CASE: Generate Basic Report Header
----------------------------------------------------------------------------------------------------
Case ID: TC-001
Method: test_report_header_generation
Status: PASSED
Execution Time: 0.000s
Timestamp: 2025-11-18 19:23:32

Description:
Verify that the report header contains all required information

Expected Result:
Report header should be generated with COMPREHENSIVE CODE REVIEW title

Actual Result:
Test passed successfully
```

### JSON Report

Machine-readable format for automation:

```json
{
  "generated_at": "2025-11-18T19:23:32",
  "summary": {
    "total_scenarios": 2,
    "total_cases": 7,
    "passed": 7,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "pass_rate": 100.0
  },
  "scenarios": [
    {
      "scenario_id": "SCN-001",
      "name": "Code Review Report Generation",
      "test_cases": [
        {
          "case_id": "TC-001",
          "name": "Generate Basic Report Header",
          "expected_result": "Report header should be generated...",
          "actual_result": "Test passed successfully",
          "status": "PASSED",
          "execution_time": 0.000034
        }
      ]
    }
  ]
}
```

### HTML Report

Interactive web-based report with color-coding and filtering.

## Example: Complete Test with Metadata

```python
import unittest
from tests.test_decorators import test_scenario, test_case, integration_test

@test_scenario(
    scenario_name="Repository Analysis Workflow",
    description="End-to-end tests for repository analysis",
    category="Integration Tests"
)
class TestRepositoryAnalysis(unittest.TestCase):
    
    @test_case(
        name="Analyze Single Repository",
        description="Execute complete analysis on a single GitHub repository",
        expected_result="Analysis completes with risk level assigned, quality score calculated, and comprehensive report generated"
    )
    @integration_test(
        dependencies=["GitHub API", "LLM Service"],
        requires_external_service=True
    )
    def test_single_repo_analysis(self):
        # Arrange
        repo_url = "https://github.com/user/repo.git"
        
        # Act
        result = analyze_repository(repo_url)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn(result.risk_level, ['LOW', 'MEDIUM', 'HIGH'])
        self.assertGreater(result.quality_score, 0)
```

## Report Output Structure

```
reports/
├── unit/
│   ├── unit_test_execution_20251118_192332.txt
│   ├── unit_test_execution_20251118_192332.json
│   └── unit_test_execution_20251118_192332.html
├── integration/
│   ├── integration_test_execution_20251118_192400.txt
│   ├── integration_test_execution_20251118_192400.json
│   └── integration_test_execution_20251118_192400.html
└── examples/
    └── ...
```

## Command Reference

### Run All Tests with Reports

```bash
python tests/run_tests_with_reports.py
```

### Run Unit Tests Only

```bash
python tests/run_tests_with_reports.py --type unit
```

### Run Integration Tests Only

```bash
python tests/run_tests_with_reports.py --type integration
```

### Custom Output Directory

```bash
python tests/run_tests_with_reports.py --output custom_reports
```

### Quiet Mode

```bash
python tests/run_tests_with_reports.py --quiet
```

### Custom Test Pattern

```bash
python tests/run_tests_with_reports.py --pattern "test_reporter*.py"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Tests with Reports

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests with detailed reports
        run: python tests/run_tests_with_reports.py --type all
      
      - name: Upload test reports
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: reports/
```

## Benefits

1. **Clear Documentation**: Expected vs actual results provide clear test intent
2. **Easier Debugging**: Detailed failure information with tracebacks
3. **Better Organization**: Scenarios group related tests logically
4. **Stakeholder Communication**: HTML reports for non-technical reviewers
5. **Automation-Friendly**: JSON format for CI/CD pipelines
6. **Historical Tracking**: Timestamped reports for trend analysis
7. **Performance Monitoring**: Execution times tracked for each test

## Best Practices

### 1. Write Clear Descriptions

```python
@test_case(
    name="Validate Email Format",
    description="User enters email address, system validates format using regex pattern",
    expected_result="Valid emails pass (user@example.com), invalid emails fail (invalid@)"
)
```

### 2. Be Specific with Expected Results

```python
# Good - Specific
expected_result="Function returns list of 5 users, each with 'id', 'name', 'email' fields"

# Bad - Vague
expected_result="Function works correctly"
```

### 3. Use Scenarios to Group Related Tests

```python
@test_scenario("User Registration", "All tests related to new user signup", "E2E Tests")
class TestRegistration(unittest.TestCase):
    # All registration-related tests here
```

### 4. Mark Integration Tests Appropriately

```python
@integration_test(dependencies=["Database", "Email Service"])
def test_user_signup_flow(self):
    # This clearly indicates external dependencies
```

## Troubleshooting

### Tests Not Appearing in Report

Ensure you're using the enhanced test runner:

```python
from tests.run_tests_with_reports import run_tests_with_detailed_reports
```

### Metadata Not Showing

Apply decorators to test classes and methods:

```python
@test_scenario(...)  # On class
class TestMyFeature(unittest.TestCase):
    
    @test_case(...)  # On method
    def test_something(self):
        pass
```

### Reports Not Generated

Check that output directory exists and is writable:

```python
os.makedirs("reports", exist_ok=True)
```

## Files

- `tests/test_report_generator.py` - Report generation engine
- `tests/run_tests_with_reports.py` - Enhanced test runner
- `tests/test_decorators.py` - Decorator definitions
- `tests/test_example_with_metadata.py` - Usage examples

## Next Steps

1. Apply decorators to existing test files
2. Run tests with enhanced reporting
3. Review generated reports
4. Integrate into CI/CD pipeline
5. Share HTML reports with stakeholders
