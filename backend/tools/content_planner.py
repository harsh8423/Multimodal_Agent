#!/usr/bin/env python3
"""
Content Planner Tool for Social Media Manager

This tool generates structured content plans for different social media platforms
and content types. It returns detailed specifications that can be used by
content creation agents to generate actual media assets.
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


def generate_content_plan(platform_name: str, content_type: str, user_brief: str = "", **kwargs) -> Dict[str, Any]:
    """
    Generate a structured content plan for the specified platform and content type.
    
    Args:
        platform_name (str): Target platform (instagram, linkedin, youtube, facebook, tiktok)
        content_type (str): Type of content (reel, image_post, carousel, video_post, text_post)
        user_brief (str): Optional user brief or requirements
        **kwargs: Additional parameters for customization
    
    Returns:
        Dict[str, Any]: Structured content plan with specifications
    """
    
    # Generate unique plan ID
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    
    # Normalize platform and content type
    platform = platform_name.lower()
    content_type_norm = content_type.lower()
    
    # Base structure
    content_plan = {
        "id": plan_id,
        "content_type": content_type_norm,
        "platform": platform,
        "instructions": "",
        "objective_instruction": "CONTENT_CREATOR: Fill objective and KPI targets here (e.g., engagement_rate, reach_target, conversion_goal).",
        "spec": {},
        "final_deliveries": [],
        "field_definitions": {},
        "notes": ""
    }
    
    # Generate platform-specific content plan
    if content_type_norm in ["reel", "shorts", "short_video"]:
        content_plan = _generate_reel_plan(content_plan, platform, user_brief, **kwargs)
    elif content_type_norm in ["image_post", "image", "photo"]:
        content_plan = _generate_image_post_plan(content_plan, platform, user_brief, **kwargs)
    elif content_type_norm in ["carousel", "slides", "multi_image"]:
        content_plan = _generate_carousel_plan(content_plan, platform, user_brief, **kwargs)
    elif content_type_norm in ["video_post", "video", "long_video"]:
        content_plan = _generate_video_post_plan(content_plan, platform, user_brief, **kwargs)
    elif content_type_norm in ["text_post", "text", "status"]:
        content_plan = _generate_text_post_plan(content_plan, platform, user_brief, **kwargs)
    else:
        # Default fallback
        content_plan = _generate_default_plan(content_plan, platform, content_type_norm, user_brief, **kwargs)
    
    return content_plan


def _generate_reel_plan(plan: Dict[str, Any], platform: str, user_brief: str, **kwargs) -> Dict[str, Any]:
    """Generate specifications for Reels/Shorts content"""
    
    # Platform-specific duration limits
    duration_limits = {
        "instagram": "15-90 seconds",
        "youtube": "15-60 seconds", 
        "tiktok": "15-60 seconds",
        "facebook": "15-60 seconds"
    }
    
    duration = duration_limits.get(platform, "15-60 seconds")
    
    plan["instructions"] = f"Create an engaging {duration} reel/short for {platform} that captures attention quickly and drives engagement. Focus on visual storytelling with clear hooks and strong CTAs."
    
    plan["spec"] = {
        "brand_detail": {
            "required": False,
            "desc": "Brand voice summary or brand_id for consistent tone and style"
        },
        "asset_requirement": {
            "required": False,
            "desc": "List of required assets: logo, brand_colors, voice_sample, font_files, product_images"
        },
        "template_detail": {
            "required": False,
            "desc": "Template style hints: shot_list, color_palette, visual_overlays, transition_style"
        },
        "search_base": {
            "required": False,
            "desc": "Relevant search results or reference URLs for content inspiration"
        },
        "knowledge_base": {
            "required": False,
            "desc": "Attached research notes or data the planner used for context"
        },
        "post_or_media_reference": {
            "required": False,
            "desc": "URLs to example posts/media for tone and format reference"
        },
        "hooks": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 short hook lines (≤3s each) for opening to grab attention",
            "examples": [
                "Hook A: \"You won't believe what happened next!\"",
                "Hook B: \"This simple trick changed everything!\"",
                "Hook C: \"Stop doing this immediately!\""
            ]
        },
        "captions": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 caption options for the post",
            "examples": [
                "Caption 1: 'Game changer! Try this today 👆'",
                "Caption 2: 'Life hack alert! Save this for later 💡'",
                "Caption 3: 'You need to see this! Tag someone who needs this tip'"
            ]
        },
        "hashtags": {
            "required": True,
            "type": "array(5-6)",
            "desc": "Platform-optimized hashtags for maximum reach",
            "examples": ["#LifeHack", "#Tips", "#Viral", "#Trending", "#MustWatch", "#Share"]
        },
        "script": {
            "required": True,
            "type": "string",
            "desc": f"Full narration script for {duration} with clear pacing and engagement points"
        },
        "cta_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 call-to-action options to drive engagement",
            "examples": ["Save for later", "Tag a friend", "Comment your thoughts"]
        },
        "splitted_scene": {
            "required": True,
            "type": "array",
            "desc": "Scene-by-scene breakdown for video production",
            "item": {
                "scene_id": "int",
                "text_to_speech": "string",
                "voice_detail": {
                    "required": False,
                    "desc": "Voice style specifications: gender, age, accent, tone"
                },
                "image_prompt": "string",
                "image_to_video_prompt": "string"
            },
            "examples": [
                {
                    "scene_id": 1,
                    "text_to_speech": "Hook line with energy and excitement",
                    "voice_detail": {"style": "energetic", "gender": "neutral", "tone": "engaging"},
                    "image_prompt": "Dynamic opening shot with bright lighting and engaging composition",
                    "image_to_video_prompt": "Quick zoom-in with text overlay animation"
                }
            ]
        }
    }
    
    plan["final_deliveries"] = [
        "caption/body_text (choose best option)",
        "hashtags (optimized list)",
        "set_of_scenes: for each scene -> image_generation_prompt, tts_text, image_to_video_prompt, voice_detail",
        "optional: engagement_tips (pinned comment suggestions, posting time recommendations)"
    ]
    
    plan["field_definitions"] = {
        "hooks": "Short attention-grabbing opening lines that stop the scroll",
        "splitted_scene.image_prompt": "Detailed prompt for image generation including composition, lighting, mood, and style",
        "splitted_scene.image_to_video_prompt": "Instructions for converting static image to engaging video clip with movement/effects"
    }
    
    plan["notes"] = f"Platform: {platform} | Duration: {duration} | Focus on quick engagement and shareability. Ensure all scenes flow smoothly with clear narrative arc."
    
    return plan


def _generate_image_post_plan(plan: Dict[str, Any], platform: str, user_brief: str, **kwargs) -> Dict[str, Any]:
    """Generate specifications for Image Post content"""
    
    plan["instructions"] = f"Create a compelling single-image post for {platform} that tells a story, educates, or entertains. Focus on visual impact and clear messaging."
    
    plan["spec"] = {
        "brand_detail": {
            "required": False,
            "desc": "Brand voice summary or brand_id for consistent messaging"
        },
        "asset_requirement": {
            "required": False,
            "desc": "Required assets: logo, product_shots, brand_colors, font_files, templates"
        },
        "template_detail": {
            "required": False,
            "desc": "Visual template or layout guidelines for consistent branding"
        },
        "knowledge_base": {
            "required": False,
            "desc": "Research data or context information to reference"
        },
        "post_or_media_reference": {
            "required": False,
            "desc": "Reference image URLs or example posts for style inspiration"
        },
        "caption_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 caption variations with different tones and lengths",
            "examples": [
                "Caption 1: 'Behind the scenes of our latest project ✨'",
                "Caption 2: 'The story behind this moment 📸'",
                "Caption 3: 'What you don't see in the final shot...'"
            ]
        },
        "hashtags": {
            "required": True,
            "type": "array(5-6)",
            "desc": "Platform-specific hashtags for optimal reach",
            "examples": ["#BehindTheScenes", "#Creative", "#Inspiration", "#Design", "#Process", "#Story"]
        },
        "cta_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "Call-to-action options to drive engagement",
            "examples": ["Double tap if you agree", "Share your thoughts below", "Save this for later"]
        },
        "enhanced_image_generation_prompt": {
            "required": True,
            "desc": "Very detailed prompt for image generation including style, composition, lighting, mood, colors, and specific elements"
        }
    }
    
    plan["final_deliveries"] = [
        "caption/body_text (best option selected)",
        "hashtags (optimized list)",
        "generated_image_prompt (detailed specification)",
        "cta (selected option)",
        "optional: engagement_tips (posting suggestions, comment starters)"
    ]
    
    plan["field_definitions"] = {
        "enhanced_image_generation_prompt": "Comprehensive prompt for AI image generation including all visual elements, style, mood, and technical specifications"
    }
    
    plan["notes"] = f"Platform: {platform} | Focus on single strong visual with supporting text. Ensure image works well at different sizes and maintains impact."
    
    return plan


def _generate_carousel_plan(plan: Dict[str, Any], platform: str, user_brief: str, **kwargs) -> Dict[str, Any]:
    """Generate specifications for Carousel content"""
    
    plan["instructions"] = f"Create an engaging multi-slide carousel for {platform} that tells a complete story or provides comprehensive information. Each slide should build on the previous one."
    
    plan["spec"] = {
        "brand_detail": {
            "required": False,
            "desc": "Brand voice summary or brand_id for consistent messaging across slides"
        },
        "asset_requirement": {
            "required": False,
            "desc": "Required assets: logo, templates, brand_colors, font_files, icons"
        },
        "template_detail": {
            "required": False,
            "desc": "Carousel template reference or layout guidelines for consistency"
        },
        "search_base": {
            "required": False,
            "desc": "Research results or reference materials for content"
        },
        "knowledge_base": {
            "required": False,
            "desc": "Attached research or data to reference in content"
        },
        "post_or_media_reference": {
            "required": False,
            "desc": "Example carousel URLs or reference images for style"
        },
        "caption_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 caption variations for the carousel post",
            "examples": [
                "Caption 1: 'Swipe to see the complete process 👉'",
                "Caption 2: 'Step-by-step guide to success 📋'",
                "Caption 3: 'Everything you need to know in one post'"
            ]
        },
        "hashtags": {
            "required": True,
            "type": "array(5-6)",
            "desc": "Platform-optimized hashtags for carousel content",
            "examples": ["#Carousel", "#Guide", "#Tips", "#HowTo", "#StepByStep", "#Learn"]
        },
        "cover_page": {
            "required": True,
            "desc": "Cover image specifications that entices users to swipe",
            "fields": {
                "text_data": "string",
                "enhanced_image_generation_prompt": "string",
                "templated_reference_image_url": "string (optional)"
            }
        },
        "script_for_all_pages": {
            "required": True,
            "desc": "Brief script or copy for each slide/page of the carousel"
        },
        "cta_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "Call-to-action options for the final slide",
            "examples": ["Save this guide", "Share with your network", "Comment your thoughts"]
        },
        "splitted_pages": {
            "required": True,
            "type": "array",
            "desc": "Array of page objects for each slide",
            "item": {
                "page_index": "int",
                "text_data": "string",
                "enhanced_image_generation_prompt": "string",
                "templated_reference_image_url": "string (optional)"
            }
        }
    }
    
    plan["final_deliveries"] = [
        "caption/body_text (selected option)",
        "hashtags (optimized list)",
        "set_of_images: cover_page + all carousel pages with detailed generation prompts",
        "optional: engagement_tips (swipe encouragement, comment prompts)"
    ]
    
    plan["field_definitions"] = {
        "cover_page": "First slide that appears in feed - must be compelling enough to encourage swiping",
        "splitted_pages": "Individual slides that make up the carousel, each with specific content and visual requirements"
    }
    
    plan["notes"] = f"Platform: {platform} | Carousel should have clear narrative flow. Cover page is crucial for engagement. Keep text concise and visuals consistent."
    
    return plan


def _generate_video_post_plan(plan: Dict[str, Any], platform: str, user_brief: str, **kwargs) -> Dict[str, Any]:
    """Generate specifications for Video Post content"""
    
    # Platform-specific video limits
    video_limits = {
        "youtube": "up to 12 hours",
        "linkedin": "up to 10 minutes", 
        "facebook": "up to 240 minutes",
        "instagram": "up to 60 minutes"
    }
    
    duration = video_limits.get(platform, "up to 10 minutes")
    
    plan["instructions"] = f"Create an engaging video post for {platform} ({duration}) that provides value, tells a story, or educates the audience. Focus on clear narrative and visual quality."
    
    plan["spec"] = {
        "brand_detail": {
            "required": False,
            "desc": "Brand voice and style guidelines for video content"
        },
        "asset_requirement": {
            "required": False,
            "desc": "Required assets: logo, brand_colors, music, voice_samples, templates"
        },
        "template_detail": {
            "required": False,
            "desc": "Video template or style guidelines for consistency"
        },
        "search_base": {
            "required": False,
            "desc": "Research materials or reference content for video"
        },
        "knowledge_base": {
            "required": False,
            "desc": "Background information or data to include in video"
        },
        "post_or_media_reference": {
            "required": False,
            "desc": "Reference video URLs or example content for style"
        },
        "video_title_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 compelling title options for the video",
            "examples": [
                "Title 1: 'The Complete Guide to Success'",
                "Title 2: 'Everything You Need to Know About X'",
                "Title 3: 'Master This Skill in 10 Minutes'"
            ]
        },
        "caption_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 description/caption options for the video",
            "examples": [
                "Caption 1: 'In this video, we cover everything you need to know about...'",
                "Caption 2: 'Learn the secrets that professionals use to...'",
                "Caption 3: 'Step-by-step tutorial that will change how you...'"
            ]
        },
        "hashtags": {
            "required": True,
            "type": "array(5-6)",
            "desc": "Platform-specific hashtags for video content",
            "examples": ["#Tutorial", "#HowTo", "#Education", "#Learning", "#Tips", "#Guide"]
        },
        "video_script": {
            "required": True,
            "type": "string",
            "desc": f"Complete video script with timing, narration, and visual cues for {duration} content"
        },
        "cta_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "Call-to-action options for video end",
            "examples": ["Subscribe for more", "Like if helpful", "Comment your questions"]
        },
        "video_segments": {
            "required": True,
            "type": "array",
            "desc": "Video segments with specific content and timing",
            "item": {
                "segment_id": "int",
                "duration": "string",
                "content_description": "string",
                "visual_requirements": "string",
                "audio_requirements": "string"
            }
        }
    }
    
    plan["final_deliveries"] = [
        "video_title (selected option)",
        "caption/description (selected option)",
        "hashtags (optimized list)",
        "video_script (complete with timing)",
        "video_segments (detailed breakdown)",
        "cta (selected option)",
        "optional: thumbnail_prompt, engagement_tips"
    ]
    
    plan["field_definitions"] = {
        "video_script": "Complete script with narration, visual cues, and timing for the entire video",
        "video_segments": "Breakdown of video into logical segments with specific requirements for each part"
    }
    
    plan["notes"] = f"Platform: {platform} | Duration: {duration} | Focus on clear structure, engaging visuals, and valuable content. Consider platform-specific video requirements."
    
    return plan


def _generate_text_post_plan(plan: Dict[str, Any], platform: str, user_brief: str, **kwargs) -> Dict[str, Any]:
    """Generate specifications for Text Post content"""
    
    plan["instructions"] = f"Create an engaging text-based post for {platform} that provides value, starts conversations, or shares insights. Focus on compelling copy and clear messaging."
    
    plan["spec"] = {
        "brand_detail": {
            "required": False,
            "desc": "Brand voice guidelines for text content and tone"
        },
        "knowledge_base": {
            "required": False,
            "desc": "Research or data to reference in the post"
        },
        "post_or_media_reference": {
            "required": False,
            "desc": "Example text posts or reference content for style"
        },
        "content_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "2-3 text content variations with different approaches",
            "examples": [
                "Content 1: 'Thought-provoking question or insight...'",
                "Content 2: 'Personal story or experience sharing...'",
                "Content 3: 'Industry tip or valuable information...'"
            ]
        },
        "hashtags": {
            "required": True,
            "type": "array(5-6)",
            "desc": "Platform-specific hashtags for text content",
            "examples": ["#Thoughts", "#Insights", "#Discussion", "#Community", "#Sharing", "#Perspective"]
        },
        "cta_options": {
            "required": True,
            "type": "array(2-3)",
            "desc": "Call-to-action options to encourage engagement",
            "examples": ["What are your thoughts?", "Share your experience", "Comment below"]
        },
        "engagement_prompts": {
            "required": False,
            "type": "array(2-3)",
            "desc": "Questions or prompts to encourage comments and discussion",
            "examples": ["What's your take on this?", "Have you experienced something similar?", "What would you add?"]
        }
    }
    
    plan["final_deliveries"] = [
        "content_text (selected option)",
        "hashtags (optimized list)",
        "cta (selected option)",
        "engagement_prompts (optional)",
        "optional: posting_tips, best_times"
    ]
    
    plan["field_definitions"] = {
        "content_options": "Different approaches to the same message with varying tones and structures",
        "engagement_prompts": "Specific questions or prompts designed to encourage audience interaction"
    }
    
    plan["notes"] = f"Platform: {platform} | Focus on compelling copy that encourages engagement. Consider platform character limits and audience preferences."
    
    return plan


def _generate_default_plan(plan: Dict[str, Any], platform: str, content_type: str, user_brief: str, **kwargs) -> Dict[str, Any]:
    """Generate a default content plan for unrecognized content types"""
    
    plan["instructions"] = f"Create engaging {content_type} content for {platform}. Adapt the approach based on platform best practices and audience preferences."
    
    plan["spec"] = {
        "brand_detail": {
            "required": False,
            "desc": "Brand guidelines and voice for content creation"
        },
        "content_requirements": {
            "required": True,
            "desc": "Specific requirements and objectives for this content type"
        },
        "platform_considerations": {
            "required": True,
            "desc": f"Platform-specific requirements and best practices for {platform}"
        },
        "deliverables": {
            "required": True,
            "desc": "List of required outputs and specifications"
        }
    }
    
    plan["final_deliveries"] = [
        "content_specifications",
        "platform_requirements",
        "deliverable_list",
        "optional: best_practices, engagement_tips"
    ]
    
    plan["field_definitions"] = {
        "content_requirements": "Detailed specifications for the requested content type",
        "platform_considerations": "Platform-specific requirements, limitations, and best practices"
    }
    
    plan["notes"] = f"Platform: {platform} | Content Type: {content_type} | This is a custom content type. Adapt specifications based on platform capabilities and user requirements."
    
    return plan


# Example usage and testing
if __name__ == "__main__":
    # Test different content types
    test_cases = [
        ("instagram", "reel", "Create a fun reel about morning routines"),
        ("linkedin", "image_post", "Professional tip about productivity"),
        ("youtube", "shorts", "Quick tutorial on a useful skill"),
        ("facebook", "carousel", "Step-by-step guide to success"),
        ("tiktok", "video_post", "Entertaining educational content")
    ]
    
    for platform, content_type, brief in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing: {platform} - {content_type}")
        print(f"Brief: {brief}")
        print('='*50)
        
        plan = generate_content_plan(platform, content_type, brief)
        print(json.dumps(plan, indent=2))