"""
LLM Provider Abstraction Layer

Supports multiple LLM providers with unified interface for chat completions.
"""

import os
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM provider"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time: Optional[float] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace('provider', '')
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        """Generate chat completion response"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get available models and capabilities"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv(config.get('api_key_env', 'OPENAI_API_KEY'))
        self.client = None
        
    def _get_client(self):
        """Lazy loading of OpenAI client"""
        if self.client is None:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai>=1.0.0")
        return self.client
    
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        """Generate chat completion using OpenAI API"""
        start_time = time.time()
        
        if not model:
            model = self.config['models']['coding']
            
        client = self._get_client()
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=model,
                provider='openai',
                tokens_used=response.usage.total_tokens if response.usage else None,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        return {
            'provider': 'openai',
            'available_models': list(self.config['models'].values()),
            'capabilities': ['chat', 'text_generation', 'code_generation']
        }
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration"""
        return bool(self.api_key and 'models' in self.config)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv(config.get('api_key_env', 'ANTHROPIC_API_KEY'))
        self.client = None
        
    def _get_client(self):
        """Lazy loading of Anthropic client"""
        if self.client is None:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic>=0.8.0")
        return self.client
    
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        """Generate chat completion using Anthropic API"""
        start_time = time.time()
        
        if not model:
            model = self.config['models']['coding']
            
        client = self._get_client()
        
        # Convert messages format for Anthropic
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append(msg)
        
        try:
            response = client.messages.create(
                model=model,
                max_tokens=kwargs.get('max_tokens', 4000),
                system=system_message,
                messages=user_messages
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=model,
                provider='anthropic',
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information"""
        return {
            'provider': 'anthropic',
            'available_models': list(self.config['models'].values()),
            'capabilities': ['chat', 'text_generation', 'code_generation', 'analysis']
        }
    
    def validate_config(self) -> bool:
        """Validate Anthropic configuration"""
        return bool(self.api_key and 'models' in self.config)


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.client = None
        
    def _get_client(self):
        """Lazy loading of Ollama client"""
        if self.client is None:
            try:
                import requests
                self.client = requests.Session()
            except ImportError:
                raise ImportError("requests package not installed")
        return self.client
    
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        """Generate chat completion using Ollama API"""
        start_time = time.time()
        
        if not model:
            model = self.config['models']['coding']
            
        client = self._get_client()
        
        try:
            # Convert messages to prompt for Ollama
            prompt = self._messages_to_prompt(messages)
            
            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                }
            )
            response.raise_for_status()
            
            result = response.json()
            
            return LLMResponse(
                content=result['response'],
                model=model,
                provider='ollama',
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert chat messages to single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model information"""
        try:
            client = self._get_client()
            response = client.get(f"{self.base_url}/api/tags")
            models = response.json().get('models', [])
            available_models = [model['name'] for model in models]
        except Exception:
            available_models = list(self.config['models'].values())
            
        return {
            'provider': 'ollama',
            'available_models': available_models,
            'capabilities': ['chat', 'text_generation', 'code_generation']
        }
    
    def validate_config(self) -> bool:
        """Validate Ollama configuration"""
        try:
            client = self._get_client()
            response = client.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv(config.get('api_key_env', 'DEEPSEEK_API_KEY'))
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
        self.client = None
        
    def _get_client(self):
        """Lazy loading of requests session for DeepSeek"""
        if self.client is None:
            try:
                import requests
                self.client = requests.Session()
            except ImportError:
                raise ImportError("requests package not installed")
        return self.client
    
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        """Generate chat completion using DeepSeek API"""
        start_time = time.time()
        
        if not model:
            model = self.config['models']['coding']
            
        client = self._get_client()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 4000),
        }
        
        try:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            
            return LLMResponse(
                content=result['choices'][0]['message']['content'],
                model=model,
                provider='deepseek',
                tokens_used=result.get('usage', {}).get('total_tokens'),
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get DeepSeek model information"""
        return {
            'provider': 'deepseek',
            'available_models': list(self.config['models'].values()),
            'capabilities': ['chat', 'text_generation', 'code_generation']
        }
    
    def validate_config(self) -> bool:
        """Validate DeepSeek configuration"""
        return bool(self.api_key and self.api_key != "YOUR_DEEPSEEK_API_KEY" and 'models' in self.config)


class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    PROVIDERS = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'ollama': OllamaProvider,
        'deepseek': DeepSeekProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> LLMProvider:
        """Create LLM provider instance"""
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_class = cls.PROVIDERS[provider_name]
        provider = provider_class(config)
        
        if not provider.validate_config():
            raise ValueError(f"Invalid configuration for provider: {provider_name}")
        
        return provider
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names"""
        return list(cls.PROVIDERS.keys())


class LLMManager:
    """Manager for handling multiple LLM providers with fallbacks"""
    
    def __init__(self, provider_configs: Dict[str, Dict]):
        self.providers = {}
        self.primary_provider = None
        
        for provider_name, config in provider_configs.items():
            try:
                provider = LLMProviderFactory.create_provider(provider_name, config)
                self.providers[provider_name] = provider
                if self.primary_provider is None:
                    self.primary_provider = provider_name
                logger.info(f"Initialized {provider_name} provider")
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_name} provider: {e}")
    
    def chat_completion(self, messages: List[Dict], provider_name: str = None, 
                       model_type: str = 'coding', **kwargs) -> LLMResponse:
        """Generate chat completion with fallback support"""
        providers_to_try = []
        
        if provider_name and provider_name in self.providers:
            providers_to_try.append(provider_name)
        
        # Add other providers as fallbacks
        for name in self.providers:
            if name not in providers_to_try:
                providers_to_try.append(name)
        
        last_error = None
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                model = provider.config['models'].get(model_type)
                return provider.chat_completion(messages, model, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    def get_provider_status(self) -> Dict[str, Dict]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            try:
                info = provider.get_model_info()
                status[name] = {'status': 'available', 'info': info}
            except Exception as e:
                status[name] = {'status': 'error', 'error': str(e)}
        return status