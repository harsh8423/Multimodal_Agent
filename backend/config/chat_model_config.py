"""
Central Chat Model Configuration

This module provides centralized configuration for chat models used across agents and tools.
It defines default models for each agent and tool, making it easy to manage model assignments.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


class ChatModelConfig:
    """Central configuration for chat models used by agents and tools."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the chat model configuration.
        
        Args:
            config_path: Optional path to custom config file. If None, uses default config.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "chat_models.json"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            # Create default config if it doesn't exist
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading config file {self.config_path}: {e}")
            print("Using default configuration...")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for all agents and tools."""
        return {
            "defaults": {
                "chat_llm_model": "openai",
                "model_name": "gpt-5-mini"
            },
            "agents": {
                "research_agent": {
                    "chat_llm_model": "gemini",
                    "model_name": "gemini-2.5-flash"
                },
                "asset_agent": {
                    "chat_llm_model": "openai", 
                    "model_name": "gpt-5-mini"
                },
                "media_analyst": {
                    "chat_llm_model": "gemini",
                    "model_name": "gemini-2.5-flash"
                },
                "social_media_search_agent": {
                    "chat_llm_model": "openai",
                    "model_name": "gpt-5-mini"
                },
                "media_activist": {
                    "chat_llm_model": "openai",
                    "model_name": "gpt-4o-mini"
                },
                "copy_writer": {
                    "chat_llm_model": "openai",
                    "model_name": "gpt-4o-mini"
                },
                "todo_planner": {
                    "chat_llm_model": "gemini",
                    "model_name": "gemini-2.5-flash"
                },
                "content_analyzer": {
                    "chat_llm_model": "openai",
                    "model_name": "gpt-4o-mini"
                },
                "social_media_manager": {
                    "chat_llm_model": "groq",
                    "model_name": "openai/gpt-oss-120b"
                }
            },
            "tools": {
                "verification_tool": {
                    "chat_llm_model": "openai",
                    "model_name": "gpt-4o-mini"
                },
                "title_generator": {
                    "chat_llm_model": "gemini",
                    "model_name": "gemini-2.5-flash"
                },
                "gemini_image": {
                    "chat_llm_model": "gemini",
                    "model_name": "gemini-2.5-flash"
                },
                "gemini_video": {
                    "chat_llm_model": "gemini",
                    "model_name": "gemini-2.5-pro"
                }
            },
            "models": {
                "openai": {
                    "default_model": "gpt-4o-mini",
                    "available_models": ["gpt-5-mini", "gpt-4o-mini", "gpt-5", "gpt-4o"]
                },
                "gemini": {
                    "default_model": "gemini-2.5-flash",
                    "available_models": ["gemini-2.5-flash", "gemini-2.5-pro"]
                },
                "groq": {
                    "default_model": "llama-3.1-8b-instant",
                    "available_models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "openai/gpt-oss-120b"]
                }
            }
        }
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file {self.config_path}: {e}")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, str]:
        """
        Get chat model configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dict containing 'chat_llm_model' and 'model_name'
        """
        agent_config = self._config.get("agents", {}).get(agent_name, {})
        
        return {
            "chat_llm_model": agent_config.get("chat_llm_model", self._config["defaults"]["chat_llm_model"]),
            "model_name": agent_config.get("model_name", self._config["defaults"]["model_name"])
        }
    
    def get_tool_config(self, tool_name: str) -> Dict[str, str]:
        """
        Get chat model configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dict containing 'chat_llm_model' and 'model_name'
        """
        tool_config = self._config.get("tools", {}).get(tool_name, {})
        
        return {
            "chat_llm_model": tool_config.get("chat_llm_model", self._config["defaults"]["chat_llm_model"]),
            "model_name": tool_config.get("model_name", self._config["defaults"]["model_name"])
        }
    
    def get_default_config(self) -> Dict[str, str]:
        """
        Get default chat model configuration.
        
        Returns:
            Dict containing 'chat_llm_model' and 'model_name'
        """
        return {
            "chat_llm_model": self._config["defaults"]["chat_llm_model"],
            "model_name": self._config["defaults"]["model_name"]
        }
    
    def update_agent_config(self, agent_name: str, chat_llm_model: str, model_name: str) -> None:
        """
        Update configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            chat_llm_model: Chat model provider
            model_name: Specific model name
        """
        if "agents" not in self._config:
            self._config["agents"] = {}
        
        self._config["agents"][agent_name] = {
            "chat_llm_model": chat_llm_model,
            "model_name": model_name
        }
        
        self._save_config(self._config)
    
    def update_tool_config(self, tool_name: str, chat_llm_model: str, model_name: str) -> None:
        """
        Update configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            chat_llm_model: Chat model provider
            model_name: Specific model name
        """
        if "tools" not in self._config:
            self._config["tools"] = {}
        
        self._config["tools"][tool_name] = {
            "chat_llm_model": chat_llm_model,
            "model_name": model_name
        }
        
        self._save_config(self._config)
    
    def get_available_models(self, provider: str) -> list:
        """
        Get available models for a specific provider.
        
        Args:
            provider: Model provider (openai, gemini, groq)
            
        Returns:
            List of available model names
        """
        return self._config.get("models", {}).get(provider, {}).get("available_models", [])
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._config = self._load_config()


# Global instance for easy access
chat_model_config = ChatModelConfig()


# Convenience functions for backward compatibility
def get_agent_chat_config(agent_name: str) -> Dict[str, str]:
    """Get chat model configuration for an agent."""
    return chat_model_config.get_agent_config(agent_name)


def get_tool_chat_config(tool_name: str) -> Dict[str, str]:
    """Get chat model configuration for a tool."""
    return chat_model_config.get_tool_config(tool_name)


def get_default_chat_config() -> Dict[str, str]:
    """Get default chat model configuration."""
    return chat_model_config.get_default_config()


# Environment variable overrides
def get_env_override_config() -> Dict[str, str]:
    """
    Get configuration from environment variables.
    Environment variables take precedence over config file.
    
    Returns:
        Dict containing overrides from environment variables
    """
    config = {}
    
    # Check for global overrides
    if os.getenv("DEFAULT_CHAT_LLM_MODEL"):
        config["chat_llm_model"] = os.getenv("DEFAULT_CHAT_LLM_MODEL")
    
    if os.getenv("DEFAULT_MODEL_NAME"):
        config["model_name"] = os.getenv("DEFAULT_MODEL_NAME")
    
    return config


def get_final_config(agent_name: Optional[str] = None, tool_name: Optional[str] = None) -> Dict[str, str]:
    """
    Get final configuration with environment variable overrides applied.
    
    Args:
        agent_name: Optional agent name for agent-specific config
        tool_name: Optional tool name for tool-specific config
        
    Returns:
        Final configuration dict
    """
    # Start with base config
    if agent_name:
        config = chat_model_config.get_agent_config(agent_name)
    elif tool_name:
        config = chat_model_config.get_tool_config(tool_name)
    else:
        config = chat_model_config.get_default_config()
    
    # Apply environment variable overrides
    env_overrides = get_env_override_config()
    config.update(env_overrides)
    
    return config