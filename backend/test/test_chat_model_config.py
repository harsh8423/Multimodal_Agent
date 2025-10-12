"""
Test script for the central chat model configuration system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.chat_model_config import get_final_config, chat_model_config

def test_config_system():
    """Test the chat model configuration system."""
    print("Testing Chat Model Configuration System")
    print("=" * 50)
    
    # Test default configuration
    print("\n1. Testing default configuration:")
    default_config = get_final_config()
    print(f"Default config: {default_config}")
    
    # Test agent configurations
    print("\n2. Testing agent configurations:")
    agents = ["research_agent", "asset_agent", "todo_planner", "media_analyst", 
              "social_media_search_agent", "media_activist", "copy_writer", "social_media_manager"]
    
    for agent in agents:
        config = get_final_config(agent_name=agent)
        print(f"{agent}: {config}")
    
    # Test tool configurations
    print("\n3. Testing tool configurations:")
    tools = ["verification_tool", "title_generator", "gemini_image", "gemini_video"]
    
    for tool in tools:
        config = get_final_config(tool_name=tool)
        print(f"{tool}: {config}")
    
    # Test configuration updates
    print("\n4. Testing configuration updates:")
    print("Updating research_agent to use Gemini...")
    chat_model_config.update_agent_config("research_agent", "gemini", "gemini-2.5-flash")
    
    updated_config = get_final_config(agent_name="research_agent")
    print(f"Updated research_agent config: {updated_config}")
    
    # Test available models
    print("\n5. Testing available models:")
    providers = ["openai", "gemini", "groq"]
    for provider in providers:
        models = chat_model_config.get_available_models(provider)
        print(f"{provider}: {models}")
    
    print("\n" + "=" * 50)
    print("Configuration system test completed successfully!")

if __name__ == "__main__":
    test_config_system()