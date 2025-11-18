# How to Run Risk Agent Analyzer

## Overview

This guide provides complete instructions for setting up, configuring, and running the Risk Agent Analyzer in various environments and use cases.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM, Recommended 4GB+ for large repositories
- **Storage**: 500MB for installation, additional space for reports
- **Network**: Internet access for LLM API calls and Git repository access

### Required Accounts/Access
- **LLM Provider**: Walmart LLM Gateway credentials (or alternative provider)
- **Git Access**: GitHub token for repository analysis
- **Optional**: GitHub Enterprise access for enterprise repositories

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd RiskAgentAnalyzer
```

### 2. Set Up Python Environment

#### Option A: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Option B: Conda Environment
```bash
# Create conda environment
conda create -n risk-analyzer python=3.9
conda activate risk-analyzer
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
python -c "import src.integration.llm_client; print('Installation successful')"
```

### 4. Install Package (Optional)

For system-wide access:
```bash
pip install .
```

## Configuration

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Required Environment Variables

```bash
# === LLM Configuration ===
LLM_PROVIDER=walmart_gateway
LLM_API_KEY=your_api_key_here
WM_CONSUMER_ID=your_consumer_id
WM_SVC_NAME=your_service_name
WM_SVC_ENV=production

# === GitHub Configuration ===
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_API_BASE=https://api.github.com  # For public GitHub
# GITHUB_API_BASE=https://gecgithub01.walmart.com/api/v3  # For GitHub Enterprise

# === Analysis Configuration ===
CODE_REVIEW_MODE=full_repo  # Options: full_repo, pr_only
PR_STATE=open              # Options: open, closed, all
PR_LIMIT=10               # Number of PRs to analyze
OUTPUT_DIR=./reports      # Report output directory

# === Optional Configuration ===
LOG_LEVEL=INFO            # Options: DEBUG, INFO, WARNING, ERROR
TIMEOUT_SECONDS=300       # Analysis timeout
MAX_FILE_SIZE=1048576     # Max file size in bytes (1MB)
```

### 3. Verify Configuration

```bash
# Test LLM connection
python -c "
from src.integration.llm_client import LLMClient
client = LLMClient()
print('LLM client configured successfully')
"

# Test GitHub connection  
python -c "
import os
import requests
token = os.getenv('GITHUB_TOKEN')
response = requests.get('https://api.github.com/user', 
                       headers={'Authorization': f'token {token}'})
print(f'GitHub API Status: {response.status_code}')
"
```

## Running the Analyzer

### 1. Basic Usage

#### Single Repository Analysis
```bash
python risk_analyzer.py https://github.com/user/repository.git
```

#### Multiple Repository Analysis
```bash
python risk_analyzer.py \
  https://github.com/user/repo1.git \
  https://github.com/user/repo2.git \
  https://github.com/user/repo3.git
```

### 2. Advanced Usage Options

#### Custom Configuration
```bash
python risk_analyzer.py https://github.com/user/repo.git \
  --pr-limit 20 \
  --pr-state all \
  --output-dir ./custom-reports \
  --log-level DEBUG
```

#### Full Repository Analysis Mode
```bash
# Set in .env file
CODE_REVIEW_MODE=full_repo

python risk_analyzer.py https://github.com/user/repo.git
```

#### PR-Only Analysis Mode
```bash
# Set in .env file  
CODE_REVIEW_MODE=pr_only

python risk_analyzer.py https://github.com/user/repo.git
```

### 3. Command Line Options

```bash
python risk_analyzer.py --help
```

Available options:
- `--pr-limit N`: Limit number of PRs to analyze (default: 10)
- `--pr-state STATE`: PR state filter (open, closed, all) (default: open)
- `--output-dir DIR`: Output directory for reports (default: ./reports)
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR) (default: INFO)
- `--timeout SECONDS`: Analysis timeout in seconds (default: 300)
- `--help`: Show help message

## Usage Examples

### 1. Enterprise Repository Analysis

```bash
# Analyze enterprise GitHub repository
export GITHUB_API_BASE=https://gecgithub01.walmart.com/api/v3
export GITHUB_TOKEN=your_enterprise_token

python risk_analyzer.py https://gecgithub01.walmart.com/team/project.git \
  --pr-limit 50 \
  --pr-state all \
  --output-dir ./enterprise-reports
```

### 2. CI/CD Integration

#### GitHub Actions Workflow
Create `.github/workflows/risk-analysis.yml`:

```yaml
name: Repository Risk Analysis
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 9 * * 1'  # Weekly Monday 9 AM

jobs:
  risk-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run Risk Analysis
      run: |
        python risk_analyzer.py ${{ github.repositoryUrl }}
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
        WM_CONSUMER_ID: ${{ secrets.WM_CONSUMER_ID }}
        WM_SVC_NAME: ${{ secrets.WM_SVC_NAME }}
        WM_SVC_ENV: ${{ secrets.WM_SVC_ENV }}
        
    - name: Upload Report
      uses: actions/upload-artifact@v3
      with:
        name: risk-analysis-report
        path: reports/
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        LLM_API_KEY = credentials('llm-api-key')
        GITHUB_TOKEN = credentials('github-token')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'python -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }
        
        stage('Risk Analysis') {
            steps {
                sh '''
                . venv/bin/activate
                python risk_analyzer.py ${GIT_URL} \
                  --pr-limit 25 \
                  --output-dir ./reports
                '''
            }
        }
        
        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'reports/*.txt', allowEmptyArchive: true
            }
        }
    }
}
```

### 3. Batch Processing Script

Create `scripts/batch_analysis.sh`:

```bash
#!/bin/bash

# Batch analysis script for multiple repositories
REPOS=(
    "https://github.com/org/repo1.git"
    "https://github.com/org/repo2.git" 
    "https://github.com/org/repo3.git"
)

OUTPUT_BASE="./batch-reports-$(date +%Y%m%d)"
mkdir -p "$OUTPUT_BASE"

for repo in "${REPOS[@]}"; do
    repo_name=$(basename "$repo" .git)
    echo "Analyzing $repo_name..."
    
    python risk_analyzer.py "$repo" \
      --output-dir "$OUTPUT_BASE/$repo_name" \
      --pr-limit 15 \
      --log-level INFO
    
    if [ $? -eq 0 ]; then
        echo "✓ $repo_name analysis completed"
    else
        echo "✗ $repo_name analysis failed"
    fi
done

echo "Batch analysis complete. Reports in $OUTPUT_BASE"
```

Make executable and run:
```bash
chmod +x scripts/batch_analysis.sh
./scripts/batch_analysis.sh
```

### 4. Programmatic Usage

```python
import asyncio
import os
from risk_analyzer import RiskAgentAnalyzer
from src.utilities.config_utils import setup_logging, load_configuration

async def custom_analysis():
    """Custom analysis workflow"""
    
    # Setup logging
    setup_logging('INFO')
    
    # Load configuration
    config = load_configuration()
    
    # Override configuration
    config.update({
        'pr_limit': 25,
        'pr_state': 'all',
        'code_review_mode': 'full_repo',
        'output_dir': './custom-analysis'
    })
    
    # Initialize analyzer
    analyzer = RiskAgentAnalyzer()
    
    # Define repositories to analyze
    repositories = [
        "https://github.com/user/critical-service.git",
        "https://github.com/user/data-pipeline.git",
        "https://github.com/user/web-frontend.git"
    ]
    
    # Run analysis
    try:
        results = await analyzer.analyze_repositories(repositories, config)
        
        print(f"Analysis completed for {len(results)} repositories")
        for result in results:
            print(f"- {result.repository_name}: {result.quality_classification}")
            
    except Exception as e:
        print(f"Analysis failed: {e}")

# Run the custom analysis
if __name__ == "__main__":
    asyncio.run(custom_analysis())
```

## Output and Reports

### 1. Report Location

Reports are saved to the configured output directory (default: `./reports/`):

```
reports/
├── comprehensive_summary_repo-name_20251117_143025.txt
├── comprehensive_summary_repo-name_20251117_143156.txt
└── ...
```

### 2. Report Structure

Each report contains 5 comprehensive sections:

1. **Executive Summary**: High-level repository health assessment
2. **Git Repository Details**: Branch information, contributor stats, PR metadata
3. **Pull Request Analysis**: Individual PR risk assessments and metrics
4. **Code Review Findings**: Detailed agent-specific technical findings
5. **Risk Classification**: Good/OK/Bad categorization with specific recommendations

### 3. Report Example

```
===========================================
COMPREHENSIVE REPOSITORY ANALYSIS REPORT
===========================================

Repository: sample-microservice
Analysis Date: 2025-11-17 14:30:25
Analysis Mode: Full Repository Review
Total Files Analyzed: 127

=== SECTION 1: EXECUTIVE SUMMARY ===

Repository Health: GOOD
Risk Level: LOW
Quality Score: 87/100

The repository demonstrates strong development practices with well-structured 
code, comprehensive testing, and security-conscious implementation...

=== SECTION 2: GIT REPOSITORY DETAILS ===

Default Branch: main
Total Branches: 8
Active Contributors: 12
Total Commits: 445
Latest Commit: 2025-11-15 16:22:31

...
```

## Troubleshooting

### 1. Common Issues

#### Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Ensure Python path is correct
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python risk_analyzer.py <repo-url>
```

#### Authentication Issues
```bash
# Error: HTTP 401 Unauthorized
# Solution: Verify API credentials
python -c "
import os
print('LLM_API_KEY:', os.getenv('LLM_API_KEY')[:10] + '...' if os.getenv('LLM_API_KEY') else 'Not set')
print('GITHUB_TOKEN:', os.getenv('GITHUB_TOKEN')[:10] + '...' if os.getenv('GITHUB_TOKEN') else 'Not set')
"
```

#### Memory Issues
```bash
# Error: Out of memory
# Solution: Reduce PR limit and file size
export PR_LIMIT=5
export MAX_FILE_SIZE=524288  # 512KB
python risk_analyzer.py <repo-url>
```

#### Network Timeouts
```bash
# Error: Request timeout
# Solution: Increase timeout
export TIMEOUT_SECONDS=600
python risk_analyzer.py <repo-url>
```

### 2. Debug Mode

Enable detailed logging:
```bash
python risk_analyzer.py <repo-url> --log-level DEBUG
```

Check log files:
```bash
tail -f logs/llm_client.log
```

### 3. Configuration Validation

Validate your setup:
```bash
python -c "
from src.utilities.config_utils import validate_environment, load_configuration

if validate_environment():
    print('✓ Environment validation passed')
    config = load_configuration()
    print(f'✓ Configuration loaded: {len(config)} settings')
else:
    print('✗ Environment validation failed')
"
```

### 4. Performance Optimization

For large repositories:
```bash
# Use PR-only mode for faster analysis
CODE_REVIEW_MODE=pr_only

# Limit file processing
MAX_FILE_SIZE=1048576  # 1MB
PR_LIMIT=10

# Increase timeout for complex analysis
TIMEOUT_SECONDS=600

python risk_analyzer.py <large-repo-url>
```

## Support and Resources

### Getting Help
- Review error logs in `logs/llm_client.log`
- Check GitHub issues for known problems
- Verify configuration with validation scripts

### Performance Monitoring
- Monitor memory usage during analysis
- Track analysis execution times
- Review LLM API usage and costs

### Best Practices
- Use PR-only mode for CI/CD integration
- Configure appropriate timeouts for your environment
- Regularly update dependencies and LLM providers
- Archive old reports to save disk space

This guide provides comprehensive instructions for running the Risk Agent Analyzer in various scenarios and environments. Follow the troubleshooting section for resolving common issues.