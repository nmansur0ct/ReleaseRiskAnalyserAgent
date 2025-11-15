# Release Risk Analyzer Agent

## Overview

The Release Risk Analyzer Agent is an enterprise-grade, AI-powered framework for automated Pull Request (PR) analysis and release decision support. It combines real-time GitHub API integration with Large Language Model (LLM) capabilities to provide comprehensive risk assessment, compliance validation, and intelligent release recommendations.

The system employs a hybrid analysis approach, leveraging both semantic understanding through AI agents and deterministic heuristic analysis to deliver accurate, evidence-based PR evaluations. It is designed for multi-repository environments and supports enterprise compliance standards including PCI DSS, GDPR, and SOX.

## Key Features

### Intelligent PR Analysis
- **Real-time GitHub Integration**: Fetches live PR data including code changes, comments, and reviews via GitHub REST API
- **Multi-Repository Support**: Analyze PRs across multiple repositories in a single execution
- **Comprehensive Comment Analysis**: Retrieves and analyzes both issue comments and inline code review comments
- **Hybrid Analysis Engine**: Combines LLM semantic understanding with rule-based heuristic analysis

### AI-Powered Decision Making
- **LLM Provider Flexibility**: Supports multiple LLM providers including Walmart LLM Gateway, OpenAI, and Anthropic
- **5-Plugin Analysis Framework**: Modular plugin system for specialized analysis domains
- **Confidence Scoring**: Provides confidence levels and quality scores for each recommendation
- **Risk Classification**: Categorizes PRs as LOW, MEDIUM, or HIGH risk with detailed reasoning

### Enterprise Compliance
- **Security Analysis**: Identifies security vulnerabilities and validates security improvements
- **Compliance Validation**: Verifies adherence to PCI DSS, GDPR, and SOX standards
- **Audit Trail**: Generates detailed reports with complete analysis methodology and decision rationale
- **Professional Output**: Enterprise-ready reports without emojis or informal language

### Advanced Reporting
- **Comprehensive Reports**: Multi-repository summary reports with per-PR breakdowns
- **Review Comment Integration**: Includes PR comments and discussions in analysis context
- **Persistent Storage**: Saves timestamped reports to dedicated reports directory
- **Detailed Metrics**: Provides aggregate statistics across repositories and PRs

## Architecture

### High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Release Risk Analyzer Agent                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Configuration Layer                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Environment      │  │ LLM Provider     │  │ Git Provider    │  │
│  │ Config (.env)    │  │ Configuration    │  │ Configuration   │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Acquisition Layer                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    GitHub API Integration                     │  │
│  │  • Pull Request Fetching    • File Changes Retrieval         │  │
│  │  • Issue Comments           • Review Comments                │  │
│  │  • Metadata Extraction      • Authentication Management      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Analysis Processing Layer                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              5-Plugin Analysis Framework                    │   │
│  │  ┌──────────────────┐  ┌──────────────────┐               │   │
│  │  │ Change Log       │  │ Security         │               │   │
│  │  │ Summarizer       │  │ Analyzer         │               │   │
│  │  └──────────────────┘  └──────────────────┘               │   │
│  │  ┌──────────────────┐  ┌──────────────────┐               │   │
│  │  │ Compliance       │  │ Release Decision │               │   │
│  │  │ Checker          │  │ Agent            │               │   │
│  │  └──────────────────┘  └──────────────────┘               │   │
│  │  ┌──────────────────┐                                      │   │
│  │  │ Notification     │                                      │   │
│  │  │ Agent            │                                      │   │
│  │  └──────────────────┘                                      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                  Hybrid Analysis Engine                     │   │
│  │  ┌─────────────────────────┐  ┌────────────────────────┐  │   │
│  │  │  LLM Semantic Analysis  │  │ Heuristic Analysis     │  │   │
│  │  │  • Context Understanding│  │ • Pattern Matching     │  │   │
│  │  │  • Intent Classification│  │ • Rule-based Scoring   │  │   │
│  │  │  • Risk Assessment      │  │ • Statistical Metrics  │  │   │
│  │  │  • Natural Language     │  │ • Deterministic Logic  │  │   │
│  │  └─────────────────────────┘  └────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Decision & Reporting Layer                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    Verdict Generation                       │   │
│  │  • Recommendation: APPROVE / CONDITIONAL / REJECT          │   │
│  │  • Risk Level: LOW / MEDIUM / HIGH                         │   │
│  │  • Confidence Score: 0-100%                                │   │
│  │  • Quality Score: 0-100                                    │   │
│  │  • Evidence-based Reasoning                                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              Comprehensive Report Generation                │   │
│  │  • Per-Repository Breakdown                                │   │
│  │  • Per-PR Analysis Details                                 │   │
│  │  • Comment and Review Integration                          │   │
│  │  • Aggregate Metrics and Statistics                        │   │
│  │  • Executive Summary (LLM-powered)                         │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Plugin Framework Architecture

Each plugin operates independently and contributes specialized analysis:

1. **Change Log Summarizer**: Analyzes code changes, impact assessment, and affected modules
2. **Security Analyzer**: Identifies vulnerabilities, validates security improvements, and checks compliance
3. **Compliance Checker**: Validates PCI DSS, GDPR, SOX adherence and code coverage requirements
4. **Release Decision Agent**: Provides final recommendation with risk assessment and manual review requirements
5. **Notification Agent**: Manages stakeholder communication and escalation routing

### Analysis Workflow

```
PR Data Input → Parallel Plugin Execution → Hybrid Analysis (LLM + Heuristic)
     ↓                                              ↓
Comment Fetching                          Individual Plugin Results
     ↓                                              ↓
Metadata Enrichment                       Confidence Scoring
     ↓                                              ↓
                        Combined Verdict Generation
                                  ↓
                        Comprehensive Report Output
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Git access token with repository read permissions
- LLM API credentials (Walmart LLM Gateway, OpenAI, or Anthropic)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/nmansur0ct/ReleaseRiskAnalyserAgent.git
   cd ReleaseRiskAnalyserAgent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy the template and configure your credentials:
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` and set the following required variables:
   ```bash
   # Git Integration
   GIT_ACCESS_TOKEN=your_github_token_here
   GIT_API_BASE_URL=https://api.github.com
   
   # LLM Provider (choose one or more)
   LLM_PROVIDER=walmart_llm_gateway
   WALMART_LLM_GATEWAY_URL=your_gateway_url
   WALMART_LLM_GATEWAY_KEY=your_api_key
   WALMART_LLM_MODEL=gpt-4
   
   # Optional: OpenAI fallback
   OPENAI_API_KEY=your_openai_key
   OPENAI_MODEL=gpt-4
   ```

4. **Verify installation**
   ```bash
   python src/simple_demo.py --help
   ```

## Usage

### Basic PR Analysis

Analyze PRs from a single repository:

```bash
python src/simple_demo.py https://github.com/owner/repository
```

Analyze specific branch:

```bash
python src/simple_demo.py https://github.com/owner/repository/tree/branch-name
```

### Multi-Repository Analysis

Analyze multiple repositories in parallel:

```bash
python src/simple_demo.py \
  https://github.com/owner/repo1 \
  https://github.com/owner/repo2 \
  https://github.com/owner/repo3
```

### Command-Line Options

```bash
python src/simple_demo.py [OPTIONS] REPOSITORY_URL [REPOSITORY_URL ...]

Options:
  --pr-limit INTEGER    Maximum number of PRs to analyze per repository (default: 5)
  --help               Show help message and exit
```

### Example Output

The tool generates comprehensive reports including:

- Repository-level statistics and aggregate metrics
- Per-PR analysis with detailed breakdown:
  - Author, changes, files modified
  - Security and compliance analysis
  - Risk assessment and confidence scores
  - Review comments and discussions
- Executive summary with AI-powered insights
- Verdict recommendations: APPROVE, CONDITIONAL, or REJECT

Reports are automatically saved to the `reports/` directory with timestamps.

## Configuration

### Environment Variables

#### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `GIT_ACCESS_TOKEN` | GitHub personal access token with repo read permissions | `ghp_abc123...` |
| `LLM_PROVIDER` | Primary LLM provider to use | `walmart_llm_gateway` |
| `WALMART_LLM_GATEWAY_KEY` | API key for Walmart LLM Gateway | `eyJhbGc...` |

#### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FALLBACK_LLM_PROVIDER` | Backup LLM provider if primary fails | `openai` |
| `LLM_TIMEOUT_SECONDS` | Timeout for LLM API calls | `60` |
| `LLM_MAX_RETRIES` | Maximum retry attempts for failed calls | `3` |
| `LOG_LEVEL` | Logging verbosity level | `INFO` |
| `ENABLE_DEBUG` | Enable debug mode with detailed logging | `false` |

### LLM Provider Configuration

#### Walmart LLM Gateway
```bash
LLM_PROVIDER=walmart_llm_gateway
WALMART_LLM_GATEWAY_URL=https://wmtllmgateway.stage.walmart.com/wmtllmgateway
WALMART_LLM_GATEWAY_KEY=your_jwt_token
WALMART_LLM_MODEL=gpt-4
```

#### OpenAI
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
```

#### Anthropic Claude
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

## Project Structure

```
ReleaseRiskAnalyserAgent/
├── .env                      # Environment configuration (not in git)
├── .env.template            # Environment template with example values
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup configuration
│
├── src/                   # Source code directory
│   ├── simple_demo.py            # Main entry point for PR analysis
│   ├── environment_config.py     # Environment configuration manager
│   ├── git_integration.py        # GitHub API integration layer
│   ├── llm_integration.py        # LLM provider abstraction
│   ├── plugin_framework.py       # Plugin architecture implementation
│   ├── enhanced_models.py        # Data models and schemas
│   ├── example_plugins.py        # Sample plugin implementations
│   └── workflow.py              # Analysis workflow orchestration
│
├── reports/               # Generated analysis reports (auto-created)
│   └── *.txt             # Timestamped report files
│
├── config/               # Additional configuration files
│   └── [optional configs]
│
└── .github/             # GitHub-specific configurations
    └── instructions/    # Copilot instructions for code generation
```

## Core Components

### Git Integration (`git_integration.py`)

Handles all GitHub API interactions:
- Pull request fetching and parsing
- Comment retrieval (issue comments and review comments)
- File change analysis
- Branch and repository URL parsing
- Token-based authentication

**Key Classes:**
- `GitProvider`: Abstract base class for Git providers
- `GitHubProvider`: GitHub-specific implementation
- `GitManager`: High-level interface for Git operations

### LLM Integration (`llm_integration.py`)

Manages interactions with various LLM providers:
- Provider abstraction and fallback mechanisms
- Prompt engineering and response parsing
- Rate limiting and error handling
- Multi-provider support with unified interface

**Key Classes:**
- `LLMProvider`: Abstract base for LLM providers
- `WalmartLLMGatewayProvider`: Walmart LLM Gateway implementation
- `OpenAIProvider`: OpenAI GPT integration
- `AnthropicProvider`: Anthropic Claude integration
- `LLMManager`: Orchestrates provider selection and fallback

### Plugin Framework (`plugin_framework.py`)

Provides extensible plugin architecture:
- Plugin registration and discovery
- Lifecycle management (initialize, execute, cleanup)
- Data passing between plugins
- Result aggregation

**Key Classes:**
- `Plugin`: Base class for all analysis plugins
- `PluginManager`: Manages plugin lifecycle and execution
- `PluginResult`: Standardized plugin output format

### Analysis Workflow (`simple_demo.py`)

Main orchestration logic:
- Multi-repository coordination
- Parallel plugin execution
- Hybrid analysis (LLM + heuristic)
- Report generation and persistence
- Command-line interface

## Analysis Methodology

### Hybrid Analysis Approach

The system employs a two-pronged analysis strategy:

#### 1. LLM Semantic Analysis
- **Purpose**: Understand context, intent, and nuanced risks
- **Capabilities**:
  - Natural language understanding of PR descriptions and comments
  - Intent classification (bug fix, feature, refactor, etc.)
  - Contextual risk assessment
  - Business impact evaluation
- **Confidence**: 85-97% depending on context clarity
- **Processing Time**: ~0.5 seconds per plugin

#### 2. Heuristic Analysis
- **Purpose**: Provide deterministic, rule-based validation
- **Capabilities**:
  - Pattern matching (security keywords, file extensions)
  - Statistical metrics (change size, complexity, file count)
  - Compliance rule validation
  - Quantitative risk scoring
- **Reliability**: 100% (deterministic)
- **Processing Time**: ~0.25 seconds per plugin

#### 3. Combined Verdict
- Weighted combination of LLM and heuristic scores
- Cross-validation between methods
- Final confidence: Minimum of (LLM confidence, 95%)
- Threshold-based decision logic with multi-factor validation

### Decision Criteria

**APPROVE Recommendation:**
- Low risk level (based on change size, complexity, and security analysis)
- All compliance checks passed
- No critical security issues
- Adequate test coverage
- Positive or neutral reviewer feedback

**CONDITIONAL Recommendation:**
- Medium risk level
- Minor compliance or security concerns
- Requires additional review or testing
- Reviewer feedback indicates concerns

**REJECT Recommendation:**
- High risk level
- Critical security vulnerabilities
- Compliance violations
- Insufficient testing
- Negative reviewer consensus

### Risk Level Classification

**LOW Risk:**
- Changes under 200 lines
- Few files affected (< 10)
- No security-related changes
- All compliance standards met
- Comprehensive test coverage

**MEDIUM Risk:**
- Changes between 200-500 lines
- Moderate file count (10-20)
- Security improvements present
- Minor compliance gaps
- Adequate testing

**HIGH Risk:**
- Changes exceeding 500 lines
- Many files affected (> 20)
- Security concerns identified
- Compliance violations
- Insufficient test coverage

## Security Considerations

### Authentication and Authorization
- GitHub tokens stored in `.env` file (excluded from version control)
- Token permissions limited to repository read access
- No token logging or exposure in output
- Secure credential management practices

### Data Privacy
- No PR data stored permanently beyond session reports
- Reports contain only PR metadata and analysis results
- No sensitive code content included in reports
- Compliance with data retention policies

### API Security
- HTTPS-only communication with GitHub API
- Rate limiting respect and backoff strategies
- Error handling prevents information leakage
- Timeout and retry mechanisms prevent abuse

## Error Handling and Resilience

### Graceful Degradation
- Fallback to mock data when API unavailable (development mode only)
- LLM provider fallback chain
- Partial results returned when some plugins fail
- Clear error messaging without system details exposure

### Logging and Monitoring
- Structured logging with configurable levels
- API response status logging
- Performance metrics tracking
- Error categorization and tracking

### Recovery Mechanisms
- Automatic retry with exponential backoff
- Provider failover for LLM services
- Partial analysis completion on non-critical failures
- State preservation for interrupted operations

## Performance Characteristics

### Processing Time
- Single PR analysis: ~4-5 seconds (5 plugins × ~0.8s each)
- Multi-repository analysis: Parallelized per repository
- API response time: ~0.3-0.6 seconds per GitHub API call
- Report generation: < 1 second for standard reports

### Scalability
- Concurrent repository analysis supported
- Rate limiting respects GitHub API constraints
- Efficient caching of configuration data
- Minimal memory footprint per PR analysis

## Troubleshooting

### Common Issues

**Issue: 401 Unauthorized from GitHub API**
- **Cause**: Invalid or expired GitHub token
- **Solution**: Update `GIT_ACCESS_TOKEN` in `.env` with valid token

**Issue: No PRs found in repository**
- **Cause**: No open PRs or incorrect repository URL
- **Solution**: Verify repository has open PRs and URL format is correct

**Issue: LLM timeout errors**
- **Cause**: LLM provider slow response or network issues
- **Solution**: Increase `LLM_TIMEOUT_SECONDS` or check provider status

**Issue: Import errors on startup**
- **Cause**: Missing dependencies
- **Solution**: Run `pip install -r requirements.txt`

### Debug Mode

Enable detailed logging:
```bash
export ENABLE_DEBUG=true
export LOG_LEVEL=DEBUG
python src/simple_demo.py [repository_url]
```

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements.txt`
4. Make changes with proper testing
5. Ensure code follows project conventions
6. Submit pull request with detailed description

### Code Standards
- PEP 8 compliance for Python code
- Type hints for all function signatures
- Comprehensive docstrings for modules, classes, and functions
- No emojis in production code
- Professional, enterprise-ready output

### Testing
- Unit tests for core functionality
- Integration tests for API interactions
- Mock data for development testing
- Real API testing in staging environment

## License

This project is proprietary software developed for enterprise use. All rights reserved.

## Support

For issues, questions, or feature requests, please contact the development team or create an issue in the repository.

## Acknowledgments

- GitHub REST API for PR data access
- LLM providers for AI-powered analysis capabilities
- Open-source dependencies listed in requirements.txt

---

**Version**: 1.0.0  
**Last Updated**: November 15, 2025  
**Maintained by**: Release Risk Analyzer Team
