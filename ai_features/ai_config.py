"""
AI Configuration System

Manages configuration for LLM providers and AI features.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    planning: str
    coding: str
    analysis: str


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    models: ModelConfig
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30


class AIConfig:
    """AI configuration manager"""
    
    DEFAULT_CONFIG = {
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "models": {
                "planning": "gpt-4o-mini",
                "coding": "gpt-4o",
                "analysis": "gpt-4o-mini"
            },
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 30
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "models": {
                "planning": "claude-3-haiku-20240307",
                "coding": "claude-3-sonnet-20240229",
                "analysis": "claude-3-haiku-20240307"
            },
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 30
        },
        "deepseek": {
            "api_key_env": "DEEPSEEK_API_KEY",
            "base_url": "https://api.deepseek.com/v1",
            "models": {
                "planning": "deepseek-chat",
                "coding": "deepseek-coder",
                "analysis": "deepseek-chat"
            },
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 30
        },
        "ollama": {
            "base_url": "http://ci.infra:11434",
            "models": {
                "planning": "qwen3-coder:30b",
                "coding": "qwen3-coder:30b",
                "analysis": "qwen3-coder:30b"
            },
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60
        }
    }
    
    MEMORY_CONFIG = {
        "storage_path": "ai_features/data/memory",
        "max_memory_size_mb": 100,
        "cleanup_older_than_days": 30,
        "auto_analyze_on_conversion": True,
        "store_full_content": False,  # Store patterns and summaries only
        "content_sample_size": 1000   # Characters to sample from files
    }
    
    WORKFLOW_CONFIG = {
        "max_todo_items": 50,
        "auto_prioritize": True,
        "require_user_approval": True,
        "backup_before_changes": True,
        "validate_changes": True,
        "parallel_execution": False,
        "max_file_size_kb": 500,      # Max file size to edit
        "excluded_file_types": [".jpg", ".png", ".gif", ".pdf", ".zip"]
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "ai_config.json"
        self.template_file = "ai_config.template.json"
        self.local_file = "ai_config.local.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from template and local files"""
        # Start with defaults
        config = {
            "providers": self.DEFAULT_CONFIG.copy(),
            "memory": self.MEMORY_CONFIG.copy(),
            "workflow": self.WORKFLOW_CONFIG.copy(),
            "active_provider": "deepseek"
        }
        
        # Load template config (static settings)
        if os.path.exists(self.template_file):
            try:
                with open(self.template_file, 'r') as f:
                    template_config = json.load(f)
                config = self._merge_with_defaults(template_config)
                logger.info(f"Loaded template config from {self.template_file}")
            except Exception as e:
                logger.warning(f"Failed to load template config {self.template_file}: {e}")
        
        # Load local config (user settings like active_provider)
        if os.path.exists(self.local_file):
            try:
                with open(self.local_file, 'r') as f:
                    local_config = json.load(f)
                # Merge local settings (active_provider, etc.)
                if "active_provider" in local_config:
                    config["active_provider"] = local_config["active_provider"]
                logger.info(f"Loaded local config from {self.local_file}")
            except Exception as e:
                logger.warning(f"Failed to load local config {self.local_file}: {e}")
        
        # Fallback to old config file if new files don't exist
        elif os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    old_config = json.load(f)
                config = self._merge_with_defaults(old_config)
                logger.info(f"Loaded legacy config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        return config
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults"""
        default_config = {
            "providers": self.DEFAULT_CONFIG.copy(),
            "memory": self.MEMORY_CONFIG.copy(),
            "workflow": self.WORKFLOW_CONFIG.copy(),
            "active_provider": "deepseek"
        }
        
        # Deep merge logic
        for section in ["providers", "memory", "workflow"]:
            if section in config:
                if section == "providers":
                    for provider, provider_config in config[section].items():
                        if provider in default_config[section]:
                            default_config[section][provider].update(provider_config)
                        else:
                            default_config[section][provider] = provider_config
                else:
                    default_config[section].update(config[section])
        
        if "active_provider" in config:
            default_config["active_provider"] = config["active_provider"]
        
        return default_config
    
    def save_config(self) -> bool:
        """Save user-specific configuration to local file"""
        try:
            # Only save user-specific settings to local file
            local_config = {
                "active_provider": self.config.get("active_provider", "deepseek")
            }
            
            with open(self.local_file, 'w') as f:
                json.dump(local_config, f, indent=2)
            logger.info(f"Saved user config to {self.local_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save local config: {e}")
            return False
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific provider"""
        return self.config["providers"].get(provider_name)
    
    def get_active_provider(self) -> str:
        """Get name of active provider"""
        return self.config.get("active_provider", "openai")
    
    def set_active_provider(self, provider_name: str) -> bool:
        """Set active provider"""
        if provider_name in self.config["providers"]:
            self.config["active_provider"] = provider_name
            return True
        return False
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory system configuration"""
        return self.config["memory"]
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration"""
        return self.config["workflow"]
    
    def validate_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Validate provider configuration and return status"""
        provider_config = self.get_provider_config(provider_name)
        if not provider_config:
            return {"valid": False, "error": "Provider not configured"}
        
        required_fields = ["models"]
        missing_fields = []
        
        for field in required_fields:
            if field not in provider_config:
                missing_fields.append(field)
        
        # Check model configuration
        if "models" in provider_config:
            models = provider_config["models"]
            required_models = ["planning", "coding", "analysis"]
            missing_models = [model for model in required_models if model not in models]
            if missing_models:
                missing_fields.extend([f"models.{model}" for model in missing_models])
        
        # Check API key for cloud providers
        if provider_name in ["openai", "anthropic", "deepseek"]:
            api_key_env = provider_config.get("api_key_env")
            if not api_key_env or not os.getenv(api_key_env):
                return {
                    "valid": False, 
                    "error": f"API key not found in environment variable: {api_key_env}"
                }
        
        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        return {"valid": True}
    
    def get_all_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get validation status for all providers"""
        status = {}
        for provider_name in self.config["providers"]:
            status[provider_name] = self.validate_provider_config(provider_name)
        return status
    
    def update_provider_config(self, provider_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update provider configuration"""
        if provider_name not in self.config["providers"]:
            self.config["providers"][provider_name] = {}
        
        self.config["providers"][provider_name].update(config_updates)
        return True
    
    def add_custom_provider(self, provider_name: str, config: Dict[str, Any]) -> bool:
        """Add custom provider configuration"""
        required_fields = ["models"]
        if not all(field in config for field in required_fields):
            return False
        
        self.config["providers"][provider_name] = config
        return True
    
    def get_model_for_task(self, task_type: str, provider_name: str = None) -> str:
        """Get appropriate model for specific task"""
        if not provider_name:
            provider_name = self.get_active_provider()
        
        provider_config = self.get_provider_config(provider_name)
        if not provider_config or "models" not in provider_config:
            raise ValueError(f"Invalid provider configuration: {provider_name}")
        
        models = provider_config["models"]
        
        # Map task types to model types
        task_model_mapping = {
            "analyze_website": "analysis",
            "generate_todo": "planning", 
            "edit_code": "coding",
            "edit_content": "coding",
            "validate_changes": "analysis",
            "summarize": "analysis"
        }
        
        model_type = task_model_mapping.get(task_type, "coding")
        return models.get(model_type, models.get("coding"))


# Global configuration instance
_config_instance = None


def get_ai_config() -> AIConfig:
    """Get global AI configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AIConfig()
    return _config_instance


def reload_ai_config():
    """Reload AI configuration from file"""
    global _config_instance
    _config_instance = None
    return get_ai_config()


def create_default_config_file(file_path: str = "ai_config.json") -> bool:
    """Create default configuration file"""
    try:
        config = AIConfig()
        config.config_file = file_path
        return config.save_config()
    except Exception as e:
        logger.error(f"Failed to create default config file: {e}")
        return False