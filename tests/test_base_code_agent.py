"""
Unit Tests for Base Code Review Agent

Comprehensive test coverage for BaseCodeReviewAgent functionality.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.base_code_agent import BaseCodeReviewAgent
from src.agents.code_review_agents import AgentInput, AgentOutput

class TestBaseCodeReviewAgent(unittest.TestCase):
    """Test cases for BaseCodeReviewAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a concrete implementation for testing
        class TestAgent(BaseCodeReviewAgent):
            def get_language_name(self):
                return "test"
            
            def get_file_extensions(self):
                return ('.test',)
            
            def get_language_specific_analysis_points(self):
                return "Test-specific analysis"
        
        self.agent = TestAgent()
        
    def test_get_metadata(self):
        """Test metadata generation"""
        metadata = self.agent.get_metadata()
        
        self.assertEqual(metadata.name, "test_code_review")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertIn("Test code quality analysis", metadata.description)
        self.assertTrue(metadata.parallel_compatible)
    
    def test_extract_file_path_from_string(self):
        """Test extracting file path from string"""
        file_path = self.agent._extract_file_path("test/file.test")
        self.assertEqual(file_path, "test/file.test")
    
    def test_extract_file_path_from_dict(self):
        """Test extracting file path from dictionary"""
        file_info = {'filename': 'test/file.test', 'status': 'modified'}
        file_path = self.agent._extract_file_path(file_info)
        self.assertEqual(file_path, "test/file.test")
    
    def test_filter_files_by_extension_string_list(self):
        """Test filtering files from string list"""
        files = ['file1.test', 'file2.py', 'file3.test']
        filtered = self.agent._filter_files_by_extension(files)
        
        self.assertEqual(len(filtered), 2)
        self.assertIn('file1.test', filtered)
        self.assertIn('file3.test', filtered)
    
    def test_filter_files_by_extension_dict_list(self):
        """Test filtering files from dictionary list"""
        files = [
            {'filename': 'file1.test', 'status': 'added'},
            {'filename': 'file2.py', 'status': 'modified'},
            {'filename': 'file3.test', 'status': 'deleted'}
        ]
        filtered = self.agent._filter_files_by_extension(files)
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['filename'], 'file1.test')
        self.assertEqual(filtered[1]['filename'], 'file3.test')
    
    def test_get_file_content_from_file_contents(self):
        """Test getting file content from file_contents dict"""
        pr_data = {
            'file_contents': {
                'test.test': 'test content here'
            }
        }
        
        content = self.agent._get_file_content('test.test', pr_data)
        self.assertEqual(content, 'test content here')
    
    def test_get_file_content_from_files_list(self):
        """Test getting file content from files list"""
        pr_data = {
            'files': [
                {
                    'filename': 'test.test',
                    'full_content': 'full content',
                    'patch': 'patch content'
                }
            ]
        }
        
        content = self.agent._get_file_content('test.test', pr_data)
        self.assertEqual(content, 'full content')
    
    def test_get_file_content_fallback_to_patch(self):
        """Test fallback to patch when full_content not available"""
        pr_data = {
            'files': [
                {
                    'filename': 'test.test',
                    'patch': 'patch content only'
                }
            ]
        }
        
        content = self.agent._get_file_content('test.test', pr_data)
        self.assertEqual(content, 'patch content only')
    
    def test_get_file_content_not_found(self):
        """Test getting file content when file not found"""
        pr_data = {'files': []}
        
        content = self.agent._get_file_content('nonexistent.test', pr_data)
        self.assertEqual(content, '')
    
    def test_extract_json_from_plain_response(self):
        """Test extracting JSON from plain text"""
        response = '{"key": "value"}'
        extracted = self.agent._extract_json_from_response(response)
        self.assertEqual(extracted, '{"key": "value"}')
    
    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code block"""
        response = '```json\n{"key": "value"}\n```'
        extracted = self.agent._extract_json_from_response(response)
        self.assertEqual(extracted, '{"key": "value"}')
    
    def test_extract_json_from_code_block(self):
        """Test extracting JSON from generic code block"""
        response = '```\n{"key": "value"}\n```'
        extracted = self.agent._extract_json_from_response(response)
        self.assertEqual(extracted, '{"key": "value"}')
    
    def test_create_fallback_analysis(self):
        """Test creating fallback analysis"""
        analysis = self.agent._create_fallback_analysis("test content")
        
        self.assertEqual(analysis['issues'], [])
        self.assertEqual(analysis['critical_count'], 0)
        self.assertEqual(analysis['warning_count'], 0)
        self.assertEqual(analysis['quality_score'], 70)
        self.assertEqual(analysis['complexity_score'], 50)
        self.assertEqual(analysis['comment_coverage'], 50)
    
    def test_aggregate_results_empty(self):
        """Test aggregating empty results"""
        result = self.agent._aggregate_results([])
        
        self.assertEqual(result['language'], 'test')
        self.assertEqual(result['files_analyzed'], 0)
        self.assertEqual(result['issues_found'], 0)
        self.assertEqual(result['critical_issues'], 0)
    
    def test_aggregate_results_with_data(self):
        """Test aggregating results with actual data"""
        file_analyses = [
            {
                'issues': [{'severity': 'critical'}, {'severity': 'warning'}],
                'critical_count': 1,
                'warning_count': 1,
                'quality_score': 80
            },
            {
                'issues': [{'severity': 'warning'}],
                'critical_count': 0,
                'warning_count': 1,
                'quality_score': 90
            }
        ]
        
        result = self.agent._aggregate_results(file_analyses)
        
        self.assertEqual(result['files_analyzed'], 2)
        self.assertEqual(result['issues_found'], 3)
        self.assertEqual(result['critical_issues'], 1)
        self.assertEqual(result['warnings'], 2)
        self.assertEqual(result['quality_score'], 85)
    
    def test_build_analysis_prompt(self):
        """Test building analysis prompt"""
        prompt = self.agent._build_analysis_prompt("test code", "test.test")
        
        self.assertIn("Test code quality analyzer", prompt)
        self.assertIn("test.test", prompt)
        self.assertIn("Test-specific analysis", prompt)
        self.assertIn("test code", prompt)
        self.assertIn("STRICT JSON format", prompt)
    
    @patch('src.agents.base_code_agent.LLMClient')
    def test_analyze_with_llm_success(self, mock_llm_class):
        """Test successful LLM analysis"""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            'success': True,
            'response': '{"issues": [{"severity": "critical"}], "quality_score": 75, "complexity_score": 60, "comment_coverage": 40}'
        }
        mock_llm_class.return_value = mock_llm
        
        # Create new agent instance with mocked LLM
        class TestAgent(BaseCodeReviewAgent):
            def get_language_name(self):
                return "test"
            def get_file_extensions(self):
                return ('.test',)
            def get_language_specific_analysis_points(self):
                return "Test-specific"
        
        agent = TestAgent()
        
        # Run async test
        async def run_test():
            result = await agent._analyze_with_llm("test code", "test.test")
            self.assertEqual(len(result['issues']), 1)
            self.assertEqual(result['critical_count'], 1)
            self.assertEqual(result['quality_score'], 75)
        
        asyncio.run(run_test())
    
    @patch('src.agents.base_code_agent.LLMClient')
    def test_analyze_with_llm_failure(self, mock_llm_class):
        """Test LLM analysis failure fallback"""
        # Mock LLM failure
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {'success': False}
        mock_llm_class.return_value = mock_llm
        
        class TestAgent(BaseCodeReviewAgent):
            def get_language_name(self):
                return "test"
            def get_file_extensions(self):
                return ('.test',)
            def get_language_specific_analysis_points(self):
                return "Test-specific"
        
        agent = TestAgent()
        
        async def run_test():
            result = await agent._analyze_with_llm("test code", "test.test")
            # Should return fallback analysis
            self.assertEqual(result['issues'], [])
            self.assertEqual(result['quality_score'], 70)
        
        asyncio.run(run_test())
    
    @patch('src.agents.base_code_agent.LLMClient')
    def test_process_no_files(self, mock_llm_class):
        """Test process method with no matching files"""
        pr_data = {
            'files': [
                {'filename': 'other.py', 'content': 'python code'}
            ]
        }
        
        input_data = AgentInput(data=pr_data, session_id="test123")
        
        async def run_test():
            result = await self.agent.process(input_data, None)
            self.assertEqual(result.result['files_analyzed'], 0)
            self.assertEqual(result.session_id, "test123")
        
        asyncio.run(run_test())
    
    @patch('src.agents.base_code_agent.LLMClient')
    def test_process_with_files(self, mock_llm_class):
        """Test process method with matching files"""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            'success': True,
            'response': '{"issues": [], "quality_score": 90, "complexity_score": 30, "comment_coverage": 80}'
        }
        mock_llm_class.return_value = mock_llm
        
        pr_data = {
            'files': [
                {'filename': 'file1.test', 'full_content': 'test code 1'},
                {'filename': 'file2.test', 'full_content': 'test code 2'}
            ]
        }
        
        input_data = AgentInput(data=pr_data, session_id="test456")
        
        class TestAgent(BaseCodeReviewAgent):
            def get_language_name(self):
                return "test"
            def get_file_extensions(self):
                return ('.test',)
            def get_language_specific_analysis_points(self):
                return "Test-specific"
        
        agent = TestAgent()
        
        async def run_test():
            result = await agent.process(input_data, None)
            self.assertEqual(result.result['files_analyzed'], 2)
            self.assertEqual(result.result['language'], 'test')
            self.assertGreater(result.execution_time, 0)
        
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
