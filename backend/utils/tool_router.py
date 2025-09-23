import os
import importlib
import inspect
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Key mappings for different tools
API_KEY_MAPPINGS = {
    "get_youtube_videos": "YOUTUBE_API_KEY",
    "search_with_perplexity_sonar": "PERPLEXITY_API_KEY", 
    "gemini_google_search": "GEMINI_API_KEY",
    "search_instagram_with_apify": "APIFY_API_TOKEN",
    "google_sheet_reader": "GOOGLE_SHEETS_API_KEY",
    "google_sheet_append": None,  # Uses service account
    "google_sheet_update": None,  # Uses service account
}

def get_api_key(tool_name: str) -> Optional[str]:
    """
    Get the appropriate API key for a tool from environment variables.
    
    Args:
        tool_name: Name of the tool requiring an API key
        
    Returns:
        API key string or None if not found/needed
    """
    env_var = API_KEY_MAPPINGS.get(tool_name)
    if env_var is None:
        return None
    return os.getenv(env_var)

def tool_router(tool_name: str, input_schema_fields: Dict[str, Any]) -> Any:
    """
    Dynamically route tool calls to the appropriate tool function in the tools directory.
    
    Args:
        tool_name: Name of the tool to call (e.g., "get_youtube_videos")
        input_schema_fields: Dictionary of input parameters for the tool (or list of dicts to be merged)
        
    Returns:
        Response from the called tool function
        
    Raises:
        ImportError: If the tool module cannot be imported
        AttributeError: If the tool function doesn't exist
        Exception: If the tool execution fails
    """
    try:
        # Handle case where input_schema_fields is a list of dictionaries
        if isinstance(input_schema_fields, list):
            # Merge all dictionaries in the list
            merged_fields = {}
            for item in input_schema_fields:
                if isinstance(item, dict):
                    merged_fields.update(item)
            input_schema_fields = merged_fields
        
        # Import the tools module dynamically
        tools_module = importlib.import_module("tools.research")
        
        # Check if tool exists in research module
        if hasattr(tools_module, tool_name):
            tool_function = getattr(tools_module, tool_name)
        else:
            # Try importing from google_sheets module
            tools_module = importlib.import_module("tools.google_sheets")
            if hasattr(tools_module, tool_name):
                tool_function = getattr(tools_module, tool_name)
            else:
                raise AttributeError(f"Tool '{tool_name}' not found in any tools module")
        
        # Get function signature to determine required parameters
        sig = inspect.signature(tool_function)
        params = list(sig.parameters.keys())
        
        # Prepare arguments for the tool function
        tool_args = {}
        
        # Add input schema fields
        for key, value in input_schema_fields.items():
            if key in params:
                tool_args[key] = value
        
        # Add API key if the tool requires it
        api_key = get_api_key(tool_name)
        if api_key and "api_key" in params:
            tool_args["api_key"] = api_key
        
        # Call the tool function with prepared arguments
        result = tool_function(**tool_args)
        
        return result
        
    except ImportError as e:
        raise ImportError(f"Failed to import tools module: {e}")
    except AttributeError as e:
        raise AttributeError(f"Tool function not found: {e}")
    except Exception as e:
        raise Exception(f"Tool execution failed: {e}")

def get_available_tools() -> list:
    """
    Get a list of all available tools from the tools directory.
    
    Returns:
        List of tool names available for routing
    """
    available_tools = []
    
    # Check research tools
    try:
        research_module = importlib.import_module("tools.research")
        research_tools = [name for name, obj in inspect.getmembers(research_module) 
                         if inspect.isfunction(obj) and not name.startswith('_')]
        available_tools.extend(research_tools)
    except ImportError:
        pass
    
    # Check google_sheets tools
    try:
        sheets_module = importlib.import_module("tools.google_sheets")
        sheets_tools = [name for name, obj in inspect.getmembers(sheets_module) 
                       if inspect.isfunction(obj) and not name.startswith('_')]
        available_tools.extend(sheets_tools)
    except ImportError:
        pass
    
    return available_tools
