"""
Configuration examples for the plugin-based framework
"""

# Example 1: Basic Configuration
BASIC_CONFIG = {
    "workflow": {
        "name": "risk_analysis_workflow",
        "version": "2.0.0",
        "description": "Modular release risk analysis",
        "execution_mode": "sequential_with_parallel",
        "timeout_seconds": 300
    },
    "plugins": {
        "change_log_summarizer": {
            "enabled": True,
            "config": {
                "llm_provider": "openai",
                "confidence_threshold": 0.7,
                "analysis_depth": "comprehensive",
                "timeout_seconds": 60
            }
        },
        "security_analyzer": {
            "enabled": True,
            "config": {
                "scan_types": ["secret_detection", "vulnerability_scan", "dependency_check"],
                "severity_threshold": "medium"
            }
        },
        "notification_agent": {
            "enabled": True,
            "config": {
                "channels": ["slack", "email"],
                "webhook_url": "https://hooks.slack.com/services/xxx"
            }
        }
    },
    "global_config": {
        "log_level": "INFO",
        "max_parallel_agents": 3,
        "enable_metrics": True,
        "metrics_endpoint": "http://metrics.internal:8080"
    }
}

# Example 2: Enterprise Configuration with all features
ENTERPRISE_CONFIG = {
    "workflow": {
        "name": "enterprise_risk_analysis",
        "version": "2.0.0",
        "description": "Comprehensive enterprise risk analysis with compliance",
        "execution_mode": "hybrid",
        "timeout_seconds": 600,
        "retry_policy": {
            "max_retries": 3,
            "backoff_strategy": "exponential"
        }
    },
    "plugins": {
        "change_log_summarizer": {
            "enabled": True,
            "config": {
                "llm_provider": "openai",
                "fallback_provider": "anthropic",
                "confidence_threshold": 0.8,
                "analysis_depth": "comprehensive",
                "timeout_seconds": 120,
                "cache_results": True
            }
        },
        "security_analyzer": {
            "enabled": True,
            "config": {
                "scan_types": ["secret_detection", "vulnerability_scan", "dependency_check", "static_analysis"],
                "severity_threshold": "low",
                "custom_patterns": {
                    "api_keys": r"(api_key|apikey).*['\"][A-Za-z0-9]{20,}['\"]",
                    "tokens": r"(token|auth).*['\"][A-Za-z0-9\-_]{20,}['\"]"
                },
                "vulnerability_db_url": "https://nvd.nist.gov/feeds/json/cve/1.1/"
            }
        },
        "custom_compliance_checker": {
            "enabled": True,
            "config": {
                "standards": ["SOX", "GDPR", "HIPAA"],
                "custom_rules": {
                    "financial_review": {
                        "file_patterns": ["*financial*", "*billing*", "*payment*"],
                        "required_approvers": ["financial_team", "compliance_officer"]
                    },
                    "data_privacy": {
                        "keywords": ["personal_data", "customer_info", "pii"],
                        "required_documentation": ["privacy_impact_assessment"]
                    }
                },
                "exemption_list": ["test_data", "mock_services"]
            }
        },
        "policy_validator": {
            "enabled": True,
            "config": {
                "policy_sources": ["internal_wiki", "confluence"],
                "policy_categories": ["deployment", "security", "compliance"],
                "auto_update_policies": True,
                "policy_cache_ttl": 3600
            }
        },
        "release_decision_agent": {
            "enabled": True,
            "config": {
                "decision_criteria": {
                    "security_score_threshold": 25,
                    "compliance_required": True,
                    "approval_gates": ["security_team", "compliance_team"],
                    "auto_approve_conditions": {
                        "change_size": "small",
                        "security_score": {"max": 10},
                        "affected_modules": {"exclude": ["core", "security"]}
                    }
                },
                "escalation_rules": {
                    "high_risk": ["cto", "security_director"],
                    "compliance_violation": ["compliance_officer", "legal_team"]
                }
            }
        },
        "notification_agent": {
            "enabled": True,
            "config": {
                "channels": ["slack", "email", "webhook", "teams"],
                "templates_path": "/config/notification_templates",
                "slack_config": {
                    "webhook_url": "https://hooks.slack.com/services/xxx",
                    "channel": "#releases",
                    "username": "RiskAnalyzer"
                },
                "email_config": {
                    "smtp_server": "smtp.company.com",
                    "from_address": "noreply@company.com",
                    "recipients": ["devops@company.com", "security@company.com"]
                },
                "notification_rules": {
                    "high_risk": ["slack", "email"],
                    "compliance_violation": ["email", "teams"],
                    "approval_required": ["slack"]
                }
            }
        }
    },
    "global_config": {
        "log_level": "DEBUG",
        "max_parallel_agents": 5,
        "enable_metrics": True,
        "metrics_endpoint": "http://prometheus.internal:9090",
        "tracing_enabled": True,
        "jaeger_endpoint": "http://jaeger.internal:14268",
        "cache_enabled": True,
        "cache_backend": "redis",
        "cache_config": {
            "host": "redis.internal",
            "port": 6379,
            "db": 0
        },
        "database": {
            "host": "postgres.internal",
            "port": 5432,
            "database": "risk_analyzer",
            "schema": "analytics"
        }
    }
}

# Example 3: Development/Testing Configuration
DEVELOPMENT_CONFIG = {
    "workflow": {
        "name": "dev_risk_analysis",
        "version": "2.0.0-dev",
        "description": "Development environment risk analysis",
        "execution_mode": "sequential",
        "timeout_seconds": 120
    },
    "plugins": {
        "change_log_summarizer": {
            "enabled": True,
            "config": {
                "llm_provider": "mock",  # Use mock provider for testing
                "confidence_threshold": 0.5,
                "analysis_depth": "basic",
                "timeout_seconds": 30
            }
        },
        "security_analyzer": {
            "enabled": True,
            "config": {
                "scan_types": ["secret_detection"],  # Limited scanning for dev
                "severity_threshold": "high"
            }
        },
        "notification_agent": {
            "enabled": False  # Disable notifications in dev
        }
    },
    "global_config": {
        "log_level": "DEBUG",
        "max_parallel_agents": 2,
        "enable_metrics": False,
        "cache_enabled": False
    }
}

# Example 4: Custom Plugin Configuration Template
CUSTOM_PLUGIN_TEMPLATE = {
    "workflow": {
        "name": "custom_analysis_workflow",
        "version": "1.0.0",
        "description": "Workflow with custom plugins",
        "execution_mode": "parallel",
        "timeout_seconds": 300
    },
    "plugins": {
        # Built-in plugins
        "change_log_summarizer": {
            "enabled": True,
            "config": {
                "llm_provider": "openai",
                "confidence_threshold": 0.7
            }
        },
        
        # Custom plugin example
        "custom_business_rules": {
            "enabled": True,
            "plugin_path": "/custom_plugins/business_rules.py",
            "class_name": "BusinessRulesPlugin",
            "config": {
                "rules_database": "postgresql://localhost/business_rules",
                "validation_mode": "strict",
                "business_units": ["finance", "hr", "operations"],
                "approval_matrix": {
                    "finance": ["finance_manager", "cfo"],
                    "hr": ["hr_director"],
                    "operations": ["ops_manager"]
                }
            }
        },
        
        # Another custom plugin
        "performance_analyzer": {
            "enabled": True,
            "plugin_path": "/custom_plugins/performance.py",
            "class_name": "PerformanceAnalyzerPlugin",
            "config": {
                "benchmark_data": "/data/benchmarks.json",
                "performance_thresholds": {
                    "response_time": 200,  # milliseconds
                    "cpu_usage": 80,       # percentage
                    "memory_usage": 85     # percentage
                },
                "load_test_config": {
                    "duration": 300,
                    "concurrent_users": 100,
                    "ramp_up_time": 30
                }
            }
        }
    },
    "global_config": {
        "log_level": "INFO",
        "max_parallel_agents": 4,
        "enable_metrics": True,
        "custom_plugins_path": "/custom_plugins",
        "hot_reload": True
    }
}

# Example 5: Minimal Configuration
MINIMAL_CONFIG = {
    "workflow": {
        "name": "minimal_analysis",
        "version": "1.0.0"
    },
    "plugins": {
        "change_log_summarizer": {
            "enabled": True,
            "config": {
                "llm_provider": "openai"
            }
        }
    }
}

# Configuration validation schema (for reference)
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["workflow", "plugins"],
    "properties": {
        "workflow": {
            "type": "object",
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "execution_mode": {
                    "type": "string",
                    "enum": ["sequential", "parallel", "hybrid", "sequential_with_parallel"]
                },
                "timeout_seconds": {"type": "integer", "minimum": 1},
                "retry_policy": {
                    "type": "object",
                    "properties": {
                        "max_retries": {"type": "integer", "minimum": 0},
                        "backoff_strategy": {
                            "type": "string",
                            "enum": ["linear", "exponential", "fixed"]
                        }
                    }
                }
            }
        },
        "plugins": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                    "type": "object",
                    "required": ["enabled"],
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "config": {"type": "object"},
                        "plugin_path": {"type": "string"},
                        "class_name": {"type": "string"}
                    }
                }
            }
        },
        "global_config": {
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                },
                "max_parallel_agents": {"type": "integer", "minimum": 1},
                "enable_metrics": {"type": "boolean"},
                "cache_enabled": {"type": "boolean"}
            }
        }
    }
}