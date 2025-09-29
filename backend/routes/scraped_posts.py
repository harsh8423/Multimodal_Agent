"""
Scraped Posts Management API Routes

This module provides CRUD operations for scraped posts including:
- Read, filter, and search scraped posts
- Post analytics and insights
- Media management and processing status
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio
from bson import ObjectId

from services.social_media_db import social_media_db
from models.social_media import PlatformType, ProcessingStatus
from services.auth import get_current_user

router = APIRouter(prefix="/api/scraped-posts", tags=["scraped-posts"])


# Request/Response Models
class MediaItemResponse(BaseModel):
    type: str
    url: str


class EngagementResponse(BaseModel):
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None


class NormalizedPostResponse(BaseModel):
    text: Optional[str] = None
    media: List[MediaItemResponse] = []
    posted_at: Optional[datetime] = None
    engagement: EngagementResponse
    source_id: str


class ProcessingInfoResponse(BaseModel):
    status: str
    pipeline: str
    normalized_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ScrapedPostResponse(BaseModel):
    id: str
    user_id: str
    brand_id: Optional[str]
    handle_id: Optional[str]
    platform: str
    source: str
    scraped_at: datetime
    platform_data: Dict[str, Any]
    normalized: NormalizedPostResponse
    processing: ProcessingInfoResponse
    important: bool
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ScrapedPostListResponse(BaseModel):
    posts: List[ScrapedPostResponse]
    total: int
    page: int
    limit: int


class PostAnalyticsResponse(BaseModel):
    total_posts: int
    platform_breakdown: Dict[str, int]
    engagement_stats: Dict[str, Any]
    media_stats: Dict[str, Any]
    date_range: Dict[str, datetime]


# Scraped Posts Operations
@router.get("/", response_model=ScrapedPostListResponse)
async def get_scraped_posts(
    current_user: dict = Depends(get_current_user),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    platform: Optional[PlatformType] = Query(None, description="Filter by platform"),
    handle_id: Optional[str] = Query(None, description="Filter by handle ID"),
    status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    date_from: Optional[datetime] = Query(None, description="Filter posts from date"),
    date_to: Optional[datetime] = Query(None, description="Filter posts to date"),
    search: Optional[str] = Query(None, description="Search in post text"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("scraped_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    Get scraped posts with filtering, pagination, and search.
    
    - **brand_id**: Filter by brand ID (optional)
    - **platform**: Filter by platform (optional)
    - **handle_id**: Filter by handle ID (optional)
    - **status**: Filter by processing status (optional)
    - **date_from**: Filter posts from date (optional)
    - **date_to**: Filter posts to date (optional)
    - **search**: Search in post text (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **sort_by**: Sort field (default: scraped_at)
    - **sort_order**: Sort order (default: desc)
    """
    try:
        user_id = current_user["id"]
        
        # Validate brand_id if provided
        if brand_id:
            brand = await social_media_db.get_brand_by_id(brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
            if brand["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied to brand")
        
        # Get all posts for user
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform,
            brand_id=brand_id,
            limit=10000  # Get all posts for filtering
        )
        
        # Apply filters
        filtered_posts = all_posts
        
        if handle_id:
            filtered_posts = [p for p in filtered_posts if p.get("handle_id") == handle_id]
        
        if status:
            filtered_posts = [p for p in filtered_posts if p["processing"]["status"] == status.value]
        
        if date_from:
            filtered_posts = [p for p in filtered_posts if p["scraped_at"] >= date_from]
        
        if date_to:
            filtered_posts = [p for p in filtered_posts if p["scraped_at"] <= date_to]
        
        if search:
            search_lower = search.lower()
            filtered_posts = [
                p for p in filtered_posts
                if search_lower in (p["normalized"].get("text", "") or "").lower()
            ]
        
        # Apply sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "scraped_at":
            filtered_posts.sort(key=lambda x: x["scraped_at"], reverse=reverse)
        elif sort_by == "engagement":
            filtered_posts.sort(
                key=lambda x: (
                    x["normalized"]["engagement"].get("likes", 0) + 
                    x["normalized"]["engagement"].get("comments", 0)
                ), 
                reverse=reverse
            )
        elif sort_by == "platform":
            filtered_posts.sort(key=lambda x: x["platform"], reverse=reverse)
        
        # Apply pagination
        total = len(filtered_posts)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_posts = filtered_posts[start_idx:end_idx]
        
        return ScrapedPostListResponse(
            posts=[ScrapedPostResponse(**post) for post in paginated_posts],
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scraped posts: {str(e)}")


@router.get("/{post_id}", response_model=ScrapedPostResponse)
async def get_scraped_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific scraped post by ID.
    
    - **post_id**: Post ID
    """
    try:
        user_id = current_user["id"]
        
        # Get post from database
        db = await social_media_db.get_db()
        post = await db.scraped_posts.find_one({
            "_id": ObjectId(post_id),
            "user_id": user_id
        })
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Convert to response format
        post_dict = {
            "id": str(post["_id"]),
            "user_id": post["user_id"],
            "brand_id": post.get("brand_id"),
            "handle_id": post.get("handle_id"),
            "platform": post["platform"],
            "source": post["source"],
            "scraped_at": post["scraped_at"],
            "platform_data": post["platform_data"],
            "normalized": post["normalized"],
            "processing": post["processing"],
            "important": post.get("important", False),
            "metadata": post.get("metadata", {})
        }
        
        return ScrapedPostResponse(**post_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve post: {str(e)}")


@router.delete("/{post_id}", status_code=204)
async def delete_scraped_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a scraped post.
    
    - **post_id**: Post ID
    """
    try:
        user_id = current_user["id"]
        
        # Check if post exists and user owns it
        db = await social_media_db.get_db()
        post = await db.scraped_posts.find_one({
            "_id": ObjectId(post_id),
            "user_id": user_id
        })
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Delete post
        result = await db.scraped_posts.delete_one({"_id": ObjectId(post_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete post")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")


@router.get("/analytics/overview", response_model=PostAnalyticsResponse)
async def get_posts_analytics(
    current_user: dict = Depends(get_current_user),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    platform: Optional[PlatformType] = Query(None, description="Filter by platform"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get analytics overview for scraped posts.
    
    - **brand_id**: Filter by brand ID (optional)
    - **platform**: Filter by platform (optional)
    - **days_back**: Number of days to look back (default: 30)
    """
    try:
        user_id = current_user["id"]
        
        # Calculate date range
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days_back)
        
        # Get all posts for user
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform,
            brand_id=brand_id,
            limit=10000
        )
        
        # Filter by date range
        filtered_posts = [
            p for p in all_posts 
            if date_from <= p["scraped_at"] <= date_to
        ]
        
        # Calculate platform breakdown
        platform_breakdown = {}
        for post in filtered_posts:
            platform = post["platform"]
            platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1
        
        # Calculate engagement stats
        total_likes = sum(p["normalized"]["engagement"].get("likes", 0) for p in filtered_posts)
        total_comments = sum(p["normalized"]["engagement"].get("comments", 0) for p in filtered_posts)
        total_shares = sum(p["normalized"]["engagement"].get("shares", 0) for p in filtered_posts)
        total_views = sum(p["normalized"]["engagement"].get("views", 0) for p in filtered_posts)
        
        avg_engagement = 0
        if filtered_posts:
            avg_engagement = (total_likes + total_comments + total_shares) / len(filtered_posts)
        
        # Calculate media stats
        total_media = sum(len(p["normalized"]["media"]) for p in filtered_posts)
        posts_with_media = len([p for p in filtered_posts if p["normalized"]["media"]])
        
        media_stats = {
            "total_media_items": total_media,
            "posts_with_media": posts_with_media,
            "avg_media_per_post": total_media / len(filtered_posts) if filtered_posts else 0
        }
        
        return PostAnalyticsResponse(
            total_posts=len(filtered_posts),
            platform_breakdown=platform_breakdown,
            engagement_stats={
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_views": total_views,
                "avg_engagement_per_post": avg_engagement
            },
            media_stats=media_stats,
            date_range={
                "from": date_from,
                "to": date_to
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/analytics/engagement", response_model=Dict[str, Any])
async def get_engagement_analytics(
    current_user: dict = Depends(get_current_user),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    platform: Optional[PlatformType] = Query(None, description="Filter by platform"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get detailed engagement analytics.
    
    - **brand_id**: Filter by brand ID (optional)
    - **platform**: Filter by platform (optional)
    - **days_back**: Number of days to look back (default: 30)
    """
    try:
        user_id = current_user["id"]
        
        # Calculate date range
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days_back)
        
        # Get all posts for user
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform,
            brand_id=brand_id,
            limit=10000
        )
        
        # Filter by date range
        filtered_posts = [
            p for p in all_posts 
            if date_from <= p["scraped_at"] <= date_to
        ]
        
        # Group by platform for engagement analysis
        platform_engagement = {}
        for post in filtered_posts:
            platform = post["platform"]
            if platform not in platform_engagement:
                platform_engagement[platform] = {
                    "total_posts": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_views": 0
                }
            
            engagement = post["normalized"]["engagement"]
            platform_engagement[platform]["total_posts"] += 1
            platform_engagement[platform]["total_likes"] += engagement.get("likes", 0)
            platform_engagement[platform]["total_comments"] += engagement.get("comments", 0)
            platform_engagement[platform]["total_shares"] += engagement.get("shares", 0)
            platform_engagement[platform]["total_views"] += engagement.get("views", 0)
        
        # Calculate averages
        for platform, stats in platform_engagement.items():
            if stats["total_posts"] > 0:
                stats["avg_likes_per_post"] = stats["total_likes"] / stats["total_posts"]
                stats["avg_comments_per_post"] = stats["total_comments"] / stats["total_posts"]
                stats["avg_shares_per_post"] = stats["total_shares"] / stats["total_posts"]
                stats["avg_views_per_post"] = stats["total_views"] / stats["total_posts"]
                stats["avg_engagement_per_post"] = (
                    stats["total_likes"] + stats["total_comments"] + stats["total_shares"]
                ) / stats["total_posts"]
        
        return {
            "date_range": {"from": date_from, "to": date_to},
            "platform_engagement": platform_engagement,
            "total_posts": len(filtered_posts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engagement analytics: {str(e)}")


@router.post("/bulk-delete", status_code=200)
async def bulk_delete_posts(
    post_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Delete multiple scraped posts.
    
    - **post_ids**: List of post IDs to delete
    """
    try:
        user_id = current_user["id"]
        
        if not post_ids:
            raise HTTPException(status_code=400, detail="No post IDs provided")
        
        # Delete posts
        db = await social_media_db.get_db()
        result = await db.scraped_posts.delete_many({
            "_id": {"$in": [ObjectId(pid) for pid in post_ids]},
            "user_id": user_id
        })
        
        return {
            "deleted_count": result.deleted_count,
            "requested_count": len(post_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete posts: {str(e)}")


@router.get("/search/advanced", response_model=ScrapedPostListResponse)
async def advanced_search_posts(
    current_user: dict = Depends(get_current_user),
    query: str = Query(..., description="Search query"),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    platform: Optional[PlatformType] = Query(None, description="Filter by platform"),
    min_likes: Optional[int] = Query(None, ge=0, description="Minimum likes"),
    min_comments: Optional[int] = Query(None, ge=0, description="Minimum comments"),
    has_media: Optional[bool] = Query(None, description="Posts with media only"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Advanced search for scraped posts with multiple filters.
    
    - **query**: Search query (required)
    - **brand_id**: Filter by brand ID (optional)
    - **platform**: Filter by platform (optional)
    - **min_likes**: Minimum likes (optional)
    - **min_comments**: Minimum comments (optional)
    - **has_media**: Posts with media only (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    try:
        user_id = current_user["id"]
        
        # Get all posts for user
        all_posts = await social_media_db.get_scraped_posts_by_user(
            user_id=user_id,
            platform=platform,
            brand_id=brand_id,
            limit=10000
        )
        
        # Apply search and filters
        filtered_posts = []
        query_lower = query.lower()
        
        for post in all_posts:
            # Text search
            text = post["normalized"].get("text", "") or ""
            if query_lower not in text.lower():
                continue
            
            # Engagement filters
            engagement = post["normalized"]["engagement"]
            if min_likes is not None and engagement.get("likes", 0) < min_likes:
                continue
            if min_comments is not None and engagement.get("comments", 0) < min_comments:
                continue
            
            # Media filter
            if has_media is not None:
                has_media_items = len(post["normalized"]["media"]) > 0
                if has_media != has_media_items:
                    continue
            
            filtered_posts.append(post)
        
        # Sort by engagement (likes + comments)
        filtered_posts.sort(
            key=lambda x: (
                x["normalized"]["engagement"].get("likes", 0) + 
                x["normalized"]["engagement"].get("comments", 0)
            ), 
            reverse=True
        )
        
        # Apply pagination
        total = len(filtered_posts)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_posts = filtered_posts[start_idx:end_idx]
        
        return ScrapedPostListResponse(
            posts=[ScrapedPostResponse(**post) for post in paginated_posts],
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search posts: {str(e)}")


@router.patch("/{post_id}/important", response_model=ScrapedPostResponse)
async def toggle_important_status(
    post_id: str,
    important: bool = Query(..., description="Whether to mark the post as important"),
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle the important status of a scraped post.
    
    - **post_id**: Post ID
    - **important**: Whether to mark the post as important
    """
    try:
        user_id = current_user["id"]
        
        # Check if post exists and user owns it
        db = await social_media_db.get_db()
        post = await db.scraped_posts.find_one({
            "_id": ObjectId(post_id),
            "user_id": user_id
        })
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Update important status
        result = await db.scraped_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"important": important}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update post")
        
        # Get updated post
        updated_post = await db.scraped_posts.find_one({"_id": ObjectId(post_id)})
        
        # Convert to response format
        post_dict = {
            "id": str(updated_post["_id"]),
            "user_id": updated_post["user_id"],
            "brand_id": updated_post.get("brand_id"),
            "handle_id": updated_post.get("handle_id"),
            "platform": updated_post["platform"],
            "source": updated_post["source"],
            "scraped_at": updated_post["scraped_at"],
            "platform_data": updated_post["platform_data"],
            "normalized": updated_post["normalized"],
            "processing": updated_post["processing"],
            "important": updated_post.get("important", False),
            "metadata": updated_post.get("metadata", {})
        }
        
        return ScrapedPostResponse(**post_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update post: {str(e)}")