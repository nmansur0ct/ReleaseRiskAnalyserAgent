"""
LLM Integration Module
Provides unified interface for different LLM providers with environment configuration
"""

import asyncio
import os
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import logging
import functools

from typing import Protocol

class EnvConfigProtocol(Protocol):
    def get_llm_config(self) -> Dict[str, Any]:
        ...

try:
    from environment_config import get_env_config
except ImportError:
    # Fallback for standalone execution
    import os
    class MockEnvConfig:
        def get_llm_config(self) -> Dict[str, Any]:
            return {
                'provider': os.getenv('LLM_PROVIDER', 'mock'),
                'walmart_llm_gateway_url': os.getenv('WALMART_LLM_GATEWAY_URL', 'https://wmtllmgateway.stage.walmart.com/wmtllmgateway'),
                'walmart_llm_gateway_key': os.getenv('WALMART_LLM_GATEWAY_KEY'),
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
            }
    def get_env_config() -> EnvConfigProtocol:
        return MockEnvConfig()

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration"""
        return bool(self.api_key and self.client)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI"""
        if not self.validate_config():
            raise ValueError("OpenAI provider not properly configured")
        
        if self.client is None:
            raise ValueError("OpenAI client is not initialized. Please install the openai package.")
        
        try:

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=kwargs.get('max_tokens', 1500),
                    temperature=kwargs.get('temperature', 0.7)
                )
            )

            content = response.choices[0].message.content
            return content if content is not None else ""
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic package not installed. Install with: pip install anthropic")
    
    def validate_config(self) -> bool:
        """Validate Anthropic configuration"""
        return bool(self.api_key and self.client)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic"""

        if not self.validate_config():
            raise ValueError("Anthropic provider not properly configured")
        
        if self.client is None:
            raise ValueError("Anthropic client is not initialized. Please install the anthropic package.")
        
        try:

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=kwargs.get('max_tokens', 1500),
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )
            )

            # Extract text from TextBlock objects only
            text_content = ""
            for content_block in response.content:
                # Check if it's a TextBlock with text attribute
                if hasattr(content_block, 'text') and hasattr(content_block, 'type') and content_block.type == 'text':
                    text_content += content_block.text
                # For other block types, check if they have a string representation or specific text fields
                elif hasattr(content_block, 'text') and not hasattr(content_block, 'type'):
                    text_content += content_block.text
            return text_content
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

class WalmartLLMGatewayProvider(LLMProvider):
    """Walmart LLM Gateway provider"""
    
    def __init__(self, gateway_url: Optional[str] = None, gateway_key: Optional[str] = None, model: str = "gpt-4"):
        self.gateway_url = gateway_url or os.getenv('WALMART_LLM_GATEWAY_URL')
        self.gateway_key = gateway_key or os.getenv('WALMART_LLM_GATEWAY_KEY')
        self.model = model
        self.client = None
        
        if self.gateway_url and self.gateway_key:
            try:
                import requests
                self.client = requests.Session()
                self.client.headers.update({
                    'Authorization': f'Bearer {self.gateway_key}',
                    'Content-Type': 'application/json'
                })
            except ImportError:
                logger.warning("requests package not installed. Install with: pip install requests")
    
    def validate_config(self) -> bool:
        """Validate Walmart LLM Gateway configuration"""
        return bool(self.gateway_url and self.gateway_key and self.client)
    
    async def generate(self, prompt: str, **kwargs) -> str:

        """ Generate response using Walmart LLM Gateway"""
        if not self.validate_config():
            raise ValueError("Walmart LLM Gateway provider not properly configured")
        
        if self.client is None:
            raise ValueError("Walmart LLM Gateway client is not initialized. Please install the requests package.")
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": kwargs.get('max_tokens', 1500),
                "temperature": kwargs.get('temperature', 0.7)
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                functools.partial(self.client.post, f"{self.gateway_url}/generate", json=payload)
            )
            
            response.raise_for_status()
            return response.json()['response']
            
        except Exception as e:
            logger.error(f"Walmart LLM Gateway API call failed: {e}")
            raise

class MockProvider(LLMProvider):
    """Mock provider for testing"""
    
    def __init__(self):
        pass
    
    def validate_config(self) -> bool:
        """Mock provider is always valid"""
        return True
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response"""
        await asyncio.sleep(0.05)  # Simulate minimal delay
        return f"This is a mock response for testing purposes. The prompt was: {prompt[:100]}..."

class LLMManager:
    """Manages LLM providers and handles fallback logic"""
    
    def __init__(self):
        self.env_config = get_env_config()
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize LLM providers based on environment configuration"""
        llm_config = self.env_config.get_llm_config()
        
        # Initialize Walmart LLM Gateway provider
        if llm_config.get('walmart_llm_gateway_url') and llm_config.get('walmart_llm_gateway_key'):
            self.providers['walmart_llm_gateway'] = WalmartLLMGatewayProvider(
                gateway_url=llm_config['walmart_llm_gateway_url'],
                gateway_key=llm_config['walmart_llm_gateway_key'],
                model=llm_config.get('walmart_llm_model', 'gpt-4')
            )
        
        # Initialize OpenAI provider
        if llm_config.get('openai_api_key'):
            self.providers['openai'] = OpenAIProvider(
                api_key=llm_config['openai_api_key'],
                model=llm_config.get('openai_model', 'gpt-4')
            )
        
        # Initialize Anthropic provider
        if llm_config.get('anthropic_api_key'):
            self.providers['anthropic'] = AnthropicProvider(
                api_key=llm_config['anthropic_api_key'],
                model=llm_config.get('anthropic_model', 'claude-3-sonnet-20240229')
            )
        
        # Always have mock provider available
        self.providers['mock'] = MockProvider()
        
        logger.info(f"Initialized LLM providers: {list(self.providers.keys())}")
    
    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get specific LLM provider"""
        return self.providers.get(provider_name)
    
    async def generate_with_fallback(self, 
                                   prompt: str, 
                                   primary_provider: Optional[str] = None,
                                   fallback_provider: Optional[str] = None,
                                   **kwargs) -> Dict[str, Any]:
        """
        Generate response with automatic fallback
        
        Args:
            prompt: The prompt to send to the LLM
            primary_provider: Primary LLM provider to try
            fallback_provider: Fallback provider if primary fails
            **kwargs: Additional arguments for the LLM
        
        Returns:
            Dict containing response, provider used, and any errors
        """
        llm_config = self.env_config.get_llm_config()
        
        # Use environment config if providers not specified
        if primary_provider is None:
            primary_provider = llm_config.get('provider', 'openai')
        if fallback_provider is None:
            fallback_provider = llm_config.get('fallback_provider', 'anthropic')
        
        # Try primary provider
        if primary_provider in self.providers:
            provider = self.providers[primary_provider]
            if provider.validate_config():
                try:
                    response = await provider.generate(prompt, **kwargs)
                    return {
                        'response': response,
                        'provider_used': primary_provider,
                        'success': True,
                        'errors': []
                    }
                except Exception as e:
                    logger.warning(f"Primary provider {primary_provider} failed: {e}")
        
        # Try fallback provider
        if fallback_provider in self.providers:
            provider = self.providers[fallback_provider]
            if provider.validate_config():
                try:
                    response = await provider.generate(prompt, **kwargs)
                    return {
                        'response': response,
                        'provider_used': fallback_provider,
                        'success': True,
                        'errors': [f"Primary provider {primary_provider} failed, used fallback"]
                    }
                except Exception as e:
                    logger.warning(f"Fallback provider {fallback_provider} failed: {e}")
        
        # Final fallback to mock provider
        if 'mock' in self.providers:
            try:
                response = await self.providers['mock'].generate(prompt, **kwargs)
                return {
                    'response': response,
                    'provider_used': 'mock',
                    'success': True,
                    'errors': [f"Both {primary_provider} and {fallback_provider} failed, used mock"]
                }
            except Exception as e:
                logger.error(f"Even mock provider failed: {e}")
        
        # Complete failure
        return {
            'response': '',
            'provider_used': None,
            'success': False,
            'errors': [f"All providers failed for prompt: {prompt[:50]}..."]
        }
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate all provider configurations"""
        validation_results = {}
        for name, provider in self.providers.items():
            validation_results[name] = provider.validate_config()
        return validation_results
    
    def get_available_providers(self) -> List[str]:
        """Get list of available and configured providers"""
        available = []
        for name, provider in self.providers.items():
            if provider.validate_config():
                available.append(name)
        return available

# Global LLM manager instance
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

def reload_llm_manager():
    """Reload the global LLM manager with updated configuration"""
    global _llm_manager
    _llm_manager = LLMManager()

# Convenience functions for common operations
async def generate_analysis(prompt: str, provider: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Convenience function for generating Agent LLM analysis - You are an Agent doing code change analysis"""
    manager = get_llm_manager()
    return await manager.generate_with_fallback(prompt, primary_provider=provider, **kwargs)

async def analyze_code_changes(changes: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
    """You are an Agent doing code change analysis using LLM"""
    prompt = f"""
    You are an Agent doing analysis of the following code changes for risk assessment:
    
    Files changed: {changes.get('changed_files', [])}
    Additions: {changes.get('additions', 0)}
    Deletions: {changes.get('deletions', 0)}
    Title: {changes.get('title', '')}
    Description: {changes.get('body', '')}
    
    As an Agent, please provide:
    1. Risk level (low/medium/high)
    2. Affected modules
    3. Potential security concerns
    4. Deployment recommendations
    
    Respond in JSON format.
    """
    
    return await generate_analysis(prompt, provider)

async def analyze_security_patterns(file_content: str, patterns: Dict[str, str], provider: Optional[str] = None) -> Dict[str, Any]:
    """You are an Agent doing security pattern analysis"""
    prompt = f"""
    You are an Agent doing analysis of the following code for security vulnerabilities:
    
    Code:
    {file_content[:2000]}  # Limit content size
    
    As an Agent, check for these patterns:
    {patterns}
    
    Provide findings in JSON format with:
    - pattern_matches: array of matched patterns
    - severity: low/medium/high
    - recommendations: array of remediation steps
    """
    
    return await generate_analysis(prompt, provider)