# Integration Testing Guide

## Overview

The integration test suite validates end-to-end workflows of the Risk Agent Analyzer system, ensuring that all components work together correctly in realistic scenarios.

## Test Structure

### Test Classes

1. **TestFullAnalysisWorkflow**
   - Complete repository analysis workflow
   - Single and multi-repository scenarios
   - PR discovery, file analysis, and risk assessment
   - Validates entire orchestration pipeline

2. **TestCodeReviewIntegration**
   - Multi-language code review workflows
   - Python, Java, JavaScript, React agent integration
   - Cross-language analysis coordination
   - Quality scoring and issue detection

3. **TestReportGenerationIntegration**
   - Comprehensive report generation
   - Data structure serialization
   - File system integration
   - Report content validation

4. **TestErrorHandlingIntegration**
   - LLM failure recovery mechanisms
   - Git API error handling
   - Graceful degradation testing
   - System resilience validation

5. **TestPerformanceIntegration**
   - Parallel agent execution
   - Performance benchmarking
   - Resource utilization validation
   - Scalability testing

## Running Integration Tests

### Run All Integration Tests

```bash
# Basic execution
python tests/run_integration_tests.py

# Quiet mode (less verbose)
python tests/run_integration_tests.py --quiet
```

### Run Specific Test Class

```bash
# Run workflow tests only
python tests/run_integration_tests.py --class TestFullAnalysisWorkflow

# Run code review integration tests
python tests/run_integration_tests.py --class TestCodeReviewIntegration

# Run report generation tests
python tests/run_integration_tests.py --class TestReportGenerationIntegration

# Run error handling tests
python tests/run_integration_tests.py --class TestErrorHandlingIntegration

# Run performance tests
python tests/run_integration_tests.py --class TestPerformanceIntegration
```

### Run Single Test Method

```bash
# Using unittest directly
python -m unittest tests.test_integration.TestFullAnalysisWorkflow.test_single_repository_analysis_workflow

# Using pytest (if installed)
pytest tests/test_integration.py::TestFullAnalysisWorkflow::test_single_repository_analysis_workflow -v
```

## Test Scenarios

### 1. Single Repository Analysis Workflow

**Purpose**: Validate complete analysis of a single repository

**Steps**:
1. Initialize RepositoryOrchestrator with configuration
2. Mock Git integration to return sample PRs
3. Mock LLM client for code analysis
4. Execute `analyze_repositories()` with single repo URL
5. Verify PR extraction and analysis
6. Validate risk level and quality classification
7. Confirm result structure and data integrity

**Expected Outcome**: Complete AnalysisResult with valid risk/quality metrics

### 2. Multi-Repository Analysis Workflow

**Purpose**: Validate parallel analysis of multiple repositories

**Steps**:
1. Configure orchestrator for multi-repo analysis
2. Mock Git integration with different PRs per repo
3. Execute analysis on multiple repo URLs
4. Verify each repository analyzed independently
5. Validate result aggregation

**Expected Outcome**: List of AnalysisResults, one per repository

### 3. Multi-Language Code Review

**Purpose**: Ensure all language agents work together

**Steps**:
1. Create PR with Python, Java, JavaScript, React files
2. Mock LLM with language-specific responses
3. Execute code review orchestration
4. Verify each language agent invoked
5. Validate language-specific analysis points

**Expected Outcome**: CodeReviewResult for each detected language

### 4. Comprehensive Report Generation

**Purpose**: Validate complete report creation workflow

**Steps**:
1. Create realistic AnalysisResult with all data structures
2. Configure ComprehensiveReporter
3. Generate report to file system
4. Verify file creation and structure
5. Validate report content completeness

**Expected Outcome**: Well-formatted report file with all sections

### 5. LLM Failure Recovery

**Purpose**: Test system resilience to LLM failures

**Steps**:
1. Mock LLM to fail first N calls
2. Execute code review with multiple files
3. Verify retry logic and fallback mechanisms
4. Validate graceful degradation
5. Ensure system continues with available data

**Expected Outcome**: Partial results without system crash

### 6. Git API Error Handling

**Purpose**: Test resilience to Git integration failures

**Steps**:
1. Mock Git API to raise exceptions
2. Execute repository analysis
3. Verify error catching and logging
4. Validate system stability

**Expected Outcome**: Graceful error handling, no unhandled exceptions

### 7. Parallel Agent Execution

**Purpose**: Verify performance characteristics

**Steps**:
1. Create PR with multiple language files
2. Mock LLM with processing delays
3. Measure execution time
4. Compare to theoretical sequential execution
5. Validate performance gains

**Expected Outcome**: Evidence of parallel execution (if implemented)

## Test Data Structures

### Mock PR Data

```python
pr_data = {
    'number': 1,
    'title': 'Feature PR',
    'state': 'open',
    'user': {'login': 'developer'},
    'created_at': '2024-01-01T00:00:00Z',
    'updated_at': '2024-01-02T00:00:00Z',
    'base': {
        'ref': 'main',
        'repo': {'clone_url': 'https://github.com/user/repo.git'}
    },
    'head': {'ref': 'feature-branch'},
    'html_url': 'https://github.com/user/repo/pull/1',
    'additions': 50,
    'deletions': 10,
    'changed_files': 3
}
```

### Mock File Data

```python
file_data = {
    'filename': 'src/main.py',
    'status': 'modified',
    'additions': 30,
    'deletions': 5,
    'patch': '+def new_feature():\n+    return True'
}
```

### Mock LLM Response

```python
llm_response = {
    'success': True,
    'response': json.dumps({
        'issues': [
            {
                'severity': 'warning',
                'line': 5,
                'message': 'Consider adding docstring',
                'type': 'documentation'
            }
        ],
        'quality_score': 85,
        'complexity_score': 40,
        'comment_coverage': 60
    }),
    'tokens_used': 150
}
```

## Mocking Strategy

### Git Integration Mocking

```python
@patch('src.integration.git_integration.get_git_manager')
def test_with_git(self, mock_git_manager):
    mock_git = Mock()
    mock_git.get_pull_requests = AsyncMock(return_value=[...])
    mock_git.get_pull_request_files = AsyncMock(return_value=[...])
    mock_git.get_file_content = AsyncMock(return_value='...')
    mock_git_manager.return_value = mock_git
```

### LLM Client Mocking

```python
@patch('src.integration.llm_client.LLMClient')
def test_with_llm(self, mock_llm_class):
    mock_llm = Mock()
    mock_llm.call_llm.return_value = {
        'success': True,
        'response': '{"issues": [...]}',
        'tokens_used': 100
    }
    mock_llm_class.return_value = mock_llm
```

### Conditional Response Mocking

```python
def llm_response_side_effect(*args, **kwargs):
    prompt = args[0] if args else ''
    if 'Python' in prompt:
        return python_response
    elif 'Java' in prompt:
        return java_response
    else:
        return default_response

mock_llm.call_llm.side_effect = llm_response_side_effect
```

## Expected Results

### Successful Test Run

```
================================================================================
INTEGRATION TEST SUITE
================================================================================
Test Discovery Path: /path/to/tests
Test Pattern: test_integration.py
================================================================================

test_single_repository_analysis_workflow ... ok
test_multi_repository_analysis_workflow ... ok
test_multi_language_code_review ... ok
test_comprehensive_report_generation ... ok
test_llm_failure_recovery ... ok
test_git_api_failure_handling ... ok
test_parallel_agent_execution ... ok

================================================================================
INTEGRATION TEST SUMMARY
================================================================================
Total Tests:       7
✓ Passed:         7 (100.0%)
✗ Failed:         0
⚠ Errors:          0
⊘ Skipped:         0
Execution Time:   5.23s
================================================================================

✓ ALL INTEGRATION TESTS PASSED
```

## Common Issues and Solutions

### Issue: Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure tests are run from project root:
```bash
cd /path/to/RiskAgentAnalyzer
python tests/run_integration_tests.py
```

### Issue: Async Test Failures

**Symptom**: `RuntimeError: Event loop is closed`

**Solution**: Use `asyncio.run()` in test methods:
```python
def test_async_workflow(self):
    async def run():
        result = await async_function()
        return result
    
    result = asyncio.run(run())
    self.assertIsNotNone(result)
```

### Issue: Mock Not Applied

**Symptom**: Tests attempt to access real APIs

**Solution**: Verify patch decorators are in correct order (bottom to top):
```python
@patch('module.ClassB')
@patch('module.ClassA')
def test_method(self, mock_a, mock_b):  # Parameters reverse order
    pass
```

### Issue: File System Conflicts

**Symptom**: Tests interfere with each other

**Solution**: Use `tempfile.mkdtemp()` in setUp, cleanup in tearDown:
```python
def setUp(self):
    self.test_dir = tempfile.mkdtemp()

def tearDown(self):
    if os.path.exists(self.test_dir):
        shutil.rmtree(self.test_dir)
```

## Best Practices

1. **Isolate External Dependencies**: Mock all external services (Git, LLM, file system)
2. **Use Realistic Data**: Create test data that matches production structures
3. **Test Error Paths**: Include negative test cases for error handling
4. **Measure Performance**: Document execution times for performance-critical paths
5. **Clean Up Resources**: Always cleanup temp files and directories
6. **Document Assumptions**: Comment why specific mock values are used
7. **Validate End-to-End**: Ensure complete workflow executes, not just units
8. **Test Integration Points**: Focus on component boundaries and data flow

## Integration Test Coverage

### Current Coverage

- ✅ Single repository analysis workflow
- ✅ Multi-repository analysis workflow
- ✅ Multi-language code review integration
- ✅ Report generation workflow
- ✅ LLM failure recovery
- ✅ Git API error handling
- ✅ Performance measurement

### Future Coverage

- 🔲 Database integration (if applicable)
- 🔲 Authentication workflows
- 🔲 Rate limiting behavior
- 🔲 Concurrent repository analysis
- 🔲 Large file handling
- 🔲 Network timeout scenarios
- 🔲 Cache integration

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run integration tests
        run: python tests/run_integration_tests.py
```

## Debugging Integration Tests

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Single Test with Debug

```bash
python -m pdb -m unittest tests.test_integration.TestFullAnalysisWorkflow.test_single_repository_analysis_workflow
```

### Print Mock Call Information

```python
print(f"Mock called {mock_object.call_count} times")
print(f"Call args: {mock_object.call_args_list}")
```

## Maintenance

- **Review quarterly**: Ensure tests match current system behavior
- **Update with features**: Add integration tests for new features
- **Monitor execution time**: Investigate tests that become slow
- **Refactor common mocks**: Extract reusable mock setups
- **Update documentation**: Keep this guide synchronized with code

## Contact

For questions about integration testing:
- Review test code in `tests/test_integration.py`
- Check test runner in `tests/run_integration_tests.py`
- Refer to unit test documentation in `tests/README.md`
