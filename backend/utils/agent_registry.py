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
                    "Perform web-grounded search + synthesis via Perplexity Sonar Pro",
                    "Run Google-grounded searches via a Gemini wrapper",
                    "Return concise synthesized answers plus sources/citations and structured search results"
                ],
                "tools": [
                    "search_with_perplexity_sonar",
                    "gemini_google_search",
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
                "short_description": "Manages and retrieves user data including brands, competitors, scraped posts, and templates with flexible querying and multi-task operations.",
                "capabilities": [
                    "Retrieve and filter user brands with search functionality",
                    "Get competitor data by platform, brand, or search terms",
                    "Access scraped posts with advanced filtering (platform, date, engagement, text search)",
                    "Manage templates with type and status filtering",
                    "Perform multi-task operations combining multiple data types",
                    "Get comprehensive analytics and statistics across all data types"
                ],
                "tools": [
                    "get_user_brands",
                    "get_brand_by_id",
                    "get_brand_stats",
                    "get_user_competitors",
                    "get_competitor_by_id",
                    "get_competitors_by_platform",
                    "get_user_scraped_posts",
                    "get_recent_posts_by_platform",
                    "get_high_engagement_posts",
                    "get_user_templates",
                    "get_template_by_id",
                    "get_templates_by_brand",
                    "get_brand_complete_data",
                    "search_across_all_data",
                    "get_platform_analytics"
                ],
                "default_prompt_template": (
                    "You are ASSET_AGENT. You specialize in retrieving and managing user data including brands, competitors, scraped posts, and templates. {place_holder}\n\n"
                    "Tools available to you (detailed below):\n{TOOLS_SECTION}\n\n"
                    "Decision rules:\n"
                    " - For brand queries: use get_user_brands, get_brand_by_id, or get_brand_stats\n"
                    " - For competitor queries: use get_user_competitors, get_competitor_by_id, or get_competitors_by_platform\n"
                    " - For scraped posts: use get_user_scraped_posts, get_recent_posts_by_platform, or get_high_engagement_posts\n"
                    " - For templates: use get_user_templates, get_template_by_id, or get_templates_by_brand\n"
                    " - For multi-task operations: use get_brand_complete_data, search_across_all_data, or get_platform_analytics\n"
                    " - Always include user_id in tool calls (extract from context or ask user)\n\n"
                    "Output RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  \"text\": \"final response to be returned or empty if tool_requered is true\",\n'
                    '  \"tool_required\": boolean,                                  // whether you will invoke an external tool\n'
                    '  \"tool_name\": \"string (if tool_required true; one of the registered tools)\",\n'
                    '  \"input_schema_fields\": [                                   // required inputs if tool_required true\n'
                    '       {"user_id": "string", "field_name": "value", ...}\n'
                    '  ],\n'
                    '  \"planner\": {\n'
                    '      \"plan_steps\": [\n'
                    '          {\"id\":1, \"description\":\"string\", \"status\":\"pending|in_progress|completed\"},\n'
                    '          ...\n'
                    '      ],\n'
                    '      \"summary\": \"short plan summary\"\n'
                    '  },'
                    "}\n\n"
                    "Process rules:\n"
                    "1) Start by building an initial plan (planner). Keep plans as small as possible for simple queries (single-step) and detailed for complex queries (multi-step).\n"
                    "2) Try to implement the plan in the least number of steps possible. If you can do it in one step, do it in one step, just call the tool and return the result.\n"
                    "3) If `tool_required` is true, set `tool_name` to the appropriate tool and populate `input_schema_fields` with exactly the inputs you need, including user_id.\n"
                    "4) For multi-task operations, use tools like get_brand_complete_data or search_across_all_data to efficiently retrieve related data.\n"
                    "5) After retrieving data, update the planner step statuses and provide comprehensive results.\n"
                    "6) Output ONLY the JSON object described above, nothing else."
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
                    "Download media content (videos, images) with metadata from supported social media platforms using get_media",
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

            # User Data Tools
            "get_user_brands": {
                "tool_description": "Get all brands for a user with optional search filtering.",
                "capabilities": ["retrieve user brands", "search by name or description", "apply limits"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "search": {"type": "string", "required": False, "description": "Search term for brand name or description"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of brands to return (default: 50)"}
                }
            },
            "get_brand_by_id": {
                "tool_description": "Get a specific brand by ID with ownership validation.",
                "capabilities": ["retrieve brand details", "validate ownership", "return brand metadata"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": True, "description": "Brand ID"}
                }
            },
            "get_brand_stats": {
                "tool_description": "Get comprehensive statistics for a brand including templates, competitors, and posts.",
                "capabilities": ["brand analytics", "related data counts", "platform breakdown"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": True, "description": "Brand ID"}
                }
            },
            "get_user_competitors": {
                "tool_description": "Get competitors for a user with filtering options (brand, platform, search).",
                "capabilities": ["retrieve competitors", "filter by brand/platform", "search by name/handle"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": False, "description": "Optional brand ID filter"},
                    "platform": {"type": "string", "required": False, "description": "Platform filter (instagram, youtube, reddit, linkedin)"},
                    "search": {"type": "string", "required": False, "description": "Search term for competitor name or handle"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of competitors to return (default: 50)"}
                }
            },
            "get_competitor_by_id": {
                "tool_description": "Get a specific competitor by ID with ownership validation.",
                "capabilities": ["retrieve competitor details", "validate ownership", "return competitor metadata"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "competitor_id": {"type": "string", "required": True, "description": "Competitor ID"}
                }
            },
            "get_competitors_by_platform": {
                "tool_description": "Get competitors filtered by platform with optional brand filter.",
                "capabilities": ["platform-specific competitors", "brand filtering", "limit results"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "platform": {"type": "string", "required": True, "description": "Platform name (instagram, youtube, reddit, linkedin)"},
                    "brand_id": {"type": "string", "required": False, "description": "Optional brand ID filter"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of competitors to return (default: 20)"}
                }
            },
            "get_user_scraped_posts": {
                "tool_description": "Get scraped posts for a user with comprehensive filtering (brand, platform, date, search, engagement).",
                "capabilities": ["retrieve posts", "advanced filtering", "sorting options", "engagement analysis"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": False, "description": "Optional brand ID filter"},
                    "platform": {"type": "string", "required": False, "description": "Platform filter (instagram, youtube, reddit, linkedin)"},
                    "days_back": {"type": "integer", "required": False, "description": "Number of days to look back"},
                    "search": {"type": "string", "required": False, "description": "Search term for post text"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of posts to return (default: 50)"},
                    "sort_by": {"type": "string", "required": False, "description": "Sort field (scraped_at, engagement, platform) (default: scraped_at)"},
                    "sort_order": {"type": "string", "required": False, "description": "Sort order (asc, desc) (default: desc)"}
                }
            },
            "get_recent_posts_by_platform": {
                "tool_description": "Get recent posts from a specific platform with date filtering.",
                "capabilities": ["platform-specific posts", "date filtering", "recent content"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "platform": {"type": "string", "required": True, "description": "Platform name (instagram, youtube, reddit, linkedin)"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of posts to return (default: 10)"},
                    "days_back": {"type": "integer", "required": False, "description": "Number of days to look back (default: 7)"}
                }
            },
            "get_high_engagement_posts": {
                "tool_description": "Get posts with high engagement metrics (likes, comments).",
                "capabilities": ["engagement filtering", "threshold-based search", "platform filtering"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "min_likes": {"type": "integer", "required": False, "description": "Minimum likes threshold (default: 100)"},
                    "min_comments": {"type": "integer", "required": False, "description": "Minimum comments threshold (default: 10)"},
                    "platform": {"type": "string", "required": False, "description": "Optional platform filter"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of posts to return (default: 20)"}
                }
            },
            "get_user_templates": {
                "tool_description": "Get templates for a user with filtering options (brand, type, status, search).",
                "capabilities": ["retrieve templates", "filter by brand/type/status", "search by name"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": False, "description": "Optional brand ID filter"},
                    "template_type": {"type": "string", "required": False, "description": "Template type filter (video, image, text, mixed)"},
                    "status": {"type": "string", "required": False, "description": "Status filter (active, archived, draft)"},
                    "search": {"type": "string", "required": False, "description": "Search term for template name"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of templates to return (default: 50)"}
                }
            },
            "get_template_by_id": {
                "tool_description": "Get a specific template by ID with ownership validation.",
                "capabilities": ["retrieve template details", "validate ownership", "return template metadata"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "template_id": {"type": "string", "required": True, "description": "Template ID"}
                }
            },
            "get_templates_by_brand": {
                "tool_description": "Get templates for a specific brand with optional type filtering.",
                "capabilities": ["brand-specific templates", "type filtering", "limit results"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": True, "description": "Brand ID"},
                    "template_type": {"type": "string", "required": False, "description": "Optional template type filter"},
                    "limit": {"type": "integer", "required": False, "description": "Maximum number of templates to return (default: 20)"}
                }
            },
            "get_brand_complete_data": {
                "tool_description": "Get complete data for a brand including templates, competitors, and recent posts.",
                "capabilities": ["comprehensive brand data", "related data retrieval", "analytics summary"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "brand_id": {"type": "string", "required": True, "description": "Brand ID"}
                }
            },
            "search_across_all_data": {
                "tool_description": "Search across all user data types (brands, competitors, posts, templates).",
                "capabilities": ["cross-data search", "unified results", "comprehensive search"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "search_term": {"type": "string", "required": True, "description": "Search term to look for"},
                    "limit_per_type": {"type": "integer", "required": False, "description": "Maximum results per data type (default: 10)"}
                }
            },
            "get_platform_analytics": {
                "tool_description": "Get comprehensive analytics for a specific platform including engagement metrics and top posts.",
                "capabilities": ["platform analytics", "engagement metrics", "top posts analysis"],
                "input_schema": {
                    "user_id": {"type": "string", "required": True, "description": "User ID"},
                    "platform": {"type": "string", "required": True, "description": "Platform name (instagram, youtube, reddit, linkedin)"},
                    "days_back": {"type": "integer", "required": False, "description": "Number of days to analyze (default: 30)"}
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
                    "Search Instagram posts using Apify API (hashtags, username, etc.)",
                    "Search YouTube videos using official API with date filters",
                    "Search Reddit posts across all subreddits using PRAW",
                    "Return structured results with metadata and platform-specific information",
                    "Didn't have support for LinkedIn and Twitter"
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
                    }
                }
            },
            "get_media": {
                "tool_description": "Download media content (videos, images) with metadata from supported platforms (YouTube, Instagram, LinkedIn).",
                "capabilities": [
                    "Download videos and images from YouTube, Instagram, and LinkedIn",
                    "Extract metadata including captions, likes, comments, published dates",
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
