import asyncio
import inspect
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Import the constant from build_prompts to avoid circular import
from utils.build_prompts import DEFAULT_REGISTRY_FILENAME

# Chat model function (your existing module)
from models.chat_openai import orchestrator_function as openai_chatmodel


def init_updated_registry(path: str = DEFAULT_REGISTRY_FILENAME) -> None:
    """
    Create / overwrite the registry JSON with updated tool & agent descriptions.
    IMPORTANT: The orchestrator agent entry is left unchanged from your original content.
    """
    registry = {
        "agents": {
            # orchestrator: (kept unchanged — exact text as requested)
            "orchestrator": {
                "short_description": "Central coordinator that decides whether to route queries to specialized agents.",
                "capabilities": [
                    "Analyze incoming user queries and decide routing",
                    "Generate concise agent queries for specialized agents",
                    "Return structured JSON orchestration decisions"
                ],
                "default_prompt_template": (
                    "You are the ORCHESTRATOR agent. Your job is to examine the incoming user query "
                    "and decide whether a specialized agent is required. Use the registered agent "
                    "descriptions below to make the decision. {place_holder}\n\n"
                    "Registered agents:\n{AGENTS_LIST}\n\n"
                    "Output requirements: Return a JSON object only (no extra text) with the exact schema.\n"
                    "Do NOT output any prose outside the JSON. The JSON MUST include the following top-level keys:\n"
                    "{\n"
                    '  \"agent_required\": boolean,                                    // true if a specialized agent should handle the task\n'
                    '  \"self_response\": \"string (only if agent_required is false)\", // concise answer if no agent needed\n'
                    '  \"agent_name\": \"string (only if agent_required is true)\",    // one of the registered agents\n'
                    '  \"agent_query\": \"string (only if agent_required is true)\",   // concise query for the chosen agent; include context in [brackets]\n'
                    '  \"planner\": {                                                  // initial plan produced by the orchestrator\n'
                    '       \"plan_steps\": [                                           // ordered list of steps (can be 1..N)\n'
                    '           {\"id\": 1, \"description\": \"string\", \"status\": \"pending|in_progress|completed\"},\n'
                    '           ...\n'
                    '       ],\n'
                    '       \"summary\": \"short plan summary which agent to call\"\n'
                    '  },\n'
                    "}\n\n"
                    "Rules:\n"
                    "1) First build an initial plan (planner) with ordered steps."
                    "2) Try to implement the plan in the least number of steps possible. If you can do it in one step, do it in one step, just call the tool and return the result.\n"
                    "2) If you can answer concisely and confidently without routing, set `agent_required` to false and place your answer in `self_response`. Set planner empty to `return_final`."
                    "3) If specialized work (research, asset creation/fetching, tool invocation) is required, set `agent_required` to true, choose `agent_name` and produce an optimized `agent_query`. Keep `agent_query` concise and include any required context in square brackets (e.g., [path:/tmp/image.png], [user:harsh]).\n"
                    "4) After producing the initial plan and sending the `agent_query`, you will later receive the agent response. When that happens, update the planner step statuses.\n"
                    "5) Output ONLY the JSON object described above, nothing else."
                )
            },

            "research_agent": {
                "short_description": "Can Perform grounded searches across YouTube, Perplexity, Gemini Google Search or Instagram; synthesizes findings into concise answers with citations.",
                "capabilities": [
                    "Fetch recent, relevant YouTube videos matching a query",
                    "Perform web-grounded search + synthesis via Perplexity Sonar Pro",
                    "Run Google-grounded searches via a Gemini wrapper",
                    "Scrape/lookup Instagram results via Apify when social signals are required",
                    "Return concise synthesized answers plus sources/citations and structured search results"
                ],
                "tools": [
                    "get_youtube_videos",
                    "search_with_perplexity_sonar",
                    "gemini_google_search",
                    "search_instagram_with_apify"
                ],
                "default_prompt_template": (
                    "You are RESEARCH_AGENT. Use the available tools to locate and synthesize factual information; produce concise answers and include short citations. {place_holder}\n\n"
                    "Tools available to you (detailed below):\n{TOOLS_SECTION}\n\n"
                    "Output RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  \"text\": \"final response to be returned or empty if tool_requered is true\",\n'
                    '  \"tool_required\": boolean,                                  // whether you need to call one of the tools\n'
                    '  \"tool_name\": \"string (if tool_required true; one of the registered tools)\",\n'
                    '  \"input_schema_fields\": [                                   // required inputs if tool_required true\n'
                    '       {"field_name": "value", ...}'
                    '  ],\n'
                    '  \"planner\": {                                               // initial plan with steps and to-do style checkpoints\n'
                    '       \"plan_steps\": [\n'
                    '           {\"id\":1, \"description\":\"string\", \"status\":\"pending|in_progress|completed\"},\n'
                    '           ...\n'
                    '       ],\n'
                    '       \"summary\": \"short plan summary which tool to call\"\n'
                    '  },'
                    "}\n\n"
                    "Process rules:\n"
                    "1) Start by building an initial plan (planner). Keep plans as small as possible for simple queries (single-step) and detailed for complex queries (multi-step).\n"
                    "2) Try to implement the plan in the least number of steps possible. If you can do it in one step, do it in one step, just call the tool and return the result.\n"
                    "2) If `tool_required` is true, set `tool_name` to the single tool you will call and populate `input_schema_fields` with exactly the inputs you need (name, date range, url, prompt text, etc.) with examples.\n"
                    "3) After performing searches, populate `answer`, `sources`, and `results` as appropriate, then update the planner step statuses.\n"
                    "5) Output ONLY the JSON object described above."
                )
            },

            "asset_agent": {
                "short_description": "Generates, stores and records assets; interacts with Google Sheets, image generation, and the asset store to return structured asset metadata.",
                "capabilities": [
                    "Generate or edit images (text->image or image-edit)",
                    "Store binary assets and return canonical URLs / asset IDs",
                    "Read, append and update Google Sheets for metadata and registry operations",
                    "Validate input schemas for asset creation and return structured JSON metadata"
                ],
                "tools": [
                    "google_sheet_reader",
                    "google_sheet_append",
                    "google_sheet_update"
                ],
                "default_prompt_template": (
                    "You are ASSET_AGENT. Produce or fetch assets and return structured metadata; use the available tools to store or index assets. {place_holder}\n\n"
                    "Tools available to you (detailed below):\n{TOOLS_SECTION}\n\n"
                    "Output RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  \"text\": \"final response to be returned or empty if tool_requered is true\",\n'
                    '  \"tool_required\": boolean,                                  // whether you will invoke an external tool (sheet write, image gen)\n'
                    '  \"tool_name\": \"string (if tool_required true; one of the registered tools)\",\n'
                    '  \"input_schema_fields\": [                                   // required inputs if tool_required true\n'
                    '       {"field_name": "value", ...}'
                    '  ],\n'
                    '  \"planner\": {\n'
                    '      \"plan_steps\": [\n'
                    '          {\"id\":1, \"description\":\"string\", \"status\":\"pending|in_progress|completed\"}, // always mark first steps as in_progress\n'
                    '          ...\n'
                    '      ],\n'
                    '      \"summary\": \"short plan summary\"\n'
                    '  },'
                    "}\n\n"
                    "Process rules:\n"
                    "1) Begin by producing an initial plan (planner) of 1..N steps required to create/fetch/store the asset. For trivial asset requests a single-step plan is acceptable.\n"
                    "2) If you set `tool_required` true, choose one primary tool in `tool_name` and enumerate exactly the `required_input_schema_fields` (name, type, example, required). Do NOT call multiple tools simultaneously in the initial output—prefer a single primary tool unless the user asked otherwise.\n"
                    "3) After creating/fetching the asset, update `plan_steps` statuses .\n"
                    "4) Output ONLY the JSON object described above, nothing else."
                    "5) If you can do it in one step, do it in one step, just call the tool and return the result."
                )
            },

            # New media_analyst agent
            "media_analyst": {
                "short_description": "Multimodal analyst specialized in analyzing images and videos using the analyze_image and analyze_video tools (Gemini-backed).",
                "capabilities": [
                    "Analyze one or multiple image URLs and return structured descriptions, detected objects, scene context, and timestamps of key events (if present).",
                    "Analyze a single video URL and return structured summaries, shot boundaries, detected objects/actions, and timestamps of key events.",
                    "Decide which media tool to call (image vs video) given the user's query and media URL(s).",
                    "Return strictly-structured JSON following the required schema and planner workflow."
                ],
                "tools": [
                    "analyze_image",
                    "analyze_video"
                ],
                "default_prompt_template": (
                    "You are MEDIA_ANALYST. You specialize in analyzing images and videos. {place_holder}\n\n"
                    "Tools available to you (detailed below):\n{TOOLS_SECTION}\n\n"
                    "Decision rules:\n"
                    " - If input contains one or more image URLs, prefer analyze_image (can accept multiple URLs).\n"
                    " - If input contains a single video URL, prefer analyze_video.\n"
                    " - If user provides ambiguous media, ask for clarification only if absolutely necessary. Prefer a single-step plan when possible to call the appropriate tool.\n\n"
                    "Output RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  \"text\": \"final response to be returned or empty if tool_requered is true\",\n'
                    '  \"tool_required\": boolean,                                  // whether you will invoke an external tool (analyze_image/analyze_video)\n'
                    '  \"tool_name\": \"string (if tool_required true; one of the registered tools)\",\n'
                    '  \"input_schema_fields\": [                                   // required inputs if tool_required true\n'
                    '       {"system_prompt": "string (example)", "user_query":"string (example)", "image_urls":["https://..."], "video_url":"https://..."}\n'
                    '  ],\n'
                    "}\n\n"
                    "Process rules:\n"
                    "1) Build an initial planner. For straightforward media analysis, produce a single-step plan that calls the correct tool with the minimal inputs.\n"
                    "2) When setting `tool_required` true, set `tool_name` to either `analyze_image` or `analyze_video` and populate `input_schema_fields` with exact fields the tool expects using the examples above.\n"
                    "3) Tools must be called with: system_prompt, user_query, and either image_urls (list) or video_url (single string). Include any extra context inside the user_query in [] if needed.\n"
                    "4) Output ONLY the JSON object described above, nothing else."
                )
            },

            # New social_media_search_agent
            "social_media_search_agent": {
                "short_description": "Specialized agent for social media search and media downloading across multiple platforms using unified_search and get_media tools.",
                "capabilities": [
                    "Search for posts and content across Instagram, YouTube, and Reddit using unified_search",
                    "Download media content (videos, images) with metadata from supported platforms using get_media",
                    "Detect media URLs in user queries and automatically download them",
                    "Return structured search results and downloaded media with metadata"
                ],
                "tools": [
                    "unified_search",
                    "get_media"
                ],
                "default_prompt_template": (
                    "You are SOCIAL_MEDIA_SEARCH_AGENT. You specialize in social media search and media downloading. {place_holder}\n\n"
                    "Tools available to you (detailed below):\n{TOOLS_SECTION}\n\n"
                    "Decision rules:\n"
                    " - If user query contains media URLs (YouTube, Instagram, LinkedIn), use get_media to download them with metadata.\n"
                    " - If user wants to search for content across platforms, use unified_search with appropriate parameters.\n"
                    " - For search queries, determine the platform(s) and search parameters needed.\n"
                    " - Always extract and preserve metadata from downloaded media.\n\n"
                    "Output RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  \"text\": \"final response to be returned or empty if tool_requered is true\",\n'
                    '  \"tool_required\": boolean,                                  // whether you will invoke an external tool (unified_search/get_media)\n'
                    '  \"tool_name\": \"string (if tool_required true; one of the registered tools)\",\n'
                    '  \"input_schema_fields\": [                                   // required inputs if tool_required true\n'
                    '       {"platform": "instagram|youtube|reddit", "query": "search term", "limit": 10, "url": "media_url"}\n'
                    '  ],\n'
                    "}\n\n"
                    "Process rules:\n"
                    "1) Start by building an initial plan (planner). Keep plans as small as possible for simple queries (single-step) and detailed for complex queries (multi-step).\n"
                    "2) Try to implement the plan in the least number of steps possible. If you can do it in one step, do it in one step, just call the tool and return the result.\n"
                    "3) If `tool_required` is true, set `tool_name` to either `unified_search` or `get_media` and populate `input_schema_fields` with exactly the inputs you need.\n"
                    "4) For unified_search: specify platform, query, limit, and optional parameters like days_back, search_type.\n"
                    "5) For get_media: provide the media URL and any optional parameters like upload_to_cloudinary_flag.\n"
                    "6) After performing searches or downloads, update the planner step statuses and provide final results.\n"
                    "7) Output ONLY the JSON object described above, nothing else."
                )
            },
        },
        "tools": {
            # Research tools (unchanged)
            "get_youtube_videos": {
                "tool_description": "YouTube Data API v3 wrapper to search for videos and return metadata (id, title, description, publishedAt, channel).",
                "capabilities": ["search videos by query", "filter by publishedAfter", "return top-k results with metadata"],
                "input_schema": {
                    "query": {"type": "string", "required": True, "description": "Search query string"},
                    "published_after": {"type": "string", "required": True, "description": "ISO8601 datetime, e.g., 2024-01-01T00:00:00Z"},
                    "max_results": {"type": "integer", "required": False, "description": "Max results to return (default 5)"}
                }
            },
            "search_with_perplexity_sonar": {
                "tool_description": "Perplexity Sonar Pro integration for web search + answer synthesis with citations.",
                "capabilities": ["web retrieval", "synthesized answers", "citations and search results metadata"],
                "input_schema": {
                    "search_description": {"type": "string", "required": False, "description": "System-level search instructions"},
                    "user_prompt": {"type": "string", "required": True, "description": "User's query or prompt"},
                    "model": {"type": "string", "required": False, "description": "Model name (default 'sonar-pro')"}
                }
            },
            "gemini_google_search": {
                "tool_description": "Gemini + Google Search grounding helper for high-quality grounded answers.",
                "capabilities": ["Google-backed grounding", "extract final text answer", "return raw response for auditing"],
                "input_schema": {
                    "search_description": {"type": "string", "required": True, "description": "What to search/ground on"},
                    "model": {"type": "string", "required": False, "description": "Model name (default 'gemini-2.5-pro')"}
                }
            },
            "search_instagram_with_apify": {
                "tool_description": "Apify Instagram Search Scraper integration to fetch posts or user/hashtag matches.",
                "capabilities": ["hashtag/user search", "scrape post metadata", "return JSON results"],
                "input_schema": {
                    "search_term": {"type": "string", "required": True, "description": "Hashtag or username"},
                    "search_type": {"type": "string", "required": False, "description": "Type: 'hashtag' or 'user'"},
                    "search_limit": {"type": "integer", "required": False, "description": "Number of results"}
                }
            },

            # Asset tools (unchanged)
            "google_sheet_reader": {
                "tool_description": "Read rows from a Google Sheet and optionally filter by column values.",
                "capabilities": ["read headers and rows", "filter rows by exact match"],
                "input_schema": {
                    "document_id": {"type": "string", "required": True, "description": "Spreadsheet ID"},
                    "sheet_id": {"type": "string", "required": True, "description": "Sheet/tab name"},
                    "filters": {"type": "object", "required": False, "description": "Dict of column->value to filter rows"}
                }
            },
            "google_sheet_append": {
                "tool_description": "Append a row to a Google Sheet, auto-creating columns if needed.",
                "capabilities": ["append row", "auto-add new columns", "return append response"],
                "input_schema": {
                    "spreadsheet_id": {"type": "string", "required": True, "description": "Spreadsheet ID"},
                    "sheet_name": {"type": "string", "required": True, "description": "Sheet/tab name"},
                    "row_data": {"type": "object", "required": True, "description": "Dict column->value for the new row"}
                }
            },
            "google_sheet_update": {
                "tool_description": "Update a cell by matching a column value and changing a target column.",
                "capabilities": ["find row by column value", "update target cell", "return update response"],
                "input_schema": {
                    "spreadsheet_id": {"type": "string", "required": True},
                    "sheet_name": {"type": "string", "required": True},
                    "match_column": {"type": "string", "required": True},
                    "match_value": {"type": "string", "required": True},
                    "update_column": {"type": "string", "required": True},
                    "new_value": {"type": "string", "required": True}
                }
            },

            # New media tools
            "analyze_image": {
                "tool_description": "Analyze one or more image URLs with Gemini multimodal model and return structured JSON analysis.",
                "capabilities": [
                    "Describe scenes, objects, attributes, relationships",
                    "Return detected objects with confidence scores and bounding boxes (if available)",
                    "Produce scene-level summary and per-image structured output",
                    "Highlight safety/NSFW concerns and any text detected via OCR"
                ],
                "input_schema": {
                    "system_prompt": {
                        "type": "string",
                        "required": True,
                        "description": "System instruction for the Gemini model (defines role/response format). Example: 'You are an assistant that returns JSON with keys summary, detected_objects, per_image_analysis'"
                    },
                    "user_query": {
                        "type": "string",
                        "required": True,
                        "description": "User's query / instruction describing what to analyze or extract from the images"
                    },
                    "image_urls": {
                        "type": "array",
                        "required": True,
                        "description": "List of publicly accessible image URLs to analyze"
                    },
                    "model_name": {
                        "type": "string",
                        "required": False,
                        "description": "Gemini model to use (default: 'gemini-2.5-flash')"
                    }
                }
            },
            "analyze_video": {
                "tool_description": "Analyze a single video URL with Gemini multimodal model and return structured JSON analysis including timestamps of key events.",
                "capabilities": [
                    "Summarize the video, list detected objects and actions, return timestamped key events and shot boundaries",
                    "Detect repeated patterns, safety issues, or textual overlays (OCR)",
                    "Provide scene-level descriptions and an ordered timeline of notable moments"
                ],
                "input_schema": {
                    "system_prompt": {
                        "type": "string",
                        "required": True,
                        "description": "System instruction for the Gemini model (defines role/response format). Example: 'You are an assistant that returns JSON with keys summary, timeline, detected_objects'"
                    },
                    "user_query": {
                        "type": "string",
                        "required": True,
                        "description": "User's query / instruction describing what to analyze or extract from the video"
                    },
                    "video_url": {
                        "type": "string",
                        "required": True,
                        "description": "Publicly accessible URL of the video to analyze (single URL)"
                    },
                    "model_name": {
                        "type": "string",
                        "required": False,
                        "description": "Gemini model to use (default: 'gemini-2.5-pro')"
                    }
                }
            },

            # Social media search and media tools
            "unified_search": {
                "tool_description": "Unified search across multiple social media platforms (Instagram, YouTube, Reddit) with configurable parameters.",
                "capabilities": [
                    "Search Instagram posts using Apify API (hashtags, users, etc.)",
                    "Search YouTube videos using official API with date filters",
                    "Search Reddit posts across all subreddits using PRAW",
                    "Return structured results with metadata and platform-specific information"
                ],
                "input_schema": {
                    "platform": {
                        "type": "string",
                        "required": True,
                        "description": "Platform to search: 'instagram', 'youtube', or 'reddit'"
                    },
                    "query": {
                        "type": "string",
                        "required": True,
                        "description": "Search query string"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Maximum number of results to fetch (default: 10)"
                    },
                    "days_back": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of days to look back for content (YouTube, Reddit)"
                    },
                    "search_type": {
                        "type": "string",
                        "required": False,
                        "description": "Type of search for Instagram: 'hashtag' or 'user' (default: 'hashtag')"
                    },
                    "api_token": {
                        "type": "string",
                        "required": False,
                        "description": "API token for Apify services (Instagram)"
                    },
                    "api_key": {
                        "type": "string",
                        "required": False,
                        "description": "API key for YouTube"
                    }
                }
            },
            "get_media": {
                "tool_description": "Download media content (videos, images) with metadata from supported platforms (YouTube, Instagram, LinkedIn).",
                "capabilities": [
                    "Download videos and images from YouTube, Instagram, and LinkedIn",
                    "Extract metadata including captions, likes, comments, published dates",
                    "Upload downloaded media to Cloudinary for cloud storage",
                    "Return structured results with file paths, metadata, and Cloudinary URLs"
                ],
                "input_schema": {
                    "url": {
                        "type": "string",
                        "required": True,
                        "description": "URL of the media content to download (YouTube, Instagram, LinkedIn)"
                    },
                    "upload_to_cloudinary_flag": {
                        "type": "boolean",
                        "required": False,
                        "description": "Whether to upload downloaded media to Cloudinary (default: True)"
                    },
                    "custom_config": {
                        "type": "object",
                        "required": False,
                        "description": "Optional custom configuration to override defaults"
                    }
                }
            }
        }
    }

    p = Path(path)
    p.write_text(json.dumps(registry, indent=2))
    print(f"Updated registry saved to: {p.resolve()}")
