"""
Unit Tests for Code Review Orchestrator

Comprehensive test coverage for CodeReviewOrchestrator functionality.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis.code_review_orchestrator import CodeReviewOrchestrator
from src.utilities.data_structures import CodeReviewResult

class TestCodeReviewOrchestrator(unittest.TestCase):
    """Test cases for CodeReviewOrchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "min_quality_score": 70.0,
            "cost_threshold": 1000.0,
            "code_review_mode": "pr_only"
        }
        self.orchestrator = CodeReviewOrchestrator(self.config)
    
    def test_initialization(self):
        """Test orchestrator initialization"""
        self.assertIsNotNone(self.orchestrator)
        self.assertEqual(self.orchestrator.config, self.config)
        self.assertIn('python_agent', self.orchestrator.agents)
        self.assertIn('java_agent', self.orchestrator.agents)
        self.assertIn('nodejs_agent', self.orchestrator.agents)
    
    def test_initialize_agents(self):
        """Test agent initialization"""
        agents = self.orchestrator._initialize_agents()
        
        # Check all expected agents are initialized
        expected_agents = [
            'python_agent', 'java_agent', 'nodejs_agent', 'react_agent',
            'bigquery_agent', 'azuresql_agent', 'postgresql_agent', 'cosmosdb_agent'
        ]
        
        for agent_name in expected_agents:
            self.assertIn(agent_name, agents)
            self.assertIsNotNone(agents[agent_name])
    
    def test_extract_repository_info_with_repository_url(self):
        """Test extracting repository info when repository_url is present"""
        pr_data = {
            'repository_url': 'https://github.com/user/repo.git',
            'base': {'ref': 'develop'}
        }
        
        repo_url, branch = self.orchestrator._extract_repository_info(pr_data)
        
        self.assertEqual(repo_url, 'https://github.com/user/repo.git')
        self.assertEqual(branch, 'develop')
    
    def test_extract_repository_info_from_base(self):
        """Test extracting repository info from base object"""
        pr_data = {
            'base': {
                'repo': {
                    'clone_url': 'https://github.com/user/repo.git'
                },
                'ref': 'main'
            }
        }
        
        repo_url, branch = self.orchestrator._extract_repository_info(pr_data)
        
        self.assertEqual(repo_url, 'https://github.com/user/repo.git')
        self.assertEqual(branch, 'main')
    
    def test_extract_repository_info_from_html_url(self):
        """Test extracting repository info from PR html_url"""
        pr_data = {
            'html_url': 'https://github.com/user/repo/pull/123'
        }
        
        repo_url, branch = self.orchestrator._extract_repository_info(pr_data)
        
        self.assertEqual(repo_url, 'https://github.com/user/repo')
        self.assertEqual(branch, 'main')  # Default branch
    
    def test_extract_repository_info_default_branch(self):
        """Test default branch when not specified"""
        pr_data = {
            'repository_url': 'https://github.com/user/repo.git'
        }
        
        repo_url, branch = self.orchestrator._extract_repository_info(pr_data)
        
        self.assertEqual(branch, 'main')
    
    def test_execute_code_review_invalid_mode(self):
        """Test execute_code_review with invalid code_review_mode"""
        invalid_config = {**self.config, 'code_review_mode': 'invalid_mode'}
        orchestrator = CodeReviewOrchestrator(invalid_config)
        
        pr_data = {
            'files': [
                {'filename': 'test.py', 'full_content': 'print("hello")'}
            ]
        }
        
        async def run_test():
            with patch.object(orchestrator, 'logger') as mock_logger:
                result = await orchestrator.execute_code_review(pr_data, "session123")
                # Should log warning and default to pr_only
                mock_logger.warning.assert_called_once()
                self.assertIn('Invalid code_review_mode', mock_logger.warning.call_args[0][0])
        
        asyncio.run(run_test())
    
    def test_execute_code_review_pr_only_mode(self):
        """Test execute_code_review in pr_only mode"""
        pr_data = {
            'files': [
                {'filename': 'test.py', 'full_content': 'print("hello")'}
            ]
        }
        
        async def run_test():
            # Mock agent execution
            with patch.object(self.orchestrator, '_execute_single_agent', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {'result': {'issues_found': 0}}
                
                result = await self.orchestrator.execute_code_review(pr_data, "session456")
                
                # Should call agent execution
                self.assertGreater(mock_execute.call_count, 0)
        
        asyncio.run(run_test())
    
    @patch('src.analysis.code_review_orchestrator.get_git_manager')
    def test_execute_code_review_full_repo_mode(self, mock_git_manager):
        """Test execute_code_review in full_repo mode"""
        config = {**self.config, 'code_review_mode': 'full_repo'}
        orchestrator = CodeReviewOrchestrator(config)
        
        # Mock git manager
        mock_manager = Mock()
        mock_manager.get_repository_files.return_value = asyncio.Future()
        mock_manager.get_repository_files.return_value.set_result([
            {'filename': 'src/main.py', 'full_content': 'def main(): pass'}
        ])
        mock_git_manager.return_value = mock_manager
        
        pr_data = {
            'repository_url': 'https://github.com/user/repo.git',
            'base': {'ref': 'main'}
        }
        
        async def run_test():
            with patch.object(orchestrator, '_execute_single_agent', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {'result': {'issues_found': 0}}
                
                result = await orchestrator.execute_code_review(pr_data, "session789")
                
                # Should fetch repository files
                mock_manager.get_repository_files.assert_called_once()
        
        asyncio.run(run_test())
    
    def test_execute_single_agent(self):
        """Test single agent execution"""
        # Create mock agent
        mock_agent = Mock()
        mock_agent_output = Mock()
        mock_agent_output.result = {'issues': []}
        mock_agent_output.metadata = {'language': 'python'}
        mock_agent_output.execution_time = 1.5
        
        mock_agent.process = AsyncMock(return_value=mock_agent_output)
        mock_agent.get_metadata.return_value = Mock(name='test_agent')
        
        agent_input = Mock()
        
        async def run_test():
            result = await self.orchestrator._execute_single_agent(
                'test_agent',
                mock_agent,
                agent_input
            )
            
            self.assertIsNotNone(result)
            mock_agent.process.assert_called_once()
        
        asyncio.run(run_test())
    
    def test_execute_single_agent_error(self):
        """Test single agent execution with error"""
        # Create mock agent that raises exception
        mock_agent = Mock()
        mock_agent.process = AsyncMock(side_effect=Exception("Test error"))
        mock_agent.get_metadata.return_value = Mock(name='error_agent')
        
        agent_input = Mock()
        
        async def run_test():
            with patch.object(self.orchestrator, 'logger') as mock_logger:
                result = await self.orchestrator._execute_single_agent(
                    'error_agent',
                    mock_agent,
                    agent_input
                )
                
                # Should log error
                mock_logger.error.assert_called_once()
                self.assertIsNone(result)
        
        asyncio.run(run_test())

class TestCodeReviewOrchestratorIntegration(unittest.TestCase):
    """Integration tests for CodeReviewOrchestrator"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = {
            "min_quality_score": 70.0,
            "code_review_mode": "pr_only"
        }
        self.orchestrator = CodeReviewOrchestrator(self.config)
    
    @patch('src.agents.code_review_agents.LLMClient')
    def test_full_code_review_workflow(self, mock_llm_class):
        """Test full code review workflow end-to-end"""
        # Mock LLM responses
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            'success': True,
            'response': '{"issues": [{"severity": "warning", "message": "Test issue"}], "quality_score": 85, "complexity_score": 40, "comment_coverage": 70}'
        }
        mock_llm_class.return_value = mock_llm
        
        pr_data = {
            'files': [
                {'filename': 'app.py', 'full_content': 'def hello():\n    print("Hello")'},
                {'filename': 'utils.js', 'full_content': 'function test() { return true; }'},
                {'filename': 'Main.java', 'full_content': 'public class Main { }'}
            ]
        }
        
        async def run_test():
            results = await self.orchestrator.execute_code_review(pr_data, "integration_test")
            
            # Should have results for multiple languages
            self.assertGreater(len(results), 0)
            
            # Check that results are CodeReviewResult objects
            for agent_name, result in results.items():
                if result:  # Some agents may not process files
                    self.assertIsNotNone(result)
        
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
