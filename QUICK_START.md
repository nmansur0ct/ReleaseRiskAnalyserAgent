# Quick Start Guide - Release Risk Analyzer

## 🚀 5-Minute Setup

### 1. Clone & Setup
```bash
git clone https://gecgithub01.walmart.com/n0m08hp/RiskAnalyzerAgent.git
cd RiskAnalyzerAgent
pip install -r requirements.txt
```

### 2. Run Demo
```bash
cd src
python simple_demo.py
```

### 3. Expected Output
```
🚀 Plugin Framework Architecture Demonstration
🔍 Change Log Summarizer ✓
🔍 Security Analyzer ✓  
🔍 Compliance Checker ✓
🔍 Release Decision Agent ✓
🔍 Notification Agent ✓
✅ Analysis Complete!
```

## ⚙️ Configuration Quick Reference

### Basic Config
```yaml
# config/basic_config.yaml
workflow:
  execution_mode: "hybrid"
plugins:
  change_log_summarizer:
    enabled: true
  security_analyzer:
    enabled: true
  notification_agent:
    enabled: true
```

### Environment Configuration
```bash
# Create .env file from template
cp .env.template .env

# Edit .env file with your settings
LLM_PROVIDER=openai
OPENAI_API_KEY="your-key"
SLACK_WEBHOOK_URL="your-webhook"
```

### Legacy Environment Variables
```bash
export OPENAI_API_KEY="your-key"
export LLM_PROVIDER="openai"
export SLACK_WEBHOOK_URL="your-webhook"
```

## 🔧 Common Commands

```bash
# Run demo
python src/simple_demo.py

# Debug mode
LOG_LEVEL=DEBUG python src/simple_demo.py

# Custom config
python src/simple_demo.py --config config/enterprise_config.yaml

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('config/basic_config.yaml')))"

# Validate environment
python -c "from src.environment_config import get_env_config; c=get_env_config(); print(f'LLM: {c.get_llm_config()}')"
```

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run from `src/` directory |
| `Config not found` | Use absolute path or run from project root |
| `API Error` | Check environment variables |
| `Plugin not loading` | Verify `enabled: true` in config |

## 🔌 Add Custom Plugin (3 Steps)

### 1. Create Plugin
```python
# src/my_plugin.py
class MyPlugin(BaseAgentPlugin):
    def get_metadata(self): 
        return AgentMetadata(name="my_plugin")
    async def process(self, input_data, state):
        return AgentOutput(result={"status": "done"})
```

### 2. Add Config
```yaml
# config/basic_config.yaml
plugins:
  my_plugin:
    enabled: true
    config:
      setting: "value"
```

### 3. Auto-Discovery
Framework automatically finds and runs your plugin!

## 📊 Understanding Output

- 🟢 **MINIMAL** (0-24): Low risk
- 🟠 **LOW** (25-49): Some concerns  
- 🟡 **MEDIUM** (50-74): Significant concerns
- 🔴 **HIGH** (75-100): Major risks

## 📚 Documentation Links

- **Complete Guide**: [HOW_TO_RUN.md](HOW_TO_RUN.md)
- **Plugin Development**: [PLUGIN_FRAMEWORK_GUIDE.md](PLUGIN_FRAMEWORK_GUIDE.md)
- **Architecture**: [Architecture.md](Architecture.md)

---
**Need help? Check HOW_TO_RUN.md for detailed instructions!**