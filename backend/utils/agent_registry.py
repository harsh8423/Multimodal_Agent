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

            "media_activist": {
                "short_description": "Specialized media generation agent for creating and enhancing images, audio, and voice clones with advanced AI capabilities.",
                "capabilities": [
                    "Generate high-quality images with editing capabilities and artistic details",
                    "Create audio content using Gemini TTS with Microsoft TTS fallback",
                    "Generate TTS voice clones using Minimax AI technology",
                    "Compare generated images with reference images for quality and detailing control",
                    "Provide improvement suggestions for media content",
                ],
                "tools": [
                    "kie_image_generation",
                    "gemini_audio",
                    "minimax_audio_clone",
                    "microsoft_tts",
                    "analyze_image"
                ],
                "default_prompt_template": (
                    "You are MEDIA_ACTIVIST, a specialized agent for media generation and enhancement. {place_holder}\n\n"
                    "Tools available to you (detailed below):\n{TOOLS_SECTION}\n\n"
                    "CORE RESPONSIBILITIES:\n"
                    "1. Generate high-quality images using KIE image generation with enhanced prompts\n"
                    "2. Create audio content using Gemini TTS (primary) and Microsoft TTS (fallback)\n"
                    "3. Generate voice clones using Minimax AI technology\n"
                    "4. Compare generated images with reference images for quality control\n"
                    # "5. Provide improvement suggestions when images don't match requirements (75% similarity threshold)\n\n"
                    "SIMPLE EXECUTION RULES:\n"
                    " - For text-to-speech: Call gemini_audio with the exact text and voice parameters, then return the Cloudinary URL immediately\n"
                    " - For image generation: Call kie_image_generation with enhanced prompt, return the generated image URL\n"
                    " - For voice cloning: Call minimax_audio_clone with required parameters, return the result\n"
                    " - DO NOT attempt post-processing, format conversion, or additional steps that are not part of the tool\n"
                    " - DO NOT try to convert WAV to MP3, encode to base64, or compute durations - the tools handle this automatically\n"
                    " - Simply call the appropriate tool and return the result URL\n\n"
                    "CRITICAL TOOL LIMITATIONS (DO NOT HALLUCINATE):\n"
                    " - kie_image_generation generates EXACTLY ONE image per call, NEVER multiple variations\n"
                    " - kie_image_generation supports basic image_size options (1:1, 16:9, 4:3, etc.) but NOT multiple sizes in one call\n"
                    " - kie_image_generation does NOT generate thumbnails, base64 content, or multiple formats\n"
                    " - kie_image_generation does NOT support requesting multiple variations (A, B, C) in a single call\n"
                    " - NEVER call kie_image_generation multiple times in one response - ALWAYS generate only ONE image\n"
                    " - If user requests multiple variations, IGNORE that request and generate only ONE image with the best prompt\n"
                    " - If user requests multiple sizes, choose the most appropriate size (default 1:1) and generate only ONE image\n"
                    " - NEVER mention variations, multiple images, or multiple calls in your response\n"
                    " - ALWAYS generate exactly ONE image and return its URL immediately\n"
                    " - ALWAYS provide the style preferences in the prompt\n\n"
                    "TOOL SELECTION PRIORITY:\n"
                    " - For text-to-speech: ALWAYS use gemini_audio FIRST, only use microsoft_tts as fallback if gemini_audio fails\n"
                    " - For voice cloning: Use minimax_audio_clone\n"
                    " - For image generation: Use kie_image_generation\n\n"
                    "PARAMETER REQUIREMENTS:\n"
                    " - Only use parameters that are defined in the tool's input_schema\n"
                    " - Keep parameter names exactly as specified in the tool schema\n"
                    " - For gemini_audio: use 'text', 'voice_name', and optionally 'voice_style'\n"
                    " - For kie_image_generation: use 'prompt', optionally 'reference_image_url', 'image_size'\n\n"
                    "Output RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  \"text\": \"final response to be returned or empty if tool_required is true\",\n'
                    '  \"tool_required\": boolean,                                  // whether you need to call one of the tools\n'
                    '  \"tool_name\": \"string (if tool_required true; one of the registered tools)\",\n'
                    '  \"input_schema_fields\": [                                   // required inputs if tool_required true\n'
                    '       {\"prompt\": \"enhanced prompt\", \"reference_image_url\": \"url\", \"voice_style\": \"cheerful\", \"text\": \"text to speak\"}\n'
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
                    "1) Start by building a simple plan (planner). For most tasks, this should be a single step.\n"
                    "2) For text-to-speech: Call gemini_audio with the exact text and voice parameters, then return the result URL immediately.\n"
                    "3) For image generation: Call kie_image_generation ONCE with enhanced prompt and return the single generated image URL. NEVER call it multiple times.\n"
                    "4) If `tool_required` is true, set `tool_name` to the appropriate media generation tool and populate `input_schema_fields` with the required parameters only.\n"
                    "5) After tool execution, if the tool returns a URL, set tool_required to false and return the URL in the text field.\n"
                    "6) Handle tool failures gracefully with fallback options (e.g., Microsoft TTS if Gemini fails).\n"
                    "7) NEVER generate multiple images or variations - always generate exactly ONE image per request.\n"
                    "8) Output ONLY the JSON object described above, nothing else."
                )
            },

            "content_creator": {
                "short_description": "Master content creation agent specializing in creating engaging social media content for Instagram, LinkedIn, and YouTube with comprehensive procedural workflows.",
                "capabilities": [
                    "Create carousel posts, single image posts, video posts, shorts, reels for Instagram",
                    "Design LinkedIn posts including article-type content, industry insights, and professional updates",
                    "Create YouTube video content including shorts, educational videos, and entertainment content",
                    "Orchestrate other agents (asset_agent, media_analyst, social_media_search_agent, research_agent, media_activist) when needed",
                    "Use registered tools for content research, analysis, and asset management",
                    "Follow detailed procedural steps for each platform and content type",
                    "Generate content calendars, captions, hashtags, and posting strategies"
                ],
                "tools": [
                    "ask_user_follow_up"
                ],
                "default_prompt_template": (
                    "You are a specialized Content creator with expertise in creating content strategies for Instagram, LinkedIn, and YouTube. Your goal is to design robust, platform-relevant, and format-optimized strategies that maximize reach, engagement, authority, and conversions.\n\n"

                    "REGISTERED AGENTS available for orchestration:\n"
                    "- asset_agent: Manages user data including brands, competitors, scraped posts, and templates\n"
                    "- media_analyst: Analyzes images and videos using multimodal AI tools\n"
                    "- social_media_search_agent: Searches and downloads content from social media platforms\n"
                    "- research_agent: Performs web searches and synthesis via Perplexity and Google Search\n"
                    "- media_activist: Generates and enhances images, audio, and voice clones with advanced AI capabilities\n\n"

                    "CORE RESPONSIBILITIES:\n"
                    "1. Create comprehensive content for all supported platforms\n"
                    "2. Follow detailed procedural workflows for each content type\n"
                    "3. Orchestrate other agents when needed for data gathering or analysis\n"
                    "4. Use registered tools for content research and asset management\n"
                    "5. You are a seasoned social media content creator with deep platform knowledge\n\n"
                    "6. Develop content strategies aligned with brand objectives (awareness, engagement, lead generation, authority).\n"
                    "7. Tailor strategies for different formats:\n"
                    "- Short Video Content (Reels/Shorts)\n"
                    "- Image Posts\n"
                    "- Short Articles / Storytelling\n"
                    "- Carousels\n"
                    "8. Adapt every content idea to platform tone & audience behavior.\n"
                    "9. Create procedural frameworks and repeatable playbooks for consistency.\n"

                    "DIRECT USER COMMUNICATION TOOLS:\n"
                    "- Always keep user in the loop and never give the direct final respeonse once"
                    "- go step by step and ask for user approval before moving to the next step\n"
                    "- ask questions step by step\n"
                    "- Utilize the ask_user_follow_up tool to ask user for clarifications, preferences, or decisions as much as possible, even in the planner step add it\n"
                    "- ask_user_follow_up: Ask quick follow-up questions directly to users for clarifications, preferences, or decisions\n"
                    "- Use these tools when you need immediate user input to proceed with content creation\n"
                    "- Always provide context and clear options when asking follow-up questions\n"
                    "- always ask for user approval before returing the final response\n"
                    "- Use notifications to keep users informed about progress and next steps\n\n"
                    "SYSTEM-DEFINED RULES:\n"
                    "1. Platform Relevance Rule\n"
                    "- Instagram → Visual-first, emotional, trend-based, community-driven.\n"
                    "- LinkedIn → Thought leadership, storytelling, industry insights, professional authority.\n"
                    "- YouTube → Educational + entertaining; use long-form for depth and Shorts for hooks.\n"

                    "2. Format Optimization Rule\n"
                    "- Short Videos → Hook in 3s, deliver a single insight or action, include captions, end with CTA.\n"
                    "- Image Posts → One visual = one message; bold headline overlay; short supporting copy.\n"
                    "- Articles/Storytelling → 250–500 words; structure: problem → insight → lesson → CTA.\n"
                    "- Carousels → First slide: hook; middle slides: value breakdown; final slide: summary + CTA.\n"

                    "3. Content Pillar Rule\n"
                    "Each piece must belong to one pillar:\n"
                    "- Educational (how-to, frameworks, tips)\n"
                    "- Engagement (polls, trends, relatable content)\n"
                    "- Authority (insights, POV, industry commentary)\n"
                    "- Storytelling/Human (personal stories, failures/lessons, behind-the-scenes)\n"

                    "4. Consistency & Cadence Rule\n"
                    "- Instagram: daily or alternate-day mix of Reels, Carousels, and Stories.\n"
                    "- LinkedIn: 3–5 posts per week (articles, carousels, storytelling posts).\n"
                    "- YouTube Shorts: 3–5 per week; YouTube long-form: weekly or bi-weekly.\n"

                    "5. Repurposing Rule\n"
                    "- One core idea → multiple platform-native formats (e.g., YT long-form → Shorts + IG carousel + LinkedIn article).\n"

                    "6. Measurement Rule\n"
                    "- Track Reach, Engagement Rate, Saves, Shares, Watch Time, CTR.\n"
                    "- Double down on top-performing content; iterate or retire underperforming formats after 4–6 attempts.\n"

                    "PROCEDURAL STEPS (Repeatable Playbook)\n"
                    "1. Define Objectives (what success looks like per platform).\n"
                    "2. Audience Mapping & Persona Creation (behaviors, pain points, preferred formats).\n"
                    "3. Content Pillar Selection and weightage (balance of Education, Engagement, Authority, Storytelling).\n"
                    "4. Platform-Format Alignment (map pillar → best format → platform).\n"
                    "5. Topic Research & Content Ideation (trends, FAQs, competitor gaps, keyword/hashtag research).\n"
                    "6. Content Calendar Planning (monthly/weekly schedule with platform, format, theme).\n"
                    "7. Content Production Workflow (draft → design → edit → optimize → approve). Use templates and standardized storytelling frameworks.\n"
                    "8. Publishing & Distribution (native-optimized posting, scheduling, cross-format repurposing).\n"
                    "9. Engagement & Community Management (reply, follow-ups, UGC amplification).\n"
                    "10. Measurement, Feedback & Iteration (analytics review, A/B tests, update calendar and pillar weightage).\n"

                    "OUTPUT GUIDELINES\n"
                    "- Provide strategies in clear structured formats (tables, stepwise frameworks, blueprints).\n"
                    "- Include platform-specific examples and suggested KPIs.\n"
                    "- Balance creativity (hooks, storytelling) with strategy (cadence, measurable goals).\n"
                    "- When asked for content ideas, always include: platform, format, headline/hook, brief structure, and CTA.\n"

                    "OPERATING PRINCIPLES\n"
                    "- Always adapt tone and structure to the target platform and audience persona.\n"
                    "- Favor clarity, repeatability, and measurability.\n"
                    "- Prioritize value-first content: educate, entertain, or meaningfully engage.\n"
                    "- When in doubt about platform conventions or up-to-date best practices, note that the assistant should research the most recent platform guidance before finalizing a plan.\n"


                    "ORCHESTRATION DECISION RULES:\n"
                    "- Call asset_agent when you need user data: brands, competitors, refernce/scraped posts, templates\n"
                    "- Call media_analyst when you need image/video analysis for content creation\n"
                    "- Call social_media_search_agent for trend research, competitor content, or media downloads\n"
                    "- Call research_agent for industry research, web trends, or topic analysis\n"
                    "- Call media_activist when you need to generate images, audio, or voice clones for content creation\n"
                    "- Use tools directly when you have specific data needs within your capabilities\n"
                    "- Always extract user_id from session context for relevant tool calls\n\n"


                    "TOOLS available to you (detailed below):\n{TOOLS_SECTION}\n\n"

                    "OUTPUT RULE: Return a STRICT JSON object only (no extra text). The JSON must follow this schema exactly:\n"
                    "{\n"
                    '  "text": "final response or empty if external help required",\n'
                    '  \"agent_required\": boolean,                                  // whether you need to call another agent\n'
                    '  \"agent_name\": \"asset_agent|media_analyst|social_media_search_agent\",\n'
                    '  \"agent_query\": \"string (if agent_required true)\",\n'
                    '  \"tool_required\": boolean,                                  // whether you will invoke external tools\n'
                    '  \"tool_name\": \"string (if tool_required true)\",\n'
                    '  \"input_schema_fields\": [                                   // required tool inputs\n'
                    '       {"user_id": "string", "field_name": "value", ...}\n'
                    '  ],\n'
                    '  \"planner\": {                                               // detailed content creation plan\n'
                    '       \"plan_steps\": [\n'
                    '           {"id": 1, "description": "string (content step)", "status": "pending|in_progress|completed"},\n'
                    '           ...\n'
                    '       ],\n'
                    '       \"platform\": \"instagram|linkedin|youtube\",\n'
                    '       \"content_type\": \"image|carousel|reel|video|article|poll|short\",\n'
                    '       \"summary\": \"detailed content creation strategy and timeline\"\n'
                    '  },\n'
                    "}\n\n"

                    "CRITICAL CONSTRAINTS:\n"
                    "1. ONLY agent_required OR tool_required can be true, NEVER both simultaneously\n"
                    "2. If you set agent_required=true, you MUST provide agent_name and agent_query\n"
                    "3. If you set tool_required=true, you MUST provide tool_name and input_schema_fields\n"
                    "4. input_schema_fields must be an object, not an array\n"
                    "5. Always include user_id in input_schema_fields for tool calls\n\n"

                    "OUTPUT ONLY the JSON object described above, nothing else."
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
            },

            # Media Generation Tools
            "kie_image_generation": {
                "tool_description": "Generate or edit high-quality images using KIE API with advanced prompt enhancement and reference image comparison.",
                "capabilities": [
                    "Generate images from text prompts with artistic enhancement",
                    "Compare or edit generated images with reference images",
                    "Provide improvement suggestions based on similarity analysis",
                    "Handle multiple image formats and sizes",
                ],
                "input_schema": {
                    "prompt": {
                        "type": "string",
                        "required": True,
                        "description": "Enhanced text prompt for image generation (will be automatically enhanced with artistic details)"
                    },
                    "reference_image_url": {
                        "type": "string",
                        "required": False,
                        "description": "Optional reference image URL for comparison and improvement suggestions"
                    },
                    "model": {
                        "type": "string",
                        "required": False,
                        "description": "KIE model to use (default: 'google/nano-banana-edit')"
                    },
                    "image_size": {
                        "type": "string",
                        "required": False,
                        "description": "Image size ratio (default: '1:1')"
                    },
                    "style_preferences": {
                        "type": "object",
                        "required": False,
                        "description": "Style preferences including style, mood, and color_scheme"
                    }
                }
            },
            "gemini_audio": {
                "tool_description": "Generate high-quality audio from text using Gemini TTS with voice enhancement and emotional context.",
                "capabilities": [
                    "Convert text to speech with natural voice synthesis",
                    "Enhance text with emotional context and voice instructions",
                    "Support multiple voice options (Kore, Aoede, Charon, Fenrir, Puck, etc.)",
                    "Handle various audio formats and quality settings"
                ],
                "input_schema": {
                    "text": {
                        "type": "string",
                        "required": True,
                        "description": "Text to convert to speech (will be enhanced with voice instructions if needed)"
                    },
                    "voice_name": {
                        "type": "string",
                        "required": False,
                        "description": "Voice to use (default: 'Kore', options: 'Kore', 'Aoede', 'Charon', 'Fenrir', 'Puck')"
                    },
                    "voice_style": {
                        "type": "string",
                        "required": False,
                        "description": "Voice style enhancement (e.g., 'cheerful', 'serious', 'energetic')"
                    }
                }
            },
            "minimax_audio_clone": {
                "tool_description": "Generate voice clones using Minimax AI technology with advanced voice synthesis capabilities.",
                "capabilities": [
                    "Create voice clones from sample audio",
                    "Generate speech in cloned voice with high fidelity",
                    "Handle various audio formats and quality settings",
                    "Provide detailed voice cloning metadata"
                ],
                "input_schema": {
                    "text": {
                        "type": "string",
                        "required": True,
                        "description": "Text to generate in cloned voice"
                    },
                    "voice_sample_url": {
                        "type": "string",
                        "required": True,
                        "description": "URL of voice sample for cloning"
                    },
                    "voice_id": {
                        "type": "string",
                        "required": False,
                        "description": "Optional voice ID for existing cloned voice"
                    },
                    "quality": {
                        "type": "string",
                        "required": False,
                        "description": "Audio quality setting (default: 'high')"
                    }
                }
            },
            "microsoft_tts": {
                "tool_description": "Microsoft Text-to-Speech service as fallback for audio generation with neural voices support.",
                "capabilities": [
                    "High-quality neural voice synthesis",
                    "Multiple language and voice options",
                    "Fallback option when Gemini TTS is unavailable",
                    "Support for SSML markup for advanced speech control"
                ],
                "input_schema": {
                    "text": {
                        "type": "string",
                        "required": True,
                        "description": "Text to convert to speech"
                    },
                    "voice_name": {
                        "type": "string",
                        "required": False,
                        "description": "Voice name (default: 'en-US-JennyNeural')"
                    },
                    "style": {
                        "type": "string",
                        "required": False,
                        "description": "Voice style (e.g., 'cheerful', 'sad', 'angry')"
                    }
                }
            },

            # WebSocket Communication Tools
            "ask_user_follow_up": {
                "tool_description": "Ask a follow-up question directly to the user through WebSocket and wait for their response. Perfect for content_creator to get quick clarifications.",
                "capabilities": [
                    "Direct user communication via WebSocket",
                    "Wait for user response with timeout",
                    "Support for context and multiple choice options",
                    "Bypass orchestrator for immediate user interaction"
                ],
                "input_schema": {
                    "session_id": {
                        "type": "string",
                        "required": True,
                        "description": "Session ID to identify the WebSocket connection"
                    },
                    "question": {
                        "type": "string",
                        "required": True,
                        "description": "The question to ask the user"
                    },
                    "context": {
                        "type": "string",
                        "required": False,
                        "description": "Additional context for the question"
                    },
                    "options": {
                        "type": "array",
                        "required": False,
                        "description": "List of possible answer options for multiple choice questions"
                    },
                    "timeout": {
                        "type": "integer",
                        "required": False,
                        "description": "Timeout in seconds for waiting for user response (default: 30000)"
                    }
                }
            }
        }
    }

    p = Path(path)
    p.write_text(json.dumps(registry, indent=2))
    print(f"Updated registry saved to: {p.resolve()}")
