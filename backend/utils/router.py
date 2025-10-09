from typing import Any, Optional, Dict
from pathlib import Path
import json

from utils.build_prompts import build_system_prompt
from utils.utility import _call_openai_chatmodel, _normalize_model_output
from agents.research_agent import research_agent
from agents.asset_agent import asset_agent
from agents.media_analyst import media_analyst
from agents.social_media_search_agent import social_media_search_agent
from agents.media_activist import media_activist
from agents.copy_writer import copy_writer
from utils.session_memory import SessionContext

DEFAULT_REGISTRY_FILENAME = "system_prompts.json"

async def call_agent(agent_name: str, query: str, model_name: str = "gpt-4o-mini",
                     registry_path: Optional[str] = None, session_context: Optional[SessionContext] = None,
                     user_metadata: Optional[Dict] = None, user_image_path: Optional[str] = None) -> Any:
    """
    Dispatch helper that receives agent_name and query and calls the corresponding agent function.

    Implementation detail:
      - Loads the registry to get list of registered agents (no conditional matching)
      - Resolves the function by name from globals() and calls it.
      - If name resolution fails, a KeyError or NameError will be raised.
    """
    # determine registry path
    if registry_path is None:
        registry_path = Path(__file__).parent.parent / DEFAULT_REGISTRY_FILENAME
    else:
        registry_path = Path(registry_path)

    # load registry to get available agent names (we do not branch on agent_name here)
    registry = json.loads(registry_path.read_text())
    agents_dict = registry.get("agents", {})

    # this ensures we use the registry as the source of truth for available agents
    # but does not use conditional statements to match the agent to call.
    # Attempt to access agents_dict[agent_name] -> will raise KeyError if not present.
    _ = agents_dict[agent_name]  # if not found -> KeyError -> caller can catch/handle it

    # Dynamically resolve function by the agent_name (must be defined in this module)
    func = globals()[agent_name]  # KeyError if function not present
    
    # Extract user_id from session context for agents that need it
    user_id = None
    if session_context:
        user_id = getattr(session_context, 'user_id', None)
    
    # call the function (it should be an async function)
    # Pass user_id for asset_agent specifically and metadata for all agents
    if agent_name == "asset_agent":
        result = await func(query, model_name=model_name, registry_path=str(registry_path), session_context=session_context, 
                           user_id=user_id, user_metadata=user_metadata, user_image_path=user_image_path)
    else:
        result = await func(query, model_name=model_name, registry_path=str(registry_path), session_context=session_context,
                           user_metadata=user_metadata, user_image_path=user_image_path)
    return result


# Example quick test when running this file directly
if __name__ == "__main__":
    import asyncio

    async def _test():
        # NOTE: ensure system_prompts.json exists in project root (init_sample_registry)
        try:
            res = await call_agent("research_agent", "Summarize recent advances in memory-augmented neural nets.", "gpt-5-mini")
            print("call_agent returned:", res)
        except Exception as e:
            print("call_agent failed:", e)

    asyncio.run(_test())
