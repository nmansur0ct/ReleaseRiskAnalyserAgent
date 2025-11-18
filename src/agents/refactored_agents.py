"""
Refactored Code Review Agents Using Base Class

All agents now inherit from BaseCodeReviewAgent to eliminate code duplication.
"""

from typing import Tuple
from .base_code_agent import BaseCodeReviewAgent

class PythonCodeReviewAgentRefactored(BaseCodeReviewAgent):
    """Python code quality review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "python"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.py',)
    
    def get_language_specific_analysis_points(self) -> str:
        return "Python-specific best practices (PEP 8, type hints, pythonic patterns)"

class JavaCodeReviewAgentRefactored(BaseCodeReviewAgent):
    """Java code quality review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "java"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.java',)
    
    def get_language_specific_analysis_points(self) -> str:
        return "Java standards, Javadoc, object-oriented design patterns"

class NodeJSCodeReviewAgentRefactored(BaseCodeReviewAgent):
    """Node.js code quality review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "nodejs"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.js', '.ts')
    
    def get_language_specific_analysis_points(self) -> str:
        return "JavaScript/TypeScript standards, async patterns, ES6+ features"

class ReactJSCodeReviewAgentRefactored(BaseCodeReviewAgent):
    """React.js code quality review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "react"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.jsx', '.tsx')
    
    def get_language_specific_analysis_points(self) -> str:
        return "React patterns, hooks usage, component design, performance optimization"

class BigQueryReviewAgentRefactored(BaseCodeReviewAgent):
    """BigQuery SQL review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "bigquery"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.sql', '.bqsql')
    
    def get_language_specific_analysis_points(self) -> str:
        return "BigQuery-specific SQL syntax, optimization patterns, cost efficiency"

class AzureSQLReviewAgentRefactored(BaseCodeReviewAgent):
    """Azure SQL review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "azuresql"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.sql',)
    
    def get_language_specific_analysis_points(self) -> str:
        return "Azure SQL specific features, T-SQL syntax, performance optimization"

class PostgreSQLReviewAgentRefactored(BaseCodeReviewAgent):
    """PostgreSQL review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "postgresql"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.sql', '.pgsql')
    
    def get_language_specific_analysis_points(self) -> str:
        return "PostgreSQL-specific features, indexing strategies, query optimization"

class CosmosDBReviewAgentRefactored(BaseCodeReviewAgent):
    """CosmosDB review agent using LLM"""
    
    def get_language_name(self) -> str:
        return "cosmosdb"
    
    def get_file_extensions(self) -> Tuple[str, ...]:
        return ('.sql', '.cosmos')
    
    def get_language_specific_analysis_points(self) -> str:
        return "CosmosDB query patterns, partition key design, RU optimization"
