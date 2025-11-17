"""
LLM Client with flexible parameter handling.

This module provides a clean interface for LLM interactions with two main approaches:
1. Full parameter control via method arguments
2. Simplified prompt-only interface using environment configuration
"""

import os
import sys
import json
import time
import base64
import logging
import argparse
from typing import Optional, Dict, Any, Union
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA256
from base64 import b64encode
import requests
import urllib3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress SSL warnings for staging environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logging.handlers

# Create logs directory if it doesn't exist
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, "llm_client.log"),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=10,
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)

class LLMClient:
    """Professional LLM Client with flexible parameter handling."""
    
    def __init__(self):
        """Initialize the LLM client with environment-based configuration."""
        # Try to use existing credential paths from .env
        credentials_path = os.getenv("CREDENTIALS_PATH", "/Users/n0m08hp/RiskAgentAnalyzer")
        
        # Set up authentication paths - use existing env vars if available, otherwise try standard paths
        self.pem_file_path = os.getenv("CONSUMER_PEM_FILE_PATH")
        if not self.pem_file_path and credentials_path:
            # Try common PEM file names in credentials directory
            for pem_name in ["private_key.pem"]:
                potential_path = os.path.join(credentials_path, pem_name)
                if os.path.exists(potential_path):
                    self.pem_file_path = potential_path
                    break
        
        self.consumer_id = os.getenv("CONSUMER_ID")
        self.ca_bundle_path = os.getenv("CA_BUNDLE_PATH")
        
        # Gateway configuration - use existing Walmart settings as fallback
        self.gateway_url = os.getenv("LLM_GATEWAY_URL") or os.getenv("WALMART_LLM_GATEWAY_URL", "https://wmtllmgateway.stage.walmart.com/wmtllmgateway/v1/openai")
        self.gateway_key = os.getenv("WALMART_LLM_GATEWAY_KEY")
        
        # Model configuration
        self.model = os.getenv("LLM_MODEL") or os.getenv("WALMART_LLM_MODEL", "gpt-4o-mini")
        self.model_version = os.getenv("LLM_MODEL_VERSION", "2024-07-18")
        self.api_version = os.getenv("LLM_API_VERSION", "2023-05-15")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.verify_ssl = os.getenv("LLM_VERIFY_SSL", "false").lower() == "true"
        
        # Load PEM key if available (optional for some authentication methods)
        self.key_content = None
        if self.pem_file_path and os.path.exists(self.pem_file_path):
            try:
                self._load_pem_key()
            except Exception as e:
                logger.warning(f"Could not load PEM key from {self.pem_file_path}: {e}")
                self.pem_file_path = None
    
    def _load_pem_key(self) -> None:
        """Load the PEM key from the configured file path."""
        if not self.pem_file_path:
            raise ValueError("PEM file path not configured")
            
        try:
            with open(self.pem_file_path, 'r') as f:
                self.key_content = f.read()
            logger.debug(f"Successfully loaded PEM key from: {self.pem_file_path}")
        except Exception as e:
            logger.error(f"Failed to load PEM key: {e}")
            raise ValueError(f"Could not read PEM file: {e}")
    
    def _generate_signature(self, consumer_id: str, key_content: str) -> Dict[str, str]:
        """Generate authentication signature for API request."""
        key_version = "1"
        epoch_time = int(time.time()) * 1000
        data = consumer_id + "\n" + str(epoch_time) + "\n" + key_version + "\n"
        
        try:
            rsakey = RSA.importKey(key_content)
            signer = PKCS1_v1_5.new(rsakey)
            digest = SHA256.new()
            digest.update(data.encode("utf-8"))
            sign = signer.sign(digest)
            
            return {
                "WM_SEC.AUTH_SIGNATURE": b64encode(sign).decode("utf-8"),
                "WM_CONSUMER.INTIMESTAMP": str(epoch_time),
                "WM_CONSUMER.ID": consumer_id,
            }
        except Exception as e:
            logger.error(f"Failed to generate signature: {e}")
            raise ValueError(f"Signature generation failed: {e}")
    
    def _generate_headers(self, consumer_id: str, key_content: str, environment: str = "stage") -> Dict[str, str]:
        """Generate complete headers for API request."""
        # Base headers
        base_headers = {
            "Content-Type": "application/json",
            "WM_SEC.KEY_VERSION": "1",
            "WM_SVC.ENV": environment,
            "WM_SVC.NAME": "WMTLLMGATEWAY",
            "WM_CONSUMER.ACCOUNT_ID": "benefits_agent",
        }
        
        # Add authentication headers
        auth_headers = self._generate_signature(consumer_id, key_content)
        
        # Combine all headers
        headers = {**base_headers, **auth_headers}
        return headers
    
    def call_llm_full(self,
                     query: str,
                     pem_file_path: Optional[str] = None,
                     consumer_id: Optional[str] = None,
                     ca_bundle_path: Optional[str] = None,
                     gateway_url: Optional[str] = None,
                     model: Optional[str] = None,
                     model_version: Optional[str] = None,
                     api_version: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     timeout: Optional[int] = None,
                     verify_ssl: Optional[bool] = None,
                     system_message: Optional[str] = None,
                     context: Optional[str] = None) -> Dict[str, Any]:
        """
        Call LLM with full parameter control.
        
        This method accepts all possible parameters as method arguments,
        allowing complete control over the API call configuration.
        
        Args:
            query: The user query/prompt
            pem_file_path: Path to PEM file for authentication
            consumer_id: Consumer ID for authentication
            ca_bundle_path: Path to CA bundle for SSL verification
            gateway_url: LLM Gateway URL
            model: Model name
            model_version: Model version
            api_version: API version
            max_tokens: Maximum tokens for response
            temperature: Temperature for response generation
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            system_message: Optional system message
            context: Optional context for RAG mode
            
        Returns:
            Dictionary containing response data and metadata
        """
        # Use provided parameters or fall back to instance defaults
        pem_path = pem_file_path or self.pem_file_path
        cons_id = consumer_id or self.consumer_id
        ca_bundle = ca_bundle_path or self.ca_bundle_path
        gw_url = gateway_url or self.gateway_url
        model_name = model or self.model
        model_ver = model_version or self.model_version
        api_ver = api_version or self.api_version
        max_tok = max_tokens or self.max_tokens
        temp = temperature or self.temperature
        req_timeout = timeout or self.timeout
        ssl_verify = verify_ssl if verify_ssl is not None else self.verify_ssl
        
        # Validate authentication - either PEM-based or gateway key
        use_pem_auth = bool(pem_path and cons_id)
        use_gateway_key = bool(self.gateway_key)
        
        if not use_pem_auth and not use_gateway_key:
            raise ValueError("Either PEM file path + consumer ID or gateway key is required for authentication")
        
        headers = {}
        
        if use_pem_auth:
            # Validate PEM parameters
            if not pem_path or not cons_id:
                raise ValueError("PEM file path and consumer ID are required for PEM authentication")
                
            # Load PEM key if different from instance
            key_content = self.key_content
            if pem_path != self.pem_file_path:
                try:
                    with open(pem_path, 'r') as f:
                        key_content = f.read()
                except Exception as e:
                    raise ValueError(f"Could not read PEM file {pem_path}: {e}")
            
            if not key_content:
                raise ValueError("No valid PEM key content available")
            
            # Generate PEM-based headers
            headers = self._generate_headers(cons_id, key_content, "stage")
        
        elif use_gateway_key:
            # Use simpler gateway key authentication
            headers = {
                "Authorization": f"Bearer {self.gateway_key}",
                "Content-Type": "application/json"
            }
        
        # Prepare request payload - use simple format for Walmart LLM Gateway
        if use_gateway_key:
            # Use simple Walmart gateway format
            payload = {
                "model": model_name,
                "prompt": query,
                "max_tokens": max_tok,
                "temperature": temp
            }
            url = f"{gw_url}/generate" if not gw_url.endswith('/generate') else gw_url
        else:
            # Use more complex format for PEM-based authentication
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            elif context:
                system_msg = f"""You are a helpful assistant. Answer questions based on the provided context.
                
                Context: {context}

                Answer the user's question based on this context. If the context doesn't contain the information needed, 
                say "I don't have information about that in the provided context.\""""
                messages.append({"role": "system", "content": system_msg})
            
            messages.append({"role": "user", "content": query})
            
            payload = {
                "model": model_name,
                "model-version": model_ver,
                "api-version": api_ver,
                "task": "chat/completions",
                "model-params": {
                    "messages": messages,
                    "max_tokens": max_tok,
                    "temperature": temp,
                }
            }
            url = gw_url
        
        # Configure SSL verification (matching standalone_llm_caller.py pattern)
        if ssl_verify and ca_bundle:
            verify_param = ca_bundle
        elif ssl_verify:
            verify_param = True
        else:
            verify_param = False
        
        # Make API request
        start_time = time.time()
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=req_timeout,
                verify=verify_param
            )
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Request URL: {url}")
                logger.error(f"Request payload: {payload}")
                try:
                    error_detail = response.json()
                    logger.error(f"Error response: {error_detail}")
                except:
                    error_detail = response.text
                    logger.error(f"Error response (raw): {error_detail}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "error_detail": error_detail,
                    "response_time_ms": response_time_ms
                }
            
            response_json = response.json()
            content = self._extract_response_text(response_json)
            token_usage = self._extract_token_usage(response_json)
            
            return {
                "success": True,
                "response": content,
                "token_usage": token_usage,
                "response_time_ms": response_time_ms,
                "status_code": response.status_code,
                "model": model_name,
                "parameters": {
                    "max_tokens": max_tok,
                    "temperature": temp
                }
            }
            
        except requests.exceptions.RequestException as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": response_time_ms
            }
    
    def call_llm(self, query: str, system_message: Optional[str] = None, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Simplified LLM call using environment configuration.
        
        This method only requires the prompt and optionally system message or context.
        All other parameters are loaded from environment variables (.env file).
        
        Args:
            query: The user query/prompt
            system_message: Optional system message
            context: Optional context for RAG mode
            
        Returns:
            Dictionary containing response data and metadata
        """
        return self.call_llm_full(
            query=query,
            system_message=system_message,
            context=context
        )
    
    def _extract_response_text(self, response_json: Dict[str, Any]) -> str:
        """Extract response text from API response."""
        try:
            # Handle Walmart LLM Gateway format (simple response field)
            if "response" in response_json:
                return response_json["response"]
            
            # Handle OpenAI-style format (choices array)
            if "choices" in response_json and len(response_json["choices"]) > 0:
                choice = response_json["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            
            # Handle other possible formats
            if "content" in response_json:
                return response_json["content"]
            
            logger.warning(f"Unexpected response format: {response_json}")
            return "Error: Could not extract response from API"
            
        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            return f"Error: {e}"
    
    def _extract_token_usage(self, response_json: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Extract token usage from API response."""
        try:
            if "usage" in response_json:
                usage = response_json["usage"]
                return {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
        except Exception as e:
            logger.debug(f"Could not extract token usage: {e}")
        
        return None
    
    def test_connection(self) -> bool:
        """Test the connection to the LLM service."""
        try:
            result = self.call_llm("Hello", system_message="Respond with just 'OK'")
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

def create_client() -> LLMClient:
    """Factory function to create a configured LLM client."""
    return LLMClient()

def main():
    """Command line interface for the LLM client."""
    parser = argparse.ArgumentParser(
        description='Professional LLM Client',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--query', required=True, help='Query to send to the LLM')
    
    # Optional override arguments
    parser.add_argument('--pem-file', help='Path to PEM file for authentication')
    parser.add_argument('--consumer-id', help='Consumer ID for authentication')
    parser.add_argument('--ca-bundle', help='Path to CA bundle for SSL verification')
    parser.add_argument('--gateway-url', help='LLM Gateway URL')
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--model-version', help='Model version')
    parser.add_argument('--api-version', help='API version')
    parser.add_argument('--max-tokens', type=int, help='Maximum tokens for response')
    parser.add_argument('--temperature', type=float, help='Temperature for response generation')
    parser.add_argument('--timeout', type=int, help='Request timeout in seconds')
    parser.add_argument('--verify-ssl', action='store_true', help='Enable SSL verification')
    parser.add_argument('--system-message', help='System message for the conversation')
    parser.add_argument('--context', help='Context for RAG mode')
    parser.add_argument('--simple', action='store_true', 
                       help='Use simple call_llm method (environment-only configuration)')
    
    args = parser.parse_args()
    
    try:
        client = LLMClient()
        
        if args.simple:
            # Use simplified method
            result = client.call_llm(
                query=args.query,
                system_message=args.system_message,
                context=args.context
            )
        else:
            # Use full parameter method
            result = client.call_llm_full(
                query=args.query,
                pem_file_path=args.pem_file,
                consumer_id=args.consumer_id,
                ca_bundle_path=args.ca_bundle,
                gateway_url=args.gateway_url,
                model=args.model,
                model_version=args.model_version,
                api_version=args.api_version,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                timeout=args.timeout,
                verify_ssl=args.verify_ssl,
                system_message=args.system_message,
                context=args.context
            )
        
        if result["success"]:
            print("Response:", "success")
            if result.get("token_usage"):
                print(f"Token Usage: {result['token_usage']}")
            print(f"Response Time: {result['response_time_ms']}ms")
        else:
            logger.error(f"Error: {result['error']}")
            if result.get("error_detail"):
                logger.error(f"Details: {result['error_detail']}")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

def get_llm_response(prompt, system_prompt=None, max_tokens=None, temperature=None, **kwargs):
    """
    Get LLM response for a given prompt.
    
    Args:
        prompt (str): The input prompt/query
        system_prompt (str, optional): Optional system message/prompt
        max_tokens (int, optional): Maximum tokens for response
        temperature (float, optional): Temperature for response generation
        **kwargs: Additional parameters to pass to the LLM client
        
    Returns:
        dict: Dictionary containing LLM response data
    """
    client = LLMClient()
    result = client.call_llm_full(
        query=prompt, 
        system_message=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )
    # # Extract just the response content
    if result.get('success'):
        response_text = result.get('response', 'No response')
        logger.debug(f"\n Response: {response_text}")
        logger.info(f"\n  Time: {result.get('response_time_ms')}ms")
        logger.info(f" Tokens: {result.get('token_usage', {}).get('total_tokens', 0)}")
    else:
        logger.error(f" Error: {result.get('error')}")

    return result

if __name__ == "__main__":
    main()