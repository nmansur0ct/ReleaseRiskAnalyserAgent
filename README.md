# Risk Agent Analyzer

Professional-grade multi-repository analysis framework for comprehensive code review and risk assessment.

## Overview

Risk Agent Analyzer is a modular Python framework that provides automated analysis of Git repositories and pull requests using multiple specialized agents. It integrates with various LLM providers and supports comprehensive reporting for technical leadership decision-making.

## Features

- **Multi-Repository Analysis**: Analyze multiple repositories in a single run
- **Code Review Agents**: Specialized agents for Python, Java, JavaScript, SQL databases, and more
- **LLM Integration**: Walmart LLM Gateway support with configurable providers
- **Comprehensive Reporting**: Detailed reports with Good/OK/Bad classifications
- **Risk Assessment**: Automated risk scoring and quality metrics
- **Modular Architecture**: Clean, maintainable package structure
- **GitHub Enterprise**: Native support for GitHub Enterprise environments

## Architecture

```
src/
├── agents/           # Code review agents for different technologies
├── analysis/         # Core analysis modules and orchestration
├── integration/      # External system integrations (LLM, Git, Config)
├── orchestration/    # Workflow and repository management
├── reporting/        # Comprehensive report generation
└── utilities/        # Common data structures and utilities
```

## Installation

### Prerequisites

- Python 3.8+
- Git access to target repositories
- LLM provider configuration (Walmart LLM Gateway)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Package

```bash
pip install .
```

## Configuration

Create a `.env` file in the root directory:

```bash
# LLM Configuration
LLM_PROVIDER=walmart_gateway
LLM_API_KEY=your_api_key_here
WM_CONSUMER_ID=your_consumer_id
WM_SVC_NAME=your_service_name  
WM_SVC_ENV=your_environment

# GitHub Configuration (for Enterprise)
GITHUB_TOKEN=your_github_token
GITHUB_API_BASE=https://your-github-enterprise.com/api/v3

# Analysis Configuration
CODE_REVIEW_MODE=full_repo  # or 'pr_only'
PR_STATE=open              # open, closed, or all
PR_LIMIT=10
```

## Usage

### Basic Usage

Analyze a single repository:

```bash
python risk_analyzer.py https://github.com/user/repo.git
```

### Multiple Repositories

```bash
python risk_analyzer.py repo1.git repo2.git repo3.git
```

### Advanced Options

```bash
python risk_analyzer.py https://github.com/user/repo.git \
  --pr-limit 5 \
  --pr-state closed \
  --output-dir ./custom-reports \
  --log-level DEBUG
```

### Programmatic Usage

```python
import asyncio
from risk_analyzer import RiskAgentAnalyzer
from src.utilities.config_utils import load_configuration

async def analyze_repos():
    analyzer = RiskAgentAnalyzer()
    config = load_configuration()
    
    repo_urls = [
        "https://github.com/user/repo1.git",
        "https://github.com/user/repo2.git"
    ]
    
    await analyzer.analyze_repositories(repo_urls, config)

# Run analysis
asyncio.run(analyze_repos())
```

## Code Review Modes

### Full Repository Mode
- Analyzes entire codebase
- Comprehensive security and quality review
- Ideal for new repositories or major releases

### PR-Only Mode  
- Focuses on changed files in pull requests
- Faster analysis for incremental changes
- Suitable for continuous integration

Configure mode in `.env`:
```bash
CODE_REVIEW_MODE=full_repo  # or pr_only
```

## Report Structure

Generated reports include:

1. **Executive Summary**: High-level repository health assessment
2. **Git Repository Details**: Branch, PR, and contributor information  
3. **Pull Request Analysis**: Individual PR risk assessments
4. **Code Review Findings**: Agent-specific technical findings
5. **Risk Classification**: Good/OK/Bad categorization with metrics

Reports are saved in `reports/` directory with timestamped filenames.

## Supported Technologies

### Code Review Agents
- **Python**: Quality, security, and complexity analysis
- **Java**: Enterprise patterns and security scanning
- **JavaScript/Node.js**: Modern JS practices and vulnerabilities
- **React**: Component architecture and performance
- **SQL Databases**: BigQuery, Azure SQL, PostgreSQL, Cosmos DB

### Version Control
- GitHub (Public and Enterprise)
- GitLab (Planned)
- Local Git repositories

### LLM Providers
- Walmart LLM Gateway (Primary)
- OpenAI (Configurable)
- Azure OpenAI (Configurable)

## Development

### Project Structure

```
RiskAgentAnalyzer/
├── risk_analyzer.py         # Main executable entry point
├── setup.py                # Package configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── ARCHITECTURE.md         # Detailed architecture documentation
└── src/                    # Source packages
    ├── agents/             # Code review agents
    ├── analysis/           # Analysis orchestration
    ├── integration/        # External integrations
    ├── orchestration/      # Workflow management
    ├── reporting/          # Report generation
    └── utilities/          # Common utilities
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test module
python -m pytest src/tests/test_analysis.py

# Run with coverage
python -m pytest --cov=src
```

### Contributing

1. Follow the modular architecture patterns
2. Add comprehensive type hints
3. Include proper error handling and logging
4. Update documentation for new features
5. Follow the established import conventions

## Examples

### Enterprise Repository Analysis

```bash
# Analyze enterprise repository with custom settings
python risk_analyzer.py https://gecgithub01.walmart.com/user/repo.git \
  --pr-limit 20 \
  --pr-state all \
  --output-dir ./enterprise-reports
```

### CI/CD Integration

```yaml
# .github/workflows/risk-analysis.yml
name: Repository Risk Analysis
on: [push, pull_request]

jobs:
  risk-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Risk Analysis
        run: python risk_analyzer.py ${{ github.repositoryUrl }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
```

## Troubleshooting

### Common Issues

**Import Errors**: Ensure all dependencies are installed and Python path is configured
```bash
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**API Authentication**: Verify LLM provider credentials and network access
```bash
# Test connection
python -c "from src.integration.llm_client import LLMClient; print('LLM connection OK')"
```

**GitHub Access**: Check token permissions and enterprise API endpoints
```bash
# Test GitHub access
curl -H "Authorization: token $GITHUB_TOKEN" https://your-github-api.com/user
```

## License

MIT License - See LICENSE file for details.

## Support

For technical support and feature requests, please create an issue in the repository.
