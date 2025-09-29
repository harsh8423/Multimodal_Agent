"""
User Data Retrieval Tools for Asset Agent

This module provides function-based tools for retrieving user data including:
- Brands management and retrieval
- Competitors tracking and analysis
- Scraped posts filtering and search
- Templates management and retrieval
- Multi-task operations combining multiple data types
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv
from services.social_media_db import social_media_db
from models.social_media import PlatformType, TemplateType, TemplateStatus, ProcessingStatus

# Load environment variables
load_dotenv()


# ======================
# Brand Tools
# ======================

async def get_user_brands(user_id: str, search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Get all brands for a user with optional search filtering.
    
    Args:
        user_id: User ID
        search: Optional search term for brand name or description
        limit: Maximum number of brands to return
    
    Returns:
        Dict containing brands list and metadata
    """
    try:
        brands = await social_media_db.get_brands_by_user(user_id)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            brands = [
                brand for brand in brands
                if search_lower in brand["name"].lower() or 
                   search_lower in brand["description"].lower()
            ]
        
        # Apply limit
        if limit and len(brands) > limit:
            brands = brands[:limit]
        
        return {
            "success": True,
            "brands": brands,
            "total_count": len(brands),
            "search_applied": search is not None,
            "limit_applied": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "brands": []
        }


async def get_brand_by_id(user_id: str, brand_id: str) -> Dict[str, Any]:
    """
    Get a specific brand by ID.
    
    Args:
        user_id: User ID
        brand_id: Brand ID
    
    Returns:
        Dict containing brand data or error
    """
    try:
        brand = await social_media_db.get_brand_by_id(brand_id)
        if not brand:
            return {
                "success": False,
                "error": "Brand not found",
                "brand": None
            }
        
        # Check if user owns this brand
        if brand["user_id"] != user_id:
            return {
                "success": False,
                "error": "Access denied",
                "brand": None
            }
        
        return {
            "success": True,
            "brand": brand
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "brand": None
        }


async def get_brand_stats(user_id: str, brand_id: str) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a brand.
    
    Args:
        user_id: User ID
        brand_id: Brand ID
    
    Returns:
        Dict containing brand statistics
    """
    try:
        # Get brand
        brand = await social_media_db.get_brand_by_id(brand_id)
        if not brand or brand["user_id"] != user_id:
            return {
                "success": False,
                "error": "Brand not found or access denied"
            }
        
        # Get related data
        templates = await social_media_db.get_templates_by_user(user_id, brand_id)
        competitors = await social_media_db.get_competitors_by_user(user_id, brand_id=brand_id)
        scraped_posts = await social_media_db.get_scraped_posts_by_user(user_id, brand_id=brand_id)
        
        # Count by platform
        platform_counts = {}
        for post in scraped_posts:
            platform = post["platform"]
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            "success": True,
            "brand_id": brand_id,
            "brand_name": brand["name"],
            "templates_count": len(templates),
            "competitors_count": len(competitors),
            "scraped_posts_count": len(scraped_posts),
            "platform_breakdown": platform_counts,
            "created_at": brand["created_at"],
            "updated_at": brand["updated_at"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ======================
# Competitor Tools
# ======================

async def get_user_competitors(user_id: str, brand_id: Optional[str] = None, 
                        platform: Optional[str] = None, search: Optional[str] = None, 
                        limit: int = 50) -> Dict[str, Any]:
    """
    Get competitors for a user with filtering options.
    
    Args:
        user_id: User ID
        brand_id: Optional brand ID filter
        platform: Optional platform filter (instagram, youtube, reddit, linkedin)
        search: Optional search term for competitor name or handle
        limit: Maximum number of competitors to return
    
    Returns:
        Dict containing competitors list and metadata
    """
    try:
        # Convert platform string to enum if provided
        platform_enum = None
        if platform:
            try:
                platform_enum = PlatformType(platform.lower())
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid platform: {platform}. Valid platforms: instagram, youtube, reddit, linkedin",
                    "competitors": []
                }
        
        competitors = await social_media_db.get_competitors_by_user(user_id, platform_enum, brand_id)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            competitors = [
                competitor for competitor in competitors
                if search_lower in competitor["name"].lower() or 
                   search_lower in competitor["handle"].lower()
            ]
        
        # Apply limit
        if limit and len(competitors) > limit:
            competitors = competitors[:limit]
        
        return {
            "success": True,
            "competitors": competitors,
            "total_count": len(competitors),
            "filters_applied": {
                "brand_id": brand_id,
                "platform": platform,
                "search": search
            },
            "limit_applied": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "competitors": []
        }


async def get_competitor_by_id(user_id: str, competitor_id: str) -> Dict[str, Any]:
    """
    Get a specific competitor by ID.
    
    Args:
        user_id: User ID
        competitor_id: Competitor ID
    
    Returns:
        Dict containing competitor data or error
    """
    try:
        competitor = await social_media_db.get_competitor_by_id(competitor_id)
        if not competitor:
            return {
                "success": False,
                "error": "Competitor not found",
                "competitor": None
            }
        
        # Check if user owns this competitor
        if competitor["user_id"] != user_id:
            return {
                "success": False,
                "error": "Access denied",
                "competitor": None
            }
        
        return {
            "success": True,
            "competitor": competitor
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "competitor": None
        }


async def get_competitors_by_platform(user_id: str, platform: str, brand_id: Optional[str] = None, 
                               limit: int = 20) -> Dict[str, Any]:
    """
    Get competitors filtered by platform.
    
    Args:
        user_id: User ID
        platform: Platform name (instagram, youtube, reddit, linkedin)
        brand_id: Optional brand ID filter
        limit: Maximum number of competitors to return
    
    Returns:
        Dict containing competitors list filtered by platform
    """
    return await get_user_competitors(user_id, brand_id, platform, None, limit)


# ======================
# Scraped Posts Tools
# ======================

async def get_user_scraped_posts(user_id: str, brand_id: Optional[str] = None, 
                          platform: Optional[str] = None, days_back: Optional[int] = None,
                          search: Optional[str] = None, limit: int = 50, 
                          sort_by: str = "scraped_at", sort_order: str = "desc") -> Dict[str, Any]:
    """
    Get scraped posts for a user with comprehensive filtering.
    
    Args:
        user_id: User ID
        brand_id: Optional brand ID filter
        platform: Optional platform filter (instagram, youtube, reddit, linkedin)
        days_back: Optional number of days to look back
        search: Optional search term for post text
        limit: Maximum number of posts to return
        sort_by: Sort field (scraped_at, engagement, platform)
        sort_order: Sort order (asc, desc)
    
    Returns:
        Dict containing posts list and metadata
    """
    try:
        # Convert platform string to enum if provided
        platform_enum = None
        if platform:
            try:
                platform_enum = PlatformType(platform.lower())
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid platform: {platform}. Valid platforms: instagram, youtube, reddit, linkedin",
                    "posts": []
                }
        
        # Get all posts for user
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform_enum,
            brand_id=brand_id,
            limit=10000  # Get all posts for filtering
        )
        
        # Apply date filter if provided
        if days_back:
            date_from = datetime.utcnow() - timedelta(days=days_back)
            all_posts = [p for p in all_posts if p["scraped_at"] >= date_from]
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_posts = [
                p for p in all_posts
                if search_lower in (p["normalized"].get("text", "") or "").lower()
            ]
        
        # Apply sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "scraped_at":
            all_posts.sort(key=lambda x: x["scraped_at"], reverse=reverse)
        elif sort_by == "engagement":
            all_posts.sort(
                key=lambda x: (
                    x["normalized"]["engagement"].get("likes", 0) + 
                    x["normalized"]["engagement"].get("comments", 0)
                ), 
                reverse=reverse
            )
        elif sort_by == "platform":
            all_posts.sort(key=lambda x: x["platform"], reverse=reverse)
        
        # Apply limit
        if limit and len(all_posts) > limit:
            all_posts = all_posts[:limit]
        
        return {
            "success": True,
            "posts": all_posts,
            "total_count": len(all_posts),
            "filters_applied": {
                "brand_id": brand_id,
                "platform": platform,
                "days_back": days_back,
                "search": search
            },
            "sorting": {
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "limit_applied": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "posts": []
        }


async def get_recent_posts_by_platform(user_id: str, platform: str, limit: int = 10, 
                                days_back: int = 7) -> Dict[str, Any]:
    """
    Get recent posts from a specific platform.
    
    Args:
        user_id: User ID
        platform: Platform name (instagram, youtube, reddit, linkedin)
        limit: Maximum number of posts to return
        days_back: Number of days to look back
    
    Returns:
        Dict containing recent posts from the platform
    """
    return await get_user_scraped_posts(user_id, None, platform, days_back, None, limit, "scraped_at", "desc")


async def get_high_engagement_posts(user_id: str, min_likes: int = 100, min_comments: int = 10,
                             platform: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """
    Get posts with high engagement metrics.
    
    Args:
        user_id: User ID
        min_likes: Minimum likes threshold
        min_comments: Minimum comments threshold
        platform: Optional platform filter
        limit: Maximum number of posts to return
    
    Returns:
        Dict containing high engagement posts
    """
    try:
        # Convert platform string to enum if provided
        platform_enum = None
        if platform:
            try:
                platform_enum = PlatformType(platform.lower())
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid platform: {platform}",
                    "posts": []
                }
        
        # Get all posts for user
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform_enum,
            limit=10000
        )
        
        # Filter by engagement
        high_engagement_posts = []
        for post in all_posts:
            engagement = post["normalized"]["engagement"]
            likes = engagement.get("likes", 0)
            comments = engagement.get("comments", 0)
            
            if likes >= min_likes and comments >= min_comments:
                high_engagement_posts.append(post)
        
        # Sort by total engagement (likes + comments)
        high_engagement_posts.sort(
            key=lambda x: (
                x["normalized"]["engagement"].get("likes", 0) + 
                x["normalized"]["engagement"].get("comments", 0)
            ), 
            reverse=True
        )
        
        # Apply limit
        if limit and len(high_engagement_posts) > limit:
            high_engagement_posts = high_engagement_posts[:limit]
        
        return {
            "success": True,
            "posts": high_engagement_posts,
            "total_count": len(high_engagement_posts),
            "filters_applied": {
                "min_likes": min_likes,
                "min_comments": min_comments,
                "platform": platform
            },
            "limit_applied": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "posts": []
        }


# ======================
# Template Tools
# ======================

async def get_user_templates(user_id: str, brand_id: Optional[str] = None, 
                      template_type: Optional[str] = None, status: Optional[str] = None,
                      search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Get templates for a user with filtering options.
    
    Args:
        user_id: User ID
        brand_id: Optional brand ID filter
        template_type: Optional template type filter (video, image, text, mixed)
        status: Optional status filter (active, archived, draft)
        search: Optional search term for template name
        limit: Maximum number of templates to return
    
    Returns:
        Dict containing templates list and metadata
    """
    try:
        # Convert template_type string to enum if provided
        type_enum = None
        if template_type:
            try:
                type_enum = TemplateType(template_type.lower())
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid template type: {template_type}. Valid types: video, image, text, mixed",
                    "templates": []
                }
        
        templates = await social_media_db.get_templates_by_user(user_id, brand_id)
        
        # Apply type filter if provided
        if type_enum:
            templates = [t for t in templates if t["type"] == type_enum.value]
        
        # Apply status filter if provided
        if status:
            try:
                status_enum = TemplateStatus(status.lower())
                templates = [t for t in templates if t["status"] == status_enum.value]
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid status: {status}. Valid statuses: active, archived, draft",
                    "templates": []
                }
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t["name"].lower()
            ]
        
        # Apply limit
        if limit and len(templates) > limit:
            templates = templates[:limit]
        
        return {
            "success": True,
            "templates": templates,
            "total_count": len(templates),
            "filters_applied": {
                "brand_id": brand_id,
                "template_type": template_type,
                "status": status,
                "search": search
            },
            "limit_applied": limit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "templates": []
        }


async def get_template_by_id(user_id: str, template_id: str) -> Dict[str, Any]:
    """
    Get a specific template by ID.
    
    Args:
        user_id: User ID
        template_id: Template ID
    
    Returns:
        Dict containing template data or error
    """
    try:
        template = await social_media_db.get_template_by_id(template_id)
        if not template:
            return {
                "success": False,
                "error": "Template not found",
                "template": None
            }
        
        # Check if user owns this template
        if template["user_id"] != user_id:
            return {
                "success": False,
                "error": "Access denied",
                "template": None
            }
        
        return {
            "success": True,
            "template": template
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "template": None
        }


async def get_templates_by_brand(user_id: str, brand_id: str, template_type: Optional[str] = None,
                          limit: int = 20) -> Dict[str, Any]:
    """
    Get templates for a specific brand.
    
    Args:
        user_id: User ID
        brand_id: Brand ID
        template_type: Optional template type filter
        limit: Maximum number of templates to return
    
    Returns:
        Dict containing templates for the brand
    """
    return await get_user_templates(user_id, brand_id, template_type, None, None, limit)


# ======================
# Multi-Task Tools
# ======================

async def get_brand_complete_data(user_id: str, brand_id: str) -> Dict[str, Any]:
    """
    Get complete data for a brand including templates, competitors, and recent posts.
    
    Args:
        user_id: User ID
        brand_id: Brand ID
    
    Returns:
        Dict containing complete brand data
    """
    try:
        # Get brand
        brand_result = await get_brand_by_id(user_id, brand_id)
        if not brand_result["success"]:
            return brand_result
        
        brand = brand_result["brand"]
        
        # Get related data
        templates = await social_media_db.get_templates_by_user(user_id, brand_id)
        competitors = await social_media_db.get_competitors_by_user(user_id, brand_id=brand_id)
        recent_posts = await social_media_db.get_scraped_posts_by_user(
            user_id, brand_id=brand_id, limit=20
        )
        
        # Sort recent posts by date
        recent_posts.sort(key=lambda x: x["scraped_at"], reverse=True)
        
        # Get platform breakdown
        platform_counts = {}
        for post in recent_posts:
            platform = post["platform"]
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            "success": True,
            "brand": brand,
            "templates": templates,
            "competitors": competitors,
            "recent_posts": recent_posts[:10],  # Last 10 posts
            "summary": {
                "templates_count": len(templates),
                "competitors_count": len(competitors),
                "total_posts": len(recent_posts),
                "platform_breakdown": platform_counts
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def search_across_all_data(user_id: str, search_term: str, limit_per_type: int = 10) -> Dict[str, Any]:
    """
    Search across all user data types (brands, competitors, posts, templates).
    
    Args:
        user_id: User ID
        search_term: Search term to look for
        limit_per_type: Maximum results per data type
    
    Returns:
        Dict containing search results from all data types
    """
    try:
        # Search brands
        brands_result = await get_user_brands(user_id, search_term, limit_per_type)
        brands = brands_result.get("brands", []) if brands_result["success"] else []
        
        # Search competitors
        competitors_result = await get_user_competitors(user_id, None, None, search_term, limit_per_type)
        competitors = competitors_result.get("competitors", []) if competitors_result["success"] else []
        
        # Search posts
        posts_result = await get_user_scraped_posts(user_id, None, None, None, search_term, limit_per_type)
        posts = posts_result.get("posts", []) if posts_result["success"] else []
        
        # Search templates
        templates_result = await get_user_templates(user_id, None, None, None, search_term, limit_per_type)
        templates = templates_result.get("templates", []) if templates_result["success"] else []
        
        return {
            "success": True,
            "search_term": search_term,
            "results": {
                "brands": brands,
                "competitors": competitors,
                "posts": posts,
                "templates": templates
            },
            "summary": {
                "brands_found": len(brands),
                "competitors_found": len(competitors),
                "posts_found": len(posts),
                "templates_found": len(templates),
                "total_results": len(brands) + len(competitors) + len(posts) + len(templates)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": {
                "brands": [],
                "competitors": [],
                "posts": [],
                "templates": []
            }
        }


async def get_platform_analytics(user_id: str, platform: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a specific platform.
    
    Args:
        user_id: User ID
        platform: Platform name (instagram, youtube, reddit, linkedin)
        days_back: Number of days to analyze
    
    Returns:
        Dict containing platform analytics
    """
    try:
        # Get posts for the platform
        posts_result = await get_user_scraped_posts(user_id, None, platform, days_back, None, 1000)
        if not posts_result["success"]:
            return posts_result
        
        posts = posts_result["posts"]
        
        # Get competitors for the platform
        competitors_result = await get_user_competitors(user_id, None, platform, None, 100)
        competitors = competitors_result.get("competitors", []) if competitors_result["success"] else []
        
        # Calculate analytics
        total_posts = len(posts)
        total_likes = sum(p["normalized"]["engagement"].get("likes", 0) for p in posts)
        total_comments = sum(p["normalized"]["engagement"].get("comments", 0) for p in posts)
        total_shares = sum(p["normalized"]["engagement"].get("shares", 0) for p in posts)
        total_views = sum(p["normalized"]["engagement"].get("views", 0) for p in posts)
        
        avg_engagement = 0
        if total_posts > 0:
            avg_engagement = (total_likes + total_comments + total_shares) / total_posts
        
        # Get top performing posts
        top_posts = sorted(posts, key=lambda x: (
            x["normalized"]["engagement"].get("likes", 0) + 
            x["normalized"]["engagement"].get("comments", 0)
        ), reverse=True)[:10]
        
        return {
            "success": True,
            "platform": platform,
            "period_days": days_back,
            "analytics": {
                "total_posts": total_posts,
                "total_competitors": len(competitors),
                "engagement": {
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "total_shares": total_shares,
                    "total_views": total_views,
                    "avg_engagement_per_post": avg_engagement
                },
                "top_posts": top_posts
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }