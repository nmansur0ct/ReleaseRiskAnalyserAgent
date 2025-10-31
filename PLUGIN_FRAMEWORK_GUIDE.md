# Plugin Framework User Guide

## Overview

The Release Risk Analyzer now uses a modular plugin-based architecture that makes adding new analysis agents simple and configurable. This guide shows you how to use, configure, and extend the framework.

## Quick Start

### 1. Running the Demo

```bash
# Run the simple demonstration
cd src
python simple_demo.py
```

This shows how the plugin system works with simulated analysis results.

### 2. Basic Configuration

The framework uses YAML configuration files to define which plugins to run and how to configure them:

```yaml
# config/basic_config.yaml
workflow:
  name: "basic_risk_analysis"
  version: "2.0.0"
  execution_mode: "sequential_with_parallel"

plugins:
  change_log_summarizer:
    enabled: true
    config:
      llm_provider: "openai"
      confidence_threshold: 0.7

  security_analyzer:
    enabled: true
    config:
      scan_types: ["secret_detection", "vulnerability_scan"]
      severity_threshold: "medium"

  notification_agent:
    enabled: true
    config:
      channels: ["slack", "email"]
```

### 3. Available Configurations

- **`config/basic_config.yaml`** - Simple setup with core plugins
- **`config/enterprise_config.yaml`** - Full enterprise features with compliance
- **`config/development_config.yaml`** - Minimal config for development

## Core Concepts

### Plugin Architecture

Every analysis capability is implemented as a plugin that inherits from `BaseAgentPlugin`:

```python
class MyCustomPlugin(BaseAgentPlugin):
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="my_custom_plugin",
            version="1.0.0",
            description="Custom analysis logic",
            capabilities=[AgentCapability.ANALYSIS],
            execution_priority=20
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        # Your analysis logic here
        return AgentOutput(
            result={"analysis": "results"},
            confidence=0.9,
            session_id=input_data.session_id
        )
```

### Configuration-Driven

Plugins are enabled, disabled, and configured through YAML files:

```yaml
plugins:
  my_custom_plugin:
    enabled: true
    config:
      api_endpoint: "https://api.example.com"
      timeout: 30
      custom_rules:
        - "rule1"
        - "rule2"
```

### Dependency Management

Plugins can depend on other plugins to ensure execution order:

```python
AgentMetadata(
    name="decision_agent",
    dependencies=["security_analyzer", "compliance_checker"],
    execution_priority=80
)
```

### Parallel Execution

Plugins can run in parallel if they don't depend on each other:

```python
AgentMetadata(
    execution_mode=ExecutionMode.PARALLEL,
    parallel_compatible=True
)
```

## Built-in Plugins

### 1. ChangeLogSummarizerPlugin

**Purpose**: Analyzes PR changes and generates intelligent summaries

**Configuration**:
```yaml
change_log_summarizer:
  enabled: true
  config:
    llm_provider: "openai"          # LLM provider for analysis
    confidence_threshold: 0.7       # Minimum confidence for LLM results
    analysis_depth: "comprehensive" # basic, standard, comprehensive
    fallback_provider: "anthropic"  # Fallback if primary fails
```

**Output**:
- Change summary
- Affected modules
- Change size classification
- Risk indicators

### 2. SecurityAnalyzerPlugin

**Purpose**: Performs security analysis on code changes

**Configuration**:
```yaml
security_analyzer:
  enabled: true
  config:
    scan_types:
      - "secret_detection"     # Find hardcoded secrets
      - "vulnerability_scan"   # Check for known vulnerabilities
      - "dependency_check"     # Analyze dependency security
    severity_threshold: "medium"  # low, medium, high, critical
    custom_patterns:
      api_keys: "(api_key|apikey).*['\"][A-Za-z0-9]{20,}['\"]"
```

**Output**:
- Security score (0-100)
- Security findings by category
- Recommendations

### 3. CustomCompliancePlugin

**Purpose**: Validates compliance with regulatory standards

**Configuration**:
```yaml
custom_compliance_checker:
  enabled: true
  config:
    standards: ["SOX", "GDPR", "HIPAA"]
    custom_rules:
      financial_review:
        file_patterns: ["*financial*", "*billing*"]
        required_approvers: ["finance_team"]
```

**Output**:
- Overall compliance status
- Standard-specific results
- Required approvals

### 4. NotificationAgentPlugin

**Purpose**: Sends analysis results to various channels

**Configuration**:
```yaml
notification_agent:
  enabled: true
  config:
    channels: ["slack", "email", "webhook"]
    slack_config:
      webhook_url: "${SLACK_WEBHOOK_URL}"
      channel: "#releases"
    email_config:
      smtp_server: "smtp.company.com"
      recipients: ["devops@company.com"]
```

**Output**:
- Notification delivery status
- Channels used

## Adding New Plugins

### Step 1: Create Plugin Class

Create a new Python file in `src/` or a custom plugins directory:

```python
# src/my_plugin.py
from plugin_framework import BaseAgentPlugin, AgentMetadata, AgentInput, AgentOutput

class MyAnalysisPlugin(BaseAgentPlugin):
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="my_analysis_plugin",
            version="1.0.0",
            description="Custom analysis for specific needs",
            capabilities=[AgentCapability.ANALYSIS],
            dependencies=[],  # List other plugins this depends on
            execution_priority=30,  # 1-100 (lower = earlier)
            required_config={
                "api_key": str,
                "threshold": float
            },
            optional_config={
                "timeout": int,
                "custom_rules": list
            }
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        # Access configuration
        api_key = self.config.get("api_key")
        threshold = self.config.get("threshold")
        
        # Access PR data
        pr_data = input_data.data
        changed_files = pr_data.get("changed_files", [])
        
        # Perform your analysis
        analysis_result = await self.perform_analysis(changed_files, api_key)
        
        # Return results
        return AgentOutput(
            result={
                "analysis_type": "custom",
                "findings": analysis_result,
                "confidence": 0.95
            },
            confidence=0.95,
            analysis_method="custom_api",
            session_id=input_data.session_id
        )
    
    async def perform_analysis(self, files, api_key):
        # Your custom analysis logic
        return {"status": "analyzed", "file_count": len(files)}
```

### Step 2: Add Configuration

Add your plugin to the YAML configuration:

```yaml
plugins:
  my_analysis_plugin:
    enabled: true
    config:
      api_key: "${MY_API_KEY}"  # Use environment variables
      threshold: 0.8
      timeout: 60
      custom_rules:
        - "check_naming_conventions"
        - "validate_documentation"
```

### Step 3: Register Plugin

Add registration code to your application:

```python
from my_plugin import MyAnalysisPlugin

# Register with framework
plugin = MyAnalysisPlugin(config)
await registry.register_agent(plugin)
```

### Step 4: Test Plugin

Run with your configuration:

```bash
python src/simple_demo.py  # For basic testing
```

## Advanced Features

### Environment Variables

Use environment variables in configuration:

```yaml
plugins:
  security_analyzer:
    config:
      api_key: "${SECURITY_API_KEY}"
      webhook_url: "${WEBHOOK_URL}"
```

Set environment variables:
```bash
export SECURITY_API_KEY="your-api-key"
export WEBHOOK_URL="https://hooks.slack.com/services/xxx"
```

### Hot Reload

Configuration changes are automatically detected:

```yaml
global_config:
  hot_reload: true
  reload_interval: 30  # seconds
```

### Parallel Execution Groups

Control which plugins run in parallel:

```yaml
workflow:
  execution_mode: "hybrid"  # sequential, parallel, hybrid

plugins:
  security_analyzer:
    config:
      execution_mode: "parallel"
  
  compliance_checker:
    config:
      execution_mode: "parallel"
      
  notification_agent:
    config:
      execution_mode: "sequential"  # Runs after analysis plugins
```

### Custom Plugin Paths

Load plugins from custom directories:

```yaml
global_config:
  custom_plugins_path: "/path/to/custom/plugins"

plugins:
  custom_business_rules:
    enabled: true
    plugin_path: "/custom/plugins/business_rules.py"
    class_name: "BusinessRulesPlugin"
```

### Error Handling

Plugins can return errors without stopping the workflow:

```python
async def process(self, input_data: AgentInput, state) -> AgentOutput:
    try:
        result = await risky_operation()
        return AgentOutput(result=result, session_id=input_data.session_id)
    except Exception as e:
        return AgentOutput(
            result={},
            errors=[f"Analysis failed: {str(e)}"],
            session_id=input_data.session_id
        )
```

### State Sharing

Plugins can share data through the state object:

```python
async def process(self, input_data: AgentInput, state) -> AgentOutput:
    # Read from state
    previous_analysis = getattr(state, 'analysis_results', {})
    
    # Perform analysis
    result = self.analyze_with_context(input_data.data, previous_analysis)
    
    # State is automatically updated with your results
    return AgentOutput(result=result, session_id=input_data.session_id)
```

## Configuration Examples

### Simple Development Setup

```yaml
# config/dev.yaml
workflow:
  name: "dev_analysis"
  execution_mode: "sequential"

plugins:
  change_log_summarizer:
    enabled: true
    config:
      llm_provider: "mock"  # Use mock for testing
      
global_config:
  log_level: "DEBUG"
  hot_reload: true
```

### Production Enterprise Setup

```yaml
# config/production.yaml
workflow:
  name: "enterprise_risk_analysis"
  execution_mode: "hybrid"
  timeout_seconds: 600

plugins:
  change_log_summarizer:
    enabled: true
    config:
      llm_provider: "openai"
      fallback_provider: "anthropic"
      confidence_threshold: 0.8

  security_analyzer:
    enabled: true
    config:
      scan_types: ["secret_detection", "vulnerability_scan", "static_analysis"]
      
  custom_compliance_checker:
    enabled: true
    config:
      standards: ["SOX", "GDPR", "HIPAA", "PCI_DSS"]
      
  notification_agent:
    enabled: true
    config:
      channels: ["slack", "email", "jira"]

global_config:
  log_level: "INFO"
  enable_metrics: true
  cache_enabled: true
  tracing_enabled: true
```

## Troubleshooting

### Plugin Not Loading

Check that:
1. Plugin class inherits from `BaseAgentPlugin`
2. Required methods are implemented
3. Plugin is properly configured in YAML
4. Dependencies are satisfied

### Configuration Errors

Validate your YAML:
```python
import yaml

with open('config/my_config.yaml') as f:
    config = yaml.safe_load(f)
    print("Configuration loaded successfully")
```

### Plugin Execution Failures

Check logs for specific error messages:
```bash
# Set debug logging
export LOG_LEVEL=DEBUG
python src/simple_demo.py
```

## Best Practices

### Plugin Design

1. **Single Responsibility**: Each plugin should have one clear purpose
2. **Fail Gracefully**: Handle errors without crashing the workflow  
3. **Configuration Validation**: Validate all required configuration
4. **Async Operations**: Use async/await for I/O operations
5. **State Management**: Use state object for sharing data between plugins

### Configuration Management

1. **Environment Variables**: Use for sensitive data
2. **Validation**: Validate configuration on startup
3. **Documentation**: Document all configuration options
4. **Defaults**: Provide sensible defaults for optional config

### Testing

1. **Unit Tests**: Test plugin logic in isolation
2. **Integration Tests**: Test with real workflow
3. **Mock Services**: Use mocks for external dependencies
4. **Configuration Tests**: Test different config scenarios

## API Reference

See `src/plugin_framework.py` for complete API documentation including:

- `BaseAgentPlugin` - Base class for all plugins
- `AgentMetadata` - Plugin metadata definition
- `AgentInput/AgentOutput` - Input/output data structures
- `AgentPluginRegistry` - Plugin registration and management
- `ConfigurationManager` - Configuration loading and hot-reload
- `WorkflowOrchestrator` - Plugin execution coordination

## Examples

Complete working examples are provided in:

- `src/example_plugins.py` - Example plugin implementations
- `config/` - Configuration file examples
- `src/simple_demo.py` - Working demonstration

## Support

For questions or issues:

1. Check the Architecture.md for design details
2. Review example plugins for implementation patterns
3. Test with different configuration files
4. Check logs for specific error messages