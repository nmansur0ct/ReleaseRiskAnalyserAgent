"""
Unit Tests for LLM Client

Tests for LLM client functionality and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.integration.llm_client import LLMClient

class TestLLMClient(unittest.TestCase):
    """Test cases for LLMClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'CONSUMER_PEM_FILE_PATH': '/path/to/test.pem',
            'CONSUMER_ID': 'test_consumer',
            'LLM_GATEWAY_URL': 'https://test.gateway.com',
            'LLM_MODEL': 'gpt-4',
            'LLM_MAX_TOKENS': '2000',
            'LLM_TEMPERATURE': '0.5',
            'LLM_TIMEOUT_SECONDS': '60'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up"""
        self.env_patcher.stop()
    
    def test_initialization(self):
        """Test LLM client initialization"""
        client = LLMClient()
        
        self.assertEqual(client.consumer_id, 'test_consumer')
        self.assertEqual(client.model, 'gpt-4')
        self.assertEqual(client.max_tokens, 2000)
        self.assertEqual(client.temperature, 0.5)
        self.assertEqual(client.timeout, 60)
    
    @patch('builtins.open', create=True)
    def test_load_pem_key_success(self, mock_open):
        """Test successful PEM key loading"""
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key_content'
        
        client = LLMClient()
        client._load_pem_key()
        
        self.assertEqual(client.key_content, 'test_key_content')
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_pem_key_failure(self, mock_open):
        """Test PEM key loading failure"""
        client = LLMClient()
        
        with self.assertRaises(ValueError):
            client._load_pem_key()
    
    @patch('src.integration.llm_client.RSA')
    @patch('src.integration.llm_client.PKCS1_v1_5')
    @patch('src.integration.llm_client.SHA256')
    def test_generate_signature(self, mock_sha256, mock_pkcs, mock_rsa):
        """Test signature generation"""
        # Mock RSA components
        mock_key = Mock()
        mock_rsa.importKey.return_value = mock_key
        
        mock_signer = Mock()
        mock_pkcs.new.return_value = mock_signer
        
        mock_digest = Mock()
        mock_sha256.new.return_value = mock_digest
        
        mock_signer.sign.return_value = b'test_signature'
        
        client = LLMClient()
        headers = client._generate_signature('test_consumer', 'test_key')
        
        self.assertIn('WM_SEC.AUTH_SIGNATURE', headers)
        self.assertIn('WM_CONSUMER.INTIMESTAMP', headers)
        self.assertIn('WM_CONSUMER.ID', headers)
        self.assertEqual(headers['WM_CONSUMER.ID'], 'test_consumer')
    
    def test_generate_headers(self):
        """Test header generation"""
        client = LLMClient()
        
        with patch.object(client, '_generate_signature') as mock_sig:
            mock_sig.return_value = {
                'WM_SEC.AUTH_SIGNATURE': 'test_sig',
                'WM_CONSUMER.INTIMESTAMP': '12345',
                'WM_CONSUMER.ID': 'test_id'
            }
            
            headers = client._generate_headers('test_consumer', 'test_key', 'prod')
            
            self.assertIn('Content-Type', headers)
            self.assertIn('WM_SEC.AUTH_SIGNATURE', headers)
            self.assertEqual(headers['WM_SVC.ENV'], 'prod')
    
    @patch('src.integration.llm_client.requests.post')
    @patch('builtins.open', create=True)
    def test_call_llm_success(self, mock_open, mock_post):
        """Test successful LLM call"""
        # Mock PEM file
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Test response'}}
            ],
            'usage': {'total_tokens': 100}
        }
        mock_post.return_value = mock_response
        
        client = LLMClient()
        result = client.call_llm("Test prompt")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], 'Test response')
        self.assertEqual(result['tokens_used'], 100)
    
    @patch('src.integration.llm_client.requests.post')
    @patch('builtins.open', create=True)
    def test_call_llm_failure(self, mock_open, mock_post):
        """Test LLM call failure"""
        # Mock PEM file
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key'
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        mock_post.return_value = mock_response
        
        client = LLMClient()
        result = client.call_llm("Test prompt")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('src.integration.llm_client.requests.post')
    @patch('builtins.open', create=True)
    def test_call_llm_with_retry(self, mock_open, mock_post):
        """Test LLM call with retry logic"""
        # Mock PEM file
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key'
        
        # Mock responses - fail first, succeed second
        mock_response_fail = Mock()
        mock_response_fail.status_code = 429  # Rate limit
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'choices': [{'message': {'content': 'Success after retry'}}],
            'usage': {'total_tokens': 50}
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        client = LLMClient()
        client.max_retries = 2
        
        result = client.call_llm("Test prompt")
        
        # Should succeed after retry
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('builtins.open', create=True)
    def test_call_llm_full_parameters(self, mock_open):
        """Test call_llm_full with all parameters"""
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key'
        
        client = LLMClient()
        
        with patch('src.integration.llm_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{'message': {'content': 'Response'}}],
                'usage': {'total_tokens': 75}
            }
            mock_post.return_value = mock_response
            
            result = client.call_llm_full(
                query="Test query",
                pem_file_path="/test/path.pem",
                consumer_id="test_id",
                model="gpt-4",
                max_tokens=1500,
                temperature=0.7,
                system_message="You are a helpful assistant",
                context="Additional context"
            )
            
            self.assertTrue(result['success'])
            mock_post.assert_called_once()

class TestLLMClientEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_initialization_without_env_vars(self):
        """Test initialization without environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient()
            
            # Should use defaults
            self.assertIsNotNone(client.gateway_url)
            self.assertIsNotNone(client.model)
    
    @patch('builtins.open', create=True)
    def test_call_llm_with_invalid_json_response(self, mock_open):
        """Test handling invalid JSON in response"""
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key'
        
        client = LLMClient()
        
        with patch('src.integration.llm_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.text = "Not valid JSON"
            mock_post.return_value = mock_response
            
            result = client.call_llm("Test prompt")
            
            self.assertFalse(result['success'])
    
    @patch('builtins.open', create=True)
    def test_call_llm_timeout(self, mock_open):
        """Test handling timeout"""
        mock_open.return_value.__enter__.return_value.read.return_value = 'test_key'
        
        client = LLMClient()
        
        with patch('src.integration.llm_client.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.Timeout("Connection timeout")
            
            result = client.call_llm("Test prompt")
            
            self.assertFalse(result['success'])
            self.assertIn('timeout', result.get('error', '').lower())

if __name__ == '__main__':
    unittest.main()
