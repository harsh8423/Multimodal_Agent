"""
build_prompts.py

Create and load system prompts for orchestrator and agents using a flexible data registry.

Usage:
    from prompt_registry import build_system_prompt, init_sample_registry

    # create sample registry file (editable JSON)
    init_sample_registry("system_prompts.json")

# build prompt for social media manager
prompt = build_system_prompt("social_media_manager", "system_prompts.json")
    print(prompt)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

# Move the constant here to break circular import
DEFAULT_REGISTRY_FILENAME = "system_prompts.json"


def _format_agents_list(agents: Dict[str, Any], skip_agent: Optional[str] = None) -> str:
    """
    Create a human-readable agents list for embedding into prompts.
    """
    lines = []
    for name, info in agents.items():
        if skip_agent and name == skip_agent:
            continue
        desc = info.get("short_description", "")
        caps = info.get("capabilities", [])
        caps_str = ", ".join(caps) if caps else "none"
        lines.append(f"- {name}: {desc}\n  Capabilities: {caps_str}")
    return "\n".join(lines)


def _format_tools_section(tool_names: list, tools_registry: Dict[str, Any]) -> str:
    """
    Create a detailed tools section for embedding into agent prompts.
    """
    lines = []
    for t in tool_names:
        tool_info = tools_registry.get(t)
        if not tool_info:
            lines.append(f"- {t}: (no metadata found)")
            continue
        desc = tool_info.get("tool_description", "")
        caps = tool_info.get("capabilities", [])
        caps_str = ", ".join(caps) if caps else "none"
        input_schema = tool_info.get("input_schema", {})
        schema_lines = []
        for param, meta in input_schema.items():
            schema_lines.append(f"    - {param}: type={meta.get('type')} required={meta.get('required')} - {meta.get('description','')}")
        schema_text = "\n".join(schema_lines) if schema_lines else "    (no input schema)"
        lines.append(f"- {t}: {desc}\n  Capabilities: {caps_str}\n  Input schema:\n{schema_text}")
    return "\n\n".join(lines)


def build_system_prompt(agent_name: str, registry_path: str = DEFAULT_REGISTRY_FILENAME,
                        extra_instructions: Optional[str] = None) -> str:
    """
    Load registry file and build the system prompt for the requested agent.

    The returned prompt will contain the agent's default_prompt_template with
    placeholders replaced:
      - {AGENTS_LIST}
      - {TOOLS_SECTION}
      - {OTHER_AGENTS}
      - {place_holder} (left for custom injection - replaced by extra_instructions or a token)
    """
    p = Path(registry_path)
    if not p.exists():
        raise FileNotFoundError(f"Registry file not found at: {p.resolve()} - call init_sample_registry() first.")

    registry = json.loads(p.read_text())
    agents = registry.get("agents", {})
    tools = registry.get("tools", {})

    if agent_name not in agents:
        raise KeyError(f"Agent '{agent_name}' not found in registry. Registered agents: {list(agents.keys())}")

    agent_info = agents[agent_name]
    template = agent_info.get("default_prompt_template", "")
    # If extra_instructions provided, inject; else leave {place_holder} token so you can post-process
    place_holder_value = extra_instructions if extra_instructions is not None else "{place_holder}"

    # Build AGENTS_LIST (for social media manager) and OTHER_AGENTS (for other agents)
    agents_list_text = _format_agents_list(agents)
    other_agents_text = _format_agents_list(agents, skip_agent=agent_name)

    # Build TOOLS_SECTION for agents which declare tools
    agent_tools = agent_info.get("tools", [])
    tools_section = _format_tools_section(agent_tools, tools) if agent_tools else "No tools registered for this agent."

    # Replace placeholders in template
    prompt = template.replace("{AGENTS_LIST}", agents_list_text)
    prompt = prompt.replace("{OTHER_AGENTS}", other_agents_text)
    prompt = prompt.replace("{TOOLS_SECTION}", tools_section)
    prompt = prompt.replace("{place_holder}", place_holder_value)

    # As a safety and clarity, append a short footer that reminds about strict schema requirements
    footer = (
        "\n\n-- Do not output anything beyond the specified response schema unless explicitly instructed. "
        "If you need more context, expect the caller to include it in the user query or via {place_holder}."
    )
    return prompt + footer


# Example usage / CLI test
if __name__ == "__main__":
    # Build a prompt for the social media manager
    social_media_manager_prompt = build_system_prompt("social_media_manager", DEFAULT_REGISTRY_FILENAME,
                                              extra_instructions="Decide whether to call a sub-agent. Provide agent_query containing any relevant metadata (e.g., [image:/uploads/...]).")
    print("\n--- SOCIAL MEDIA MANAGER PROMPT ---\n")
    print(social_media_manager_prompt)

    # Build a prompt for the research_agent
    research_prompt = build_system_prompt("research_agent", DEFAULT_REGISTRY_FILENAME,
                                         extra_instructions="Search for recent authoritative sources and summarize in 2-3 sentences.")
    print("\n\n--- RESEARCH AGENT PROMPT ---\n")
    print(research_prompt)

    # Build a prompt for the asset_agent
    asset_prompt = build_system_prompt("asset_agent", DEFAULT_REGISTRY_FILENAME,
                                       extra_instructions="If creating an image, include expected resolution and a short caption.")
    print("\n\n--- ASSET AGENT PROMPT ---\n")
    print(asset_prompt)
