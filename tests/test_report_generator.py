"""
Test Report Generator

Generates detailed test execution reports with scenarios, cases, expected/actual results.
"""

import unittest
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from io import StringIO

class TestScenario:
    """Represents a test scenario with metadata"""
    
    def __init__(self, scenario_id: str, name: str, description: str, category: str):
        self.scenario_id = scenario_id
        self.name = name
        self.description = description
        self.category = category
        self.test_cases: List[TestCase] = []
    
    def add_test_case(self, test_case: 'TestCase'):
        """Add a test case to this scenario"""
        self.test_cases.append(test_case)

class TestCase:
    """Represents a single test case with expected and actual results"""
    
    def __init__(self, case_id: str, name: str, description: str, 
                 expected_result: str, test_method: str):
        self.case_id = case_id
        self.name = name
        self.description = description
        self.expected_result = expected_result
        self.test_method = test_method
        self.actual_result: str = ""
        self.status: str = "NOT_RUN"  # NOT_RUN, PASSED, FAILED, ERROR, SKIPPED
        self.execution_time: float = 0.0
        self.error_message: str = ""
        self.traceback: str = ""
        self.timestamp: str = ""
    
    def set_result(self, status: str, actual_result: str, execution_time: float = 0.0,
                   error_message: str = "", traceback: str = ""):
        """Set the test execution result"""
        self.status = status
        self.actual_result = actual_result
        self.execution_time = execution_time
        self.error_message = error_message
        self.traceback = traceback
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class TestReportGenerator:
    """Generates comprehensive test execution reports"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        self.scenarios: List[TestScenario] = []
        os.makedirs(output_dir, exist_ok=True)
    
    def add_scenario(self, scenario: TestScenario):
        """Add a test scenario"""
        self.scenarios.append(scenario)
    
    def generate_report(self, report_name: str = "test_execution_report") -> str:
        """Generate comprehensive test execution report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate text report
        txt_path = os.path.join(self.output_dir, f"{report_name}_{timestamp}.txt")
        self._generate_text_report(txt_path)
        
        # Generate JSON report
        json_path = os.path.join(self.output_dir, f"{report_name}_{timestamp}.json")
        self._generate_json_report(json_path)
        
        # Generate HTML report
        html_path = os.path.join(self.output_dir, f"{report_name}_{timestamp}.html")
        self._generate_html_report(html_path)
        
        return txt_path
    
    def _generate_text_report(self, file_path: str):
        """Generate text format report"""
        with open(file_path, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("TEST EXECUTION REPORT\n")
            f.write("=" * 100 + "\n\n")
            
            # Summary statistics
            total_cases = sum(len(s.test_cases) for s in self.scenarios)
            passed = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "PASSED")
            failed = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "FAILED")
            errors = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "ERROR")
            skipped = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "SKIPPED")
            
            f.write("SUMMARY\n")
            f.write("-" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Scenarios: {len(self.scenarios)}\n")
            f.write(f"Total Test Cases: {total_cases}\n")
            f.write(f"✓ Passed: {passed} ({passed/total_cases*100:.1f}%)\n" if total_cases > 0 else "✓ Passed: 0\n")
            f.write(f"✗ Failed: {failed}\n")
            f.write(f"⚠ Errors: {errors}\n")
            f.write(f"⊘ Skipped: {skipped}\n\n")
            
            # Detailed scenarios
            for scenario in self.scenarios:
                f.write("=" * 100 + "\n")
                f.write(f"SCENARIO: {scenario.name}\n")
                f.write("=" * 100 + "\n")
                f.write(f"Scenario ID: {scenario.scenario_id}\n")
                f.write(f"Category: {scenario.category}\n")
                f.write(f"Description: {scenario.description}\n\n")
                
                for test_case in scenario.test_cases:
                    f.write("-" * 100 + "\n")
                    f.write(f"TEST CASE: {test_case.name}\n")
                    f.write("-" * 100 + "\n")
                    f.write(f"Case ID: {test_case.case_id}\n")
                    f.write(f"Method: {test_case.test_method}\n")
                    f.write(f"Status: {test_case.status}\n")
                    f.write(f"Execution Time: {test_case.execution_time:.3f}s\n")
                    f.write(f"Timestamp: {test_case.timestamp}\n\n")
                    
                    f.write(f"Description:\n{test_case.description}\n\n")
                    
                    f.write(f"Expected Result:\n{test_case.expected_result}\n\n")
                    
                    f.write(f"Actual Result:\n{test_case.actual_result}\n\n")
                    
                    if test_case.error_message:
                        f.write(f"Error Message:\n{test_case.error_message}\n\n")
                    
                    if test_case.traceback:
                        f.write(f"Traceback:\n{test_case.traceback}\n\n")
                
                f.write("\n")
    
    def _generate_json_report(self, file_path: str):
        """Generate JSON format report"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": self._get_summary_stats(),
            "scenarios": [
                {
                    "scenario_id": scenario.scenario_id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "category": scenario.category,
                    "test_cases": [
                        {
                            "case_id": tc.case_id,
                            "name": tc.name,
                            "description": tc.description,
                            "test_method": tc.test_method,
                            "expected_result": tc.expected_result,
                            "actual_result": tc.actual_result,
                            "status": tc.status,
                            "execution_time": tc.execution_time,
                            "timestamp": tc.timestamp,
                            "error_message": tc.error_message,
                            "traceback": tc.traceback
                        }
                        for tc in scenario.test_cases
                    ]
                }
                for scenario in self.scenarios
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def _generate_html_report(self, file_path: str):
        """Generate HTML format report"""
        summary = self._get_summary_stats()
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Execution Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .scenario {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-case {{ border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; background-color: #ecf0f1; }}
        .test-case.passed {{ border-left-color: #27ae60; }}
        .test-case.failed {{ border-left-color: #e74c3c; }}
        .test-case.error {{ border-left-color: #f39c12; }}
        .test-case.skipped {{ border-left-color: #95a5a6; }}
        .status {{ font-weight: bold; padding: 5px 10px; border-radius: 3px; display: inline-block; }}
        .status.passed {{ background-color: #27ae60; color: white; }}
        .status.failed {{ background-color: #e74c3c; color: white; }}
        .status.error {{ background-color: #f39c12; color: white; }}
        .status.skipped {{ background-color: #95a5a6; color: white; }}
        .section {{ margin: 15px 0; }}
        .section-title {{ font-weight: bold; color: #2c3e50; margin-bottom: 5px; }}
        .section-content {{ padding: 10px; background-color: white; border-radius: 3px; white-space: pre-wrap; }}
        .error-content {{ background-color: #fee; color: #c00; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Scenarios</td>
                <td>{summary['total_scenarios']}</td>
            </tr>
            <tr>
                <td>Total Test Cases</td>
                <td>{summary['total_cases']}</td>
            </tr>
            <tr>
                <td>Passed</td>
                <td style="color: #27ae60; font-weight: bold;">{summary['passed']} ({summary['pass_rate']:.1f}%)</td>
            </tr>
            <tr>
                <td>Failed</td>
                <td style="color: #e74c3c; font-weight: bold;">{summary['failed']}</td>
            </tr>
            <tr>
                <td>Errors</td>
                <td style="color: #f39c12; font-weight: bold;">{summary['errors']}</td>
            </tr>
            <tr>
                <td>Skipped</td>
                <td style="color: #95a5a6;">{summary['skipped']}</td>
            </tr>
        </table>
    </div>
"""
        
        for scenario in self.scenarios:
            html_content += f"""
    <div class="scenario">
        <h2>Scenario: {scenario.name}</h2>
        <p><strong>ID:</strong> {scenario.scenario_id}</p>
        <p><strong>Category:</strong> {scenario.category}</p>
        <p><strong>Description:</strong> {scenario.description}</p>
"""
            
            for test_case in scenario.test_cases:
                status_class = test_case.status.lower()
                html_content += f"""
        <div class="test-case {status_class}">
            <h3>{test_case.name}</h3>
            <p>
                <strong>Case ID:</strong> {test_case.case_id} | 
                <strong>Method:</strong> {test_case.test_method} | 
                <span class="status {status_class}">{test_case.status}</span>
            </p>
            <p><strong>Execution Time:</strong> {test_case.execution_time:.3f}s | <strong>Timestamp:</strong> {test_case.timestamp}</p>
            
            <div class="section">
                <div class="section-title">Description:</div>
                <div class="section-content">{test_case.description}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Expected Result:</div>
                <div class="section-content">{test_case.expected_result}</div>
            </div>
            
            <div class="section">
                <div class="section-title">Actual Result:</div>
                <div class="section-content">{test_case.actual_result}</div>
            </div>
"""
                
                if test_case.error_message:
                    html_content += f"""
            <div class="section">
                <div class="section-title">Error Message:</div>
                <div class="section-content error-content">{test_case.error_message}</div>
            </div>
"""
                
                if test_case.traceback:
                    html_content += f"""
            <div class="section">
                <div class="section-title">Traceback:</div>
                <div class="section-content error-content">{test_case.traceback}</div>
            </div>
"""
                
                html_content += """
        </div>
"""
            
            html_content += """
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(file_path, 'w') as f:
            f.write(html_content)
    
    def _get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        total_cases = sum(len(s.test_cases) for s in self.scenarios)
        passed = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "PASSED")
        failed = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "FAILED")
        errors = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "ERROR")
        skipped = sum(1 for s in self.scenarios for tc in s.test_cases if tc.status == "SKIPPED")
        
        return {
            "total_scenarios": len(self.scenarios),
            "total_cases": total_cases,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": (passed / total_cases * 100) if total_cases > 0 else 0
        }

class EnhancedTestResult(unittest.TextTestResult):
    """Enhanced test result that captures detailed execution data"""
    
    def __init__(self, stream, descriptions, verbosity, report_generator: TestReportGenerator):
        super().__init__(stream, descriptions, verbosity)
        self.report_generator = report_generator
        self.current_test_start_time = None
        self.test_metadata = {}  # Store metadata for tests
    
    def startTest(self, test):
        """Called when a test starts"""
        super().startTest(test)
        import time
        self.current_test_start_time = time.time()
    
    def addSuccess(self, test):
        """Called when a test passes"""
        super().addSuccess(test)
        self._record_test_result(test, "PASSED", "Test passed successfully")
    
    def addError(self, test, err):
        """Called when a test has an error"""
        super().addError(test, err)
        import traceback
        error_msg = str(err[1])
        tb = ''.join(traceback.format_exception(*err))
        self._record_test_result(test, "ERROR", f"Test encountered an error: {error_msg}", 
                                error_message=error_msg, traceback=tb)
    
    def addFailure(self, test, err):
        """Called when a test fails"""
        super().addFailure(test, err)
        import traceback
        error_msg = str(err[1])
        tb = ''.join(traceback.format_exception(*err))
        self._record_test_result(test, "FAILED", f"Test assertion failed: {error_msg}",
                                error_message=error_msg, traceback=tb)
    
    def addSkip(self, test, reason):
        """Called when a test is skipped"""
        super().addSkip(test, reason)
        self._record_test_result(test, "SKIPPED", f"Test skipped: {reason}")
    
    def _record_test_result(self, test, status, actual_result, error_message="", traceback=""):
        """Record detailed test result"""
        import time
        execution_time = time.time() - self.current_test_start_time if self.current_test_start_time else 0.0
        
        # Get test metadata
        test_id = test.id()
        metadata = self.test_metadata.get(test_id, {})
        
        # Create or find test case
        scenario_name = metadata.get('scenario', test.__class__.__name__)
        test_case_name = metadata.get('name', test._testMethodName)
        
        # Find or create scenario
        scenario = None
        for s in self.report_generator.scenarios:
            if s.name == scenario_name:
                scenario = s
                break
        
        if not scenario:
            scenario = TestScenario(
                scenario_id=f"SCN-{len(self.report_generator.scenarios) + 1:03d}",
                name=scenario_name,
                description=metadata.get('scenario_description', test.__class__.__doc__ or ""),
                category=metadata.get('category', 'Unit Tests')
            )
            self.report_generator.add_scenario(scenario)
        
        # Create test case
        test_case = TestCase(
            case_id=f"TC-{len(scenario.test_cases) + 1:03d}",
            name=test_case_name,
            description=metadata.get('description', test._testMethodDoc or ""),
            expected_result=metadata.get('expected_result', "Test should pass without errors"),
            test_method=test._testMethodName
        )
        
        test_case.set_result(status, actual_result, execution_time, error_message, traceback)
        scenario.add_test_case(test_case)

class EnhancedTestRunner(unittest.TextTestRunner):
    """Enhanced test runner that generates detailed reports"""
    
    def __init__(self, output_dir="reports", report_name="test_execution_report", **kwargs):
        super().__init__(**kwargs)
        self.report_generator = TestReportGenerator(output_dir)
        self.report_name = report_name
    
    def _makeResult(self):
        """Create enhanced test result"""
        return EnhancedTestResult(self.stream, self.descriptions, self.verbosity, self.report_generator)
    
    def run(self, test):
        """Run tests and generate report"""
        result = super().run(test)
        
        # Generate comprehensive report
        report_path = self.report_generator.generate_report(self.report_name)
        
        print(f"\n{'='*100}")
        print(f"Detailed test execution report generated:")
        print(f"  Text Report: {report_path}")
        print(f"  JSON Report: {report_path.replace('.txt', '.json')}")
        print(f"  HTML Report: {report_path.replace('.txt', '.html')}")
        print(f"{'='*100}")
        
        return result
