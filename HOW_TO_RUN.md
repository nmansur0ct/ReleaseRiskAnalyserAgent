# How to Run the Release Risk Analyzer

This guide provides step-by-step instructions for running the Release Risk Analyzer plugin-based framework.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **Git** for cloning the repository
- **Environment variables** for LLM integration (optional)

### 1. Clone the Repository

```bash
# Clone from Walmart GitHub
git clone https://gecgithub01.walmart.com/n0m08hp/RiskAnalyzerAgent.git
cd RiskAnalyzerAgent

# OR clone from public GitHub
git clone https://github.com/nmansur0ct/ReleaseRiskAnalyserAgent.git
cd ReleaseRiskAnalyserAgent
```

### 2. Install Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt

# OR use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Demo

```bash
# Navigate to source directory
cd src

# Run the interactive demonstration
python simple_demo.py
```

**Expected Output:**
```
🚀 Plugin Framework Architecture Demonstration
================================================================================

📋 Analyzing PR: Add user authentication and payment processing
📁 Files changed: 7
📊 Changes: +342 -28

🔄 Executing Plugin-Based Risk Analysis...
------------------------------------------------------------
🔍 Change Log Summarizer
   Summary: Modified 7 files with authentication and payment features
   Modules: auth, payments, api, database
   Size: LARGE
   Risk Areas: security, database, api
   ⏱️  Execution Time: 2.60s

🔍 Security Analyzer
   Security Score: 45 - 🟠 LOW
   Findings: 3 issues detected
   Recommendation: Additional security validation recommended
   ⏱️  Execution Time: 2.20s
```

## 🔧 Configuration Setup

### Environment Variables (Optional)

For LLM integration, set up environment variables:

```bash
# OpenAI (Primary LLM provider)
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic (Fallback LLM provider)
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Slack notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"

# Email notifications
export SMTP_PASSWORD="your-smtp-password"
```

### Configuration Files

Choose a configuration based on your environment:

#### Development Environment
```bash
# Use minimal configuration for testing
cp config/development_config.yaml config/active_config.yaml
```

#### Basic Setup
```bash
# Use standard configuration
cp config/basic_config.yaml config/active_config.yaml
```

#### Enterprise Setup
```bash
# Use full enterprise features
cp config/enterprise_config.yaml config/active_config.yaml
```

## 🎯 Running Different Scenarios

### 1. Basic Demo (No LLM Required)

```bash
cd src
python simple_demo.py
```

This runs a simulation with realistic plugin execution without requiring LLM APIs.

### 2. Interactive Plugin Demo

```bash
cd src
python plugin_demo.py
```

Note: This requires fixing the import issues first (see Troubleshooting section).

### 3. Custom Configuration

```bash
# Create your own configuration
cp config/basic_config.yaml config/my_config.yaml
# Edit config/my_config.yaml with your settings

# Run with custom config
python simple_demo.py --config ../config/my_config.yaml
```

## 📊 Understanding the Output

### Plugin Execution Flow

1. **Change Log Summarizer**
   - Analyzes PR content and generates summary
   - Identifies affected modules and risk areas
   - Provides change size classification

2. **Security Analyzer**
   - Scans for security vulnerabilities
   - Generates risk score (0-100)
   - Provides security recommendations

3. **Compliance Checker**
   - Validates against regulatory standards
   - Checks SOX, GDPR, HIPAA compliance
   - Identifies required approvals

4. **Release Decision Agent**
   - Makes go/no-go decision
   - Provides detailed rationale
   - Lists required approvals

5. **Notification Agent**
   - Sends results to configured channels
   - Supports Slack, Email, Webhook

### Output Interpretation

#### Risk Levels
- 🟢 **MINIMAL** (0-24): Low risk, likely approved
- 🟠 **LOW** (25-49): Some concerns, review recommended
- 🟡 **MEDIUM** (50-74): Significant concerns, approval required
- 🔴 **HIGH** (75-100): Major risks, extensive review needed

#### Decision Status
- ✅ **APPROVED**: Release can proceed
- 🚫 **BLOCKED**: Manual review required
- ⏳ **PENDING**: Waiting for approvals

## 🔌 Running with Real LLM Integration

### 1. Set Up LLM API Keys

```bash
# Get API keys from providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Configure LLM Settings

Edit your configuration file:

```yaml
plugins:
  change_log_summarizer:
    enabled: true
    config:
      llm_provider: "openai"  # or "anthropic"
      confidence_threshold: 0.7
      fallback_provider: "anthropic"
```

### 3. Run with LLM Analysis

```bash
# The framework will automatically use LLM if API keys are available
python simple_demo.py
```

## 🔧 Configuration Options

### Plugin Configuration

#### Enable/Disable Plugins
```yaml
plugins:
  security_analyzer:
    enabled: true    # Enable this plugin
  compliance_checker:
    enabled: false   # Disable this plugin
```

#### Plugin-Specific Settings
```yaml
plugins:
  security_analyzer:
    config:
      scan_types:
        - "secret_detection"
        - "vulnerability_scan"
      severity_threshold: "medium"
      custom_patterns:
        api_keys: "(api_key|apikey).*"
```

### Execution Modes

#### Sequential Execution
```yaml
workflow:
  execution_mode: "sequential"
```
Plugins run one after another.

#### Parallel Execution
```yaml
workflow:
  execution_mode: "parallel"
```
Compatible plugins run simultaneously.

#### Hybrid Execution (Recommended)
```yaml
workflow:
  execution_mode: "hybrid"
```
Optimal mix of sequential and parallel execution.

### Global Settings

```yaml
global_config:
  log_level: "INFO"           # DEBUG, INFO, WARNING, ERROR
  max_parallel_agents: 3      # Limit concurrent plugins
  enable_metrics: true        # Enable performance metrics
  hot_reload: true            # Enable configuration hot-reload
  cache_enabled: true         # Enable result caching
```

## 🧪 Testing Different Scenarios

### 1. High-Risk PR Simulation

Modify the sample data in `simple_demo.py`:

```python
sample_pr_data = {
    "title": "Emergency security patch with database schema changes",
    "changed_files": [
        "src/auth/security.py",
        "src/database/schema.sql", 
        "src/payments/processor.py",
        "config/production.yml"
    ],
    "additions": 847,
    "deletions": 234
}
```

### 2. Low-Risk PR Simulation

```python
sample_pr_data = {
    "title": "Update documentation and fix typos",
    "changed_files": [
        "README.md",
        "docs/user_guide.md"
    ],
    "additions": 23,
    "deletions": 8
}
```

### 3. Compliance-Focused Testing

```python
sample_pr_data = {
    "title": "Add customer data processing for GDPR compliance",
    "body": "Implements data retention policies and customer consent management",
    "changed_files": [
        "src/privacy/gdpr_handler.py",
        "src/customer/data_processor.py"
    ]
}
```

## 🔍 Advanced Usage

### 1. Custom Plugin Development

Create a new plugin:

```python
# src/my_custom_plugin.py
from plugin_framework import BaseAgentPlugin, AgentMetadata, AgentInput, AgentOutput

class MyCustomPlugin(BaseAgentPlugin):
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="my_custom_plugin",
            version="1.0.0",
            capabilities=[AgentCapability.ANALYSIS]
        )
    
    async def process(self, input_data: AgentInput, state) -> AgentOutput:
        # Your analysis logic
        return AgentOutput(
            result={"custom_analysis": "completed"},
            session_id=input_data.session_id
        )
```

Add to configuration:

```yaml
plugins:
  my_custom_plugin:
    enabled: true
    config:
      custom_setting: "value"
```

### 2. Integration with CI/CD

#### GitHub Actions Integration

```yaml
# .github/workflows/risk-analysis.yml
name: Release Risk Analysis
on:
  pull_request:
    branches: [main]

jobs:
  risk-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Risk Analysis
        run: |
          cd src
          python analyze_pr.py --pr-url ${{ github.event.pull_request.url }}
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

#### Jenkins Integration

```groovy
pipeline {
    agent any
    stages {
        stage('Risk Analysis') {
            steps {
                script {
                    sh '''
                        cd src
                        python analyze_pr.py --pr-data "${PR_DATA}"
                    '''
                }
            }
        }
    }
}
```

### 3. API Integration

Create a REST API wrapper:

```python
# api_server.py
from fastapi import FastAPI
from plugin_framework import WorkflowOrchestrator

app = FastAPI()

@app.post("/analyze")
async def analyze_pr(pr_data: dict):
    orchestrator = WorkflowOrchestrator()
    result = await orchestrator.analyze(pr_data)
    return result
```

Run the API:

```bash
pip install fastapi uvicorn
uvicorn api_server:app --reload
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError` when running scripts

**Solution**:
```bash
# Ensure you're in the right directory
cd /path/to/ReleaseRiskAnalyserAgent/src

# Check Python path
export PYTHONPATH=/path/to/ReleaseRiskAnalyserAgent/src:$PYTHONPATH
```

#### 2. Configuration Not Found

**Problem**: `FileNotFoundError: config/basic_config.yaml`

**Solution**:
```bash
# Run from project root, not src directory
cd /path/to/ReleaseRiskAnalyserAgent
python src/simple_demo.py

# Or use absolute path
python src/simple_demo.py --config /absolute/path/to/config.yaml
```

#### 3. LLM API Errors

**Problem**: `Authentication Error` or `Rate Limit Exceeded`

**Solution**:
```bash
# Check API key is set
echo $OPENAI_API_KEY

# Use fallback to heuristic analysis
export LLM_ENABLED=false

# Or use development config with mock LLM
cp config/development_config.yaml config/active_config.yaml
```

#### 4. Plugin Not Loading

**Problem**: Plugin not appearing in execution

**Solution**:
```yaml
# Check plugin is enabled in config
plugins:
  my_plugin:
    enabled: true  # Make sure this is true

# Check plugin name matches exactly
# Names are case-sensitive
```

#### 5. Permission Errors

**Problem**: `Permission denied` when accessing files

**Solution**:
```bash
# Check file permissions
ls -la config/

# Fix permissions if needed
chmod 644 config/*.yaml
chmod 755 src/*.py
```

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python src/simple_demo.py
```

Or in configuration:

```yaml
global_config:
  log_level: "DEBUG"
```

### Performance Issues

If plugins run slowly:

```yaml
global_config:
  max_parallel_agents: 1    # Reduce parallelism
  cache_enabled: true       # Enable caching
  timeout_seconds: 60       # Reduce timeout
```

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.8+
- **RAM**: 512MB
- **Disk**: 100MB

### Recommended Requirements
- **Python**: 3.9+
- **RAM**: 2GB (for LLM integration)
- **Disk**: 1GB
- **Network**: Stable internet (for LLM APIs)

### Optional Dependencies

For enhanced features:

```bash
# Redis for caching
pip install redis

# PostgreSQL for data persistence
pip install psycopg2-binary

# Monitoring
pip install prometheus-client

# Additional LLM providers
pip install anthropic cohere
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "src/api_server.py"]
```

```bash
# Build and run
docker build -t risk-analyzer .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key risk-analyzer
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: risk-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: risk-analyzer
  template:
    spec:
      containers:
      - name: risk-analyzer
        image: risk-analyzer:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-key
```

## 💡 Tips and Best Practices

### 1. Configuration Management
- Use environment-specific configs
- Keep secrets in environment variables
- Version control your configuration files

### 2. Plugin Development
- Follow the BaseAgentPlugin interface
- Include comprehensive error handling
- Add unit tests for your plugins

### 3. Performance Optimization
- Enable caching for repeated analysis
- Use parallel execution where possible
- Monitor plugin execution times

### 4. Security
- Never commit API keys to version control
- Use secure credential management
- Regularly update dependencies

### 5. Monitoring
- Enable metrics collection
- Set up alerts for failures
- Monitor plugin performance

## 📚 Next Steps

1. **Explore the demo**: Run `python src/simple_demo.py`
2. **Read the documentation**: Check `PLUGIN_FRAMEWORK_GUIDE.md`
3. **Customize configuration**: Edit config files for your needs
4. **Develop plugins**: Create custom analysis plugins
5. **Integrate with CI/CD**: Set up automated PR analysis

## 🆘 Getting Help

- **Documentation**: Check the `docs/` directory
- **Examples**: Review `src/example_plugins.py`
- **Issues**: Open GitHub issues for bugs
- **Configuration**: Try different config files

---

**Ready to analyze your first pull request? Run the demo and explore the plugin framework!** 🚀