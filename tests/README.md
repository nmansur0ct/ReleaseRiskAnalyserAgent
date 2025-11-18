# Unit Tests Documentation

## Overview

Comprehensive unit test suite for the Risk Agent Analyzer framework covering all major components and scenarios.

## Test Structure

```
tests/
├── __init__.py                          # Tests package initialization
├── run_tests.py                         # Test runner script
├── test_base_code_agent.py             # Base agent functionality tests
├── test_code_review_orchestrator.py    # Orchestrator tests
├── test_comprehensive_reporter.py      # Reporter tests
├── test_llm_client.py                  # LLM client tests
└── test_utilities.py                   # Utility functions tests
```

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Test Module
```bash
python tests/run_tests.py test_base_code_agent
```

### Run Individual Test Class
```bash
python -m unittest tests.test_base_code_agent.TestBaseCodeReviewAgent
```

### Run Specific Test Method
```bash
python -m unittest tests.test_base_code_agent.TestBaseCodeReviewAgent.test_get_metadata
```

## Test Coverage

### 1. Base Code Agent Tests (`test_base_code_agent.py`)
- **Metadata generation**: Validates agent metadata creation
- **File filtering**: Tests extension-based file filtering
- **File path extraction**: Tests extracting paths from strings and dicts
- **File content retrieval**: Tests content extraction from PR data
- **JSON parsing**: Tests extracting JSON from various response formats
- **Fallback analysis**: Tests default analysis when LLM fails
- **Result aggregation**: Tests combining multiple file analyses
- **LLM integration**: Tests successful and failed LLM calls
- **Process workflow**: Tests end-to-end agent processing

**Key Test Scenarios:**
- Empty file lists
- Mixed file formats (strings and dictionaries)
- Missing content fallbacks
- Markdown code block parsing
- Error handling and recovery

### 2. Code Review Orchestrator Tests (`test_code_review_orchestrator.py`)
- **Initialization**: Tests orchestrator and agent setup
- **Repository info extraction**: Tests extracting repo URL and branch
- **Mode validation**: Tests valid and invalid code review modes
- **PR-only mode**: Tests analyzing only changed files
- **Full repo mode**: Tests analyzing entire repository
- **Agent execution**: Tests single and parallel agent runs
- **Error handling**: Tests graceful failure recovery
- **Integration workflow**: Tests complete code review process

### 3. Integration Tests (`test_integration.py`) - **NEW**
- **Full analysis workflow**: End-to-end single repository analysis
- **Multi-repository analysis**: Parallel processing of multiple repos
- **Multi-language code review**: Python, Java, JavaScript, React integration
- **Report generation**: Complete report creation and validation
- **Error handling**: LLM failure recovery and Git API error handling
- **Performance testing**: Parallel agent execution measurement

See `INTEGRATION_TESTING.md` for detailed documentation.

**Key Test Scenarios:**
- Multiple repository URL formats
- Default branch handling
- Invalid configuration modes
- Git manager integration
- Parallel agent execution

### 3. Comprehensive Reporter Tests (`test_comprehensive_reporter.py`)
- **Report generation**: Tests single and multi-repo reports
- **Section formatting**: Tests all report sections
- **Statistics calculation**: Tests summary metrics
- **JSON/AST parsing**: Tests agent response parsing
- **Table formatting**: Tests findings table generation
- **File management**: Tests report file creation
- **Content verification**: Tests report completeness

**Key Test Scenarios:**
- Single repository reports
- Multi-repository reports
- Empty findings
- Complex issue hierarchies
- Temporary file handling

### 4. LLM Client Tests (`test_llm_client.py`)
- **Initialization**: Tests client setup with env vars
- **PEM key loading**: Tests key file reading
- **Signature generation**: Tests authentication headers
- **Header generation**: Tests complete request headers
- **Successful calls**: Tests normal LLM interactions
- **Failed calls**: Tests error handling
- **Retry logic**: Tests automatic retries
- **Timeout handling**: Tests connection timeouts
- **Parameter passing**: Tests full parameter interface

**Key Test Scenarios:**
- Missing environment variables
- File not found errors
- Network failures
- Invalid JSON responses
- Rate limiting (429 errors)
- Connection timeouts

### 5. Utilities Tests (`test_utilities.py`)
- **Enums**: Tests RiskLevel and QualityClassification
- **Data structures**: Tests all dataclass creations
- **Configuration**: Tests logging and validation
- **Formatting**: Tests metric formatting functions
- **Edge cases**: Tests minimal and empty data

**Key Test Scenarios:**
- Enum value validation
- Dataclass field validation
- Logging level configuration
- Empty metrics formatting
- Missing optional fields

## Test Categories

### Unit Tests
- Test individual functions and methods in isolation
- Mock external dependencies (LLM, Git, file system)
- Fast execution (<1 second per test)
- No network calls or external services

### Integration Tests
- Test multiple components working together
- Mock only external services (LLM API, GitHub API)
- Verify data flow between components
- Test realistic workflows

### Edge Case Tests
- Empty inputs
- Null/None values
- Invalid configurations
- Missing required data
- Unexpected data formats

## Mocking Strategy

### External Dependencies Mocked:
- **LLM Client**: Mock API calls to avoid network dependency
- **Git Integration**: Mock repository access
- **File System**: Use temporary directories
- **Environment Variables**: Patch os.environ

### Not Mocked:
- Internal data structures
- Utility functions
- Pure business logic
- Data transformations

## Test Data Patterns

### Sample PR Data
```python
pr_data = {
    'files': [
        {'filename': 'app.py', 'full_content': 'code here'},
        {'filename': 'test.js', 'patch': '+new code'}
    ],
    'repository_url': 'https://github.com/user/repo.git',
    'base': {'ref': 'main'}
}
```

### Sample LLM Response
```python
llm_response = {
    'success': True,
    'response': '{"issues": [], "quality_score": 85}',
    'tokens_used': 100
}
```

## Adding New Tests

### 1. Create Test File
```python
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.instance = YourClass()
    
    def test_your_method(self):
        """Test description"""
        result = self.instance.your_method()
        self.assertEqual(result, expected_value)
```

### 2. Follow Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<method_name>_<scenario>`

### 3. Use Descriptive Docstrings
- Explain what the test validates
- Document expected behavior
- Note any edge cases

### 4. Mock External Dependencies
```python
from unittest.mock import Mock, patch

@patch('module.external_dependency')
def test_with_mock(self, mock_dep):
    mock_dep.return_value = 'mocked_value'
    # Your test code
```

## Best Practices

1. **Test Independence**: Each test should run independently
2. **Clear Assertions**: Use descriptive assertion messages
3. **Setup/Teardown**: Clean up resources in tearDown
4. **Mock External Calls**: Never make real API calls
5. **Fast Execution**: Keep tests under 1 second
6. **Coverage**: Aim for >80% code coverage
7. **Documentation**: Document complex test scenarios

## Continuous Integration

Tests should be run:
- Before every commit
- In CI/CD pipeline
- Before merging PRs
- After major refactoring

## Troubleshooting

### Import Errors
```bash
# Ensure parent directory is in path
export PYTHONPATH="${PYTHONPATH}:/path/to/RiskAgentAnalyzer"
```

### Mock Not Working
```python
# Use correct import path for patching
@patch('src.module.Class')  # Patch where it's imported
not @patch('original.module.Class')  # Not where it's defined
```

### Async Test Failures
```python
# Use asyncio.run() for async tests
import asyncio

def test_async_method(self):
    async def run_test():
        result = await self.async_method()
        self.assertEqual(result, expected)
    
    asyncio.run(run_test())
```

## Future Enhancements

- [ ] Add performance benchmarks
- [ ] Implement coverage reporting
- [ ] Add mutation testing
- [ ] Create integration test suite
- [ ] Add property-based testing
- [ ] Implement test data generators
- [ ] Add stress tests for concurrent execution

## Contact

For test-related questions or issues, refer to the main project README or contact the development team.
