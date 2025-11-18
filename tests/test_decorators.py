"""
Test Metadata Decorators

Decorators to add metadata to test cases for enhanced reporting.
"""

import functools

def test_scenario(scenario_name, description="", category="Unit Tests"):
    """
    Decorator to add scenario metadata to a test class
    
    Args:
        scenario_name: Name of the test scenario
        description: Description of what the scenario tests
        category: Category of tests (Unit Tests, Integration Tests, etc.)
    
    Example:
        @test_scenario("User Authentication", "Tests user login and logout", "Integration Tests")
        class TestUserAuth(unittest.TestCase):
            pass
    """
    def decorator(cls):
        cls._test_scenario = scenario_name
        cls._scenario_description = description
        cls._test_category = category
        return cls
    return decorator

def test_case(name, description, expected_result):
    """
    Decorator to add metadata to individual test methods
    
    Args:
        name: Friendly name for the test case
        description: Detailed description of what is being tested
        expected_result: Description of the expected outcome
    
    Example:
        @test_case(
            name="Valid Login",
            description="User provides valid credentials",
            expected_result="User is authenticated and redirected to dashboard"
        )
        def test_valid_login(self):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        
        wrapper._test_case_name = name
        wrapper._test_description = description
        wrapper._expected_result = expected_result
        
        return wrapper
    return decorator

def test_data(data_description, test_data):
    """
    Decorator to add test data metadata
    
    Args:
        data_description: Description of the test data
        test_data: The actual test data
    
    Example:
        @test_data("Valid user credentials", {"username": "test", "password": "pass123"})
        def test_login(self):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        
        wrapper._test_data_description = data_description
        wrapper._test_data = test_data
        
        return wrapper
    return decorator

def performance_test(max_execution_time_ms=1000):
    """
    Decorator to mark a test as performance-sensitive
    
    Args:
        max_execution_time_ms: Maximum acceptable execution time in milliseconds
    
    Example:
        @performance_test(max_execution_time_ms=500)
        def test_fast_operation(self):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            import time
            start = time.time()
            result = func(self, *args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            if duration_ms > max_execution_time_ms:
                self.fail(f"Performance test failed: {duration_ms:.2f}ms > {max_execution_time_ms}ms")
            
            return result
        
        wrapper._is_performance_test = True
        wrapper._max_execution_time_ms = max_execution_time_ms
        
        return wrapper
    return decorator

def integration_test(dependencies=None, requires_external_service=False):
    """
    Decorator to mark a test as an integration test
    
    Args:
        dependencies: List of systems/services this test depends on
        requires_external_service: Whether test requires external services
    
    Example:
        @integration_test(dependencies=["Database", "API"], requires_external_service=True)
        def test_data_sync(self):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        
        wrapper._is_integration_test = True
        wrapper._test_dependencies = dependencies or []
        wrapper._requires_external_service = requires_external_service
        
        return wrapper
    return decorator

def critical_test(severity="HIGH"):
    """
    Decorator to mark a test as critical
    
    Args:
        severity: Severity level (HIGH, MEDIUM, LOW)
    
    Example:
        @critical_test(severity="HIGH")
        def test_payment_processing(self):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        
        wrapper._is_critical = True
        wrapper._severity = severity
        
        return wrapper
    return decorator

# Helper function to extract metadata from test
def get_test_metadata(test):
    """Extract all metadata from a test method and class"""
    metadata = {}
    
    # Get test class metadata
    test_class = test.__class__
    metadata['scenario'] = getattr(test_class, '_test_scenario', test_class.__name__)
    metadata['scenario_description'] = getattr(test_class, '_scenario_description', test_class.__doc__ or "")
    metadata['category'] = getattr(test_class, '_test_category', 'Unit Tests')
    
    # Get test method metadata
    test_method = getattr(test, test._testMethodName)
    metadata['name'] = getattr(test_method, '_test_case_name', test._testMethodName)
    metadata['description'] = getattr(test_method, '_test_description', test._testMethodDoc or "")
    metadata['expected_result'] = getattr(test_method, '_expected_result', 'Test should pass without errors')
    
    # Additional metadata
    metadata['is_performance_test'] = getattr(test_method, '_is_performance_test', False)
    metadata['is_integration_test'] = getattr(test_method, '_is_integration_test', False)
    metadata['is_critical'] = getattr(test_method, '_is_critical', False)
    metadata['test_data'] = getattr(test_method, '_test_data', None)
    
    return metadata
